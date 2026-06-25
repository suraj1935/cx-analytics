import sys
from pathlib import Path

from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.auth import CurrentUser, get_current_user
from app.main import app
from app.routes import audio


class _FakeStorageBucket:
    def upload(self, storage_path, content, options):
        self.storage_path = storage_path
        self.content = content
        self.options = options
        return {"path": storage_path}


class _FakeStorage:
    def from_(self, bucket_name):
        assert bucket_name == "audio"
        return _FakeStorageBucket()


class _FakeTableQuery:
    def __init__(self):
        self.insert_payload = None

    def insert(self, payload):
        self.insert_payload = payload
        return self

    def execute(self):
        assert self.insert_payload["filename"] == "sample.mp3"
        assert self.insert_payload["status"] == "pending"
        return type("Response", (), {"data": [self.insert_payload]})()


class _FakeSupabase:
    storage = _FakeStorage()

    def table(self, table_name):
        assert table_name == "call_recordings"
        return _FakeTableQuery()


def _current_user():
    return CurrentUser(id="00000000-0000-0000-0000-000000000001", email="admin@example.com")


def test_audio_upload_accepts_mp3_and_queues_transcription(monkeypatch):
    monkeypatch.setattr(audio, "get_supabase_admin", lambda: _FakeSupabase())
    monkeypatch.setattr(audio, "get_user_settings", lambda user_id: {"retain_original_audio": True})
    monkeypatch.setattr(audio, "queue_transcription", lambda recording_id, storage_path, retain: None)
    app.dependency_overrides[get_current_user] = _current_user

    try:
        client = TestClient(app)
        response = client.post(
            "/api/audio/upload",
            files={"file": ("sample.mp3", b"fake-mp3-bytes", "audio/mpeg")},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 202
    body = response.json()
    assert body["status"] == "pending"
    assert body["id"]
    assert body["original_file_retained"] is True


def test_audio_upload_respects_disabled_retention(monkeypatch):
    monkeypatch.setattr(audio, "get_supabase_admin", lambda: _FakeSupabase())
    monkeypatch.setattr(audio, "get_user_settings", lambda user_id: {"retain_original_audio": False})
    monkeypatch.setattr(audio, "queue_transcription", lambda recording_id, storage_path, retain: None)
    app.dependency_overrides[get_current_user] = _current_user
    try:
        response = TestClient(app).post(
            "/api/audio/upload",
            files={"file": ("sample.mp3", b"fake-mp3-bytes", "audio/mpeg")},
        )
    finally:
        app.dependency_overrides.clear()
    assert response.status_code == 202
    assert response.json()["original_file_retained"] is False


def test_audio_upload_rejects_anonymous_requests():
    client = TestClient(app)
    response = client.post(
        "/api/audio/upload",
        files={"file": ("sample.mp3", b"fake-mp3-bytes", "audio/mpeg")},
    )

    assert response.status_code == 401


def test_original_audio_download_rejects_anonymous_requests():
    response = TestClient(app).get(
        "/api/audio/00000000-0000-0000-0000-000000000099/file"
    )
    assert response.status_code == 401

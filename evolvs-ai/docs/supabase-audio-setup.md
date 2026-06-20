# Supabase Audio Setup

Project: `imtqmruynirbejvxvqnj`

The audio feature uses Supabase for metadata, transcript segments, and private audio file storage. You do not need to manually add MP3 files in Supabase. The app uploads files to Storage when the user clicks **Start Transcription**.

## Current Status

Verified objects:

- `public.call_recordings`
- `public.transcript_segments`
- private Storage bucket `audio`
- `vector` extension
- RLS enabled on audio tables

Live verification created:

- Recording id: `e790cfff-cd6c-4f4d-b29e-79789882a68a`
- Filename alias: `Call Recording 7 - Alex - John.mp3`
- Status: `done`

## Local Migration Files

The current audio migrations are:

```text
supabase/migrations/20260619010000_audio_only_current_app.sql
supabase/migrations/20260619011000_audio_advisor_fixes.sql
supabase/migrations/20260619012000_revoke_public_rls_auto_enable.sql
```

If a fresh Supabase project is created, run these in order from Supabase Studio SQL Editor or with `supabase db push`.

## Run The App

Backend:

```powershell
cd C:\Users\sg200\Desktop\cx-analytics-react\evolvs-ai\backend
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Frontend:

```powershell
cd C:\Users\sg200\Desktop\cx-analytics-react\evolvs-ai\frontend
npm.cmd run dev -- --host 127.0.0.1 --port 3000
```

Open:

```text
http://127.0.0.1:3000/#
```

Admin test user:

```text
admin@example.com
StrongPassword123!
```

## Run Tests

Backend audio route:

```powershell
cd C:\Users\sg200\Desktop\cx-analytics-react\evolvs-ai
& 'C:\Users\sg200\AppData\Local\Programs\Python\Python313\python.exe' -m pytest backend\tests\test_audio.py -q
```

Mocked frontend audio UI:

```powershell
cd C:\Users\sg200\Desktop\cx-analytics-react\evolvs-ai\frontend
npx.cmd playwright test audio.spec.ts --reporter=line
```

Live audio upload:

```powershell
cd C:\Users\sg200\Desktop\cx-analytics-react\evolvs-ai\frontend
npx.cmd playwright test audio-live.spec.ts --headed --reporter=line
```

## Expected Upload Flow

1. User selects an MP3 in the Audio Transcription page.
2. Browser sends `POST /api/audio/upload` with Supabase bearer token.
3. Backend uploads the file to private Supabase Storage bucket `audio`.
4. Backend inserts `call_recordings.status = pending`.
5. FastAPI background task changes status to `processing`.
6. `faster-whisper` transcribes locally on CPU.
7. Backend inserts `transcript_segments`.
8. Backend updates `call_recordings.status = done` with transcript and VTT.

## Model

The audio path uses local `faster-whisper`.

Default backend setting:

```text
WHISPER_MODEL=base
```

Runtime:

```text
device=cpu
compute_type=int8
```

No external LLM API key is used for audio transcription.

## Known Limitation

CPU Whisper can take several minutes for real call recordings. The live Playwright test verifies upload queueing and Supabase persistence, not full transcript completion.

from app.services.knowledge import chunk_text


def test_chunk_text_splits_large_content():
    chunks = chunk_text("First.\n\n" + ("A" * 3000) + "\n\nLast.")
    assert chunks[0] == "First."
    assert all(len(chunk) <= 2800 for chunk in chunks)
    assert chunks[-1] == "Last."

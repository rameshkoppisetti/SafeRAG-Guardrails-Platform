from app.utils.chunker import chunk_text


def test_chunk_text_with_overlap():
    text = "a" * 1000
    chunks = chunk_text(text, chunk_size=300, overlap=50)
    assert len(chunks) == 4
    assert all(len(chunk) <= 300 for chunk in chunks)

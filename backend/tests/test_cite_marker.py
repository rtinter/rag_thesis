from app.services.generation import build_context, find_cited_markers

def test_build_context_numbers_chunks_in_order():
    chunks = [
        {"title": "Titel A", "page_content": "Inhalt A"},
        {"title": "Titel B", "page_content": "Inhalt B"},
    ]
    ctx = build_context(chunks)

    assert "[1] Titel A" in ctx
    assert "[2] Titel B" in ctx
    assert ctx.index("[1]") < ctx.index("[2]")

def test_find_cited_markers_dedup_and_sorted():
    assert find_cited_markers("Text [3], dann [1], nochmal [1].") == [1, 3]

def test_find_cited_markers_empty_when_none():
    assert find_cited_markers("Hier gibt es keine Marker.") == []

def test_find_cited_markers_multidigit_sorts_numerically():
    assert find_cited_markers("Siehe [10] und [2].") == [2, 10]

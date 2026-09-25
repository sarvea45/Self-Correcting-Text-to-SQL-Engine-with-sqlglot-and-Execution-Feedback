from src.heuristics import evaluate_semantic_sanity

def test_cartesian_product():
    # Simulate a result with > 1000 rows
    results = [{} for _ in range(1001)]
    res = evaluate_semantic_sanity("SELECT * FROM a, b", results, "Total revenue?")
    assert res['is_suspicious'] == True
    assert "Cartesian product" in res['reason']

def test_empty_results():
    res = evaluate_semantic_sanity("SELECT * FROM a WHERE false", [], "Who are the customers with zero lifetime value?")
    assert res['is_suspicious'] == True
    assert "Query returned 0 rows" in res['reason']

    # Should not flag if not expecting entities
    res = evaluate_semantic_sanity("SELECT sum(amount) FROM a", [], "total sum")
    assert res['is_suspicious'] == False

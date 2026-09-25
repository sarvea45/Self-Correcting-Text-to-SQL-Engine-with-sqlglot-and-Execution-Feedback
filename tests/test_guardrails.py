from src.guardrails import validate_and_guard_sql

def test_guardrails():
    # Valid SELECT
    res = validate_and_guard_sql("SELECT * FROM customers")
    assert res['is_valid'] == True

    # Invalid syntax
    res = validate_and_guard_sql("SELECT * FRM customers")
    assert res['is_valid'] == False
    assert "Syntax Error" in res['error']

    # Guardrail blocked (DROP)
    res = validate_and_guard_sql("DROP TABLE customers;")
    assert res['is_valid'] == False
    assert "Security Guardrail Violation" in res['error']

    # Markdown stripped
    res = validate_and_guard_sql("```sql\nSELECT * FROM customers\n```")
    assert res['is_valid'] == True

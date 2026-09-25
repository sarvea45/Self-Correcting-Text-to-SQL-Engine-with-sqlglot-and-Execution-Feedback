def evaluate_semantic_sanity(sql: str, results: list, question: str) -> dict:
    """
    Evaluates a successful SQL execution result for semantic suspicion.
    Returns: dict containing 'is_suspicious' (bool) and 'reason' (str)
    """
    # Heuristic 1: Cartesian Product (Row count explosion)
    if len(results) > 1000: # Threshold based on DB size
        return {
            "is_suspicious": True,
            "reason": "Result set is unusually large (>1000 rows). Check for missing JOIN conditions (Cartesian product)."
        }
        
    # Heuristic 2: Unexpected Empty Results
    # Check if question expects entities
    expecting_data_words = ["which", "who", "list", "show", "what", "find", "get"]
    expecting_data = any(word in question.lower() for word in expecting_data_words)
    
    if len(results) == 0 and expecting_data:
        return {
            "is_suspicious": True,
            "reason": "Query returned 0 rows, but the question implies entities exist. Check WHERE clause filters (date ranges, exact string matches) or JOIN keys."
        }
        
    # Return clean bill of health
    return {
        "is_suspicious": False,
        "reason": None
    }

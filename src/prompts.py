BASE_SYSTEM_PROMPT = """You are an expert PostgreSQL developer.
Your task is to translate natural language questions into valid PostgreSQL queries.
Respond ONLY with the raw SQL query. Do not include markdown formatting, backticks, or conversational text.
"""

def get_generation_prompt(question: str, schema: str) -> str:
    return f"""
{schema}

Question: {question}

Generate the PostgreSQL query to answer this question.
"""

def get_syntax_repair_prompt(sql: str, error: str, history: str) -> str:
    history_section = f"\nPrior Attempts:\n{history}\n" if history else ""
    return f"""
Your previous SQL query failed syntax validation (or violated security guardrails).
{history_section}
Failed SQL:
{sql}

Parser Error:
{error}

Remember standard PostgreSQL dialect rules and that ONLY SELECT statements are allowed.
Please provide the corrected SQL query. Respond ONLY with the raw SQL query.
"""

def get_schema_repair_prompt(sql: str, error: str, schema: str, history: str) -> str:
    history_section = f"\nPrior Attempts:\n{history}\n" if history else ""
    return f"""
Your previous SQL query failed during execution due to a database engine error.
{history_section}
Failed SQL:
{sql}

Database Error:
{error}

This usually means you referenced a column or table that does not exist.
Here is the actual database schema for your reference:
{schema}

Please provide the corrected SQL query. Respond ONLY with the raw SQL query.
"""

def get_semantic_repair_prompt(sql: str, question: str, reason: str, results_sample: list, history: str) -> str:
    history_section = f"\nPrior Attempts:\n{history}\n" if history else ""
    return f"""
Your previous SQL query executed successfully, but the results look suspicious.
{history_section}
Original Question: {question}

Suspicious SQL:
{sql}

Heuristic Failure Reason:
{reason}

Sample of results (first 3 rows):
{results_sample[:3]}

Please review your logic (e.g., JOIN conditions, WHERE filters, GROUP BY) and provide the corrected SQL query. Respond ONLY with the raw SQL query.
"""

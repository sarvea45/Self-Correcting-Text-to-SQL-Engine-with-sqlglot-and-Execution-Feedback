import re
import sqlglot
from sqlglot import parse_one, exp
from sqlglot.errors import ParseError

def validate_and_guard_sql(sql_string: str) -> dict:
    """
    Validates that a SQL string is safe and syntactically correct.
    Strips markdown formatting if present.
    """
    # Pre-process: Strip markdown blocks if LLM returns them
    sql_string = sql_string.strip()
    if sql_string.startswith("```"):
        match = re.search(r"```(?:sql)?\n(.*?)```", sql_string, re.DOTALL | re.IGNORECASE)
        if match:
            sql_string = match.group(1).strip()
        else:
            # Fallback
            sql_string = re.sub(r"^```(?:sql)?", "", sql_string, flags=re.IGNORECASE).strip()
            sql_string = re.sub(r"```$", "", sql_string).strip()

    try:
        # Parse the SQL using sqlglot (target postgres)
        ast = parse_one(sql_string, read='postgres')
        
        # Guardrail: Only allow SELECT statements (and CTEs based on SELECT)
        if not isinstance(ast, (exp.Select, exp.Union)):
            return {
                "is_valid": False,
                "sql": sql_string,
                "error": "Security Guardrail Violation: Only SELECT statements are permitted."
            }
        
        # Return normalized SQL
        return {
            "is_valid": True,
            "sql": ast.sql(dialect='postgres'),
            "error": None
        }
    except ParseError as e:
        return {
            "is_valid": False,
            "sql": sql_string,
            "error": f"Syntax Error: {str(e)}"
        }

import os
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import Tuple, List, Dict, Optional

def get_db_connection():
    return psycopg2.connect(
        host=os.environ.get("DB_HOST", "localhost"),
        port=os.environ.get("DB_PORT", "5432"),
        user=os.environ.get("DB_USER", "postgres"),
        password=os.environ.get("DB_PASSWORD", "postgres"),
        dbname=os.environ.get("DB_NAME", "ecommerce_messy")
    )

def get_database_schema() -> str:
    """
    Retrieves the full schema DDL (Table names, Column names, Types) for the repair prompt.
    """
    query = """
    SELECT 
        table_name, 
        column_name, 
        data_type 
    FROM information_schema.columns 
    WHERE table_schema = 'public' 
    ORDER BY table_name, ordinal_position;
    """
    try:
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query)
                rows = cur.fetchall()
                
                schema_str = "Database Schema:\n"
                current_table = None
                for row in rows:
                    if row['table_name'] != current_table:
                        current_table = row['table_name']
                        schema_str += f"\nTable: {current_table}\n"
                    schema_str += f"  - {row['column_name']} ({row['data_type']})\n"
                
                return schema_str
    except Exception as e:
        return f"Error retrieving schema: {str(e)}"

def execute_sql(sql: str) -> Tuple[bool, Optional[List[Dict]], Optional[str]]:
    """
    Executes a SQL query. Catch psycopg2 schema errors.
    Returns: (success_bool, results_list, error_message_string)
    """
    try:
        with get_db_connection() as conn:
            # Set readonly transaction to prevent any accidental modifications just in case
            conn.set_session(readonly=True, autocommit=True)
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(sql)
                
                if cur.description:
                    results = cur.fetchall()
                    return True, results, None
                return True, [], None
    except psycopg2.Error as e:
        # e.pgcode contains the specific error code
        # e.pgerror contains the string message
        error_msg = f"Database Engine Error [{e.pgcode}]: {str(e)}"
        return False, None, error_msg
    except Exception as e:
        return False, None, f"Execution Error: {str(e)}"

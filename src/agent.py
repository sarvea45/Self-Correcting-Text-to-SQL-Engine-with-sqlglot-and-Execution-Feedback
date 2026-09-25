import time
import os
from litellm import completion
from src.guardrails import validate_and_guard_sql
from src.db import execute_sql, get_database_schema
from src.heuristics import evaluate_semantic_sanity
from src.prompts import (
    BASE_SYSTEM_PROMPT,
    get_generation_prompt,
    get_syntax_repair_prompt,
    get_schema_repair_prompt,
    get_semantic_repair_prompt
)

class TextToSQLAgent:
    def __init__(self, max_attempts: int = 3):
        self.max_attempts = max_attempts
        self.model = os.environ.get("LLM_MODEL_ID", "gemini-3.1-pro")
        self.schema = get_database_schema()

    def _call_llm(self, prompt: str) -> str:
        for attempt in range(5):
            try:
                response = completion(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": BASE_SYSTEM_PROMPT},
                        {"role": "user", "content": prompt}
                    ],
                    api_key=os.environ.get("LLM_API_KEY")
                )
                return response.choices[0].message.content.strip()
            except Exception as e:
                error_str = str(e).lower()
                if "rate limit" in error_str or "429" in error_str or "rate_limit_exceeded" in error_str:
                    print("Rate limit hit! Sleeping for 65 seconds to clear window...", flush=True)
                    time.sleep(65)
                    continue
                raise Exception(f"LLM API Error: {str(e)}")
        raise Exception("LLM API Error: Max rate limit retries exceeded")

    def process_query(self, question: str, disable_semantics: bool = False) -> dict:
        """
        Executes the deterministic state machine for Text-to-SQL.
        """
        iterations = 0
        repair_history = []
        
        # Initial State
        current_prompt = get_generation_prompt(question, self.schema)
        
        while iterations < self.max_attempts:
            iterations += 1
            
            # State 1: Generation
            sql_candidate = self._call_llm(current_prompt)
            
            # Keep history for next loops if needed
            history_str = "\n".join([f"Attempt {h['iteration']} - {h['failure_class']}: {h['sql']}" for h in repair_history])
            
            # State 2: AST Validation
            ast_check = validate_and_guard_sql(sql_candidate)
            sql = ast_check['sql']
            
            if not ast_check['is_valid']:
                repair_history.append({
                    "iteration": iterations,
                    "failure_class": "Syntax",
                    "sql": sql_candidate,
                    "error": ast_check['error']
                })
                if iterations >= self.max_attempts:
                    break
                current_prompt = get_syntax_repair_prompt(sql, ast_check['error'], history_str)
                continue
                
            # State 3: Execution / Schema Validation
            success, results, error_msg = execute_sql(sql)
            
            if not success:
                repair_history.append({
                    "iteration": iterations,
                    "failure_class": "Schema",
                    "sql": sql,
                    "error": error_msg
                })
                if iterations >= self.max_attempts:
                    break
                current_prompt = get_schema_repair_prompt(sql, error_msg, self.schema, history_str)
                continue
                
            # State 4: Semantic Validation
            if not disable_semantics:
                sanity_check = evaluate_semantic_sanity(sql, results, question)
                if sanity_check['is_suspicious']:
                    repair_history.append({
                        "iteration": iterations,
                        "failure_class": "Semantic",
                        "sql": sql,
                        "error": sanity_check['reason']
                    })
                    if iterations >= self.max_attempts:
                        break
                    current_prompt = get_semantic_repair_prompt(sql, question, sanity_check['reason'], results, history_str)
                    continue
            
            # State 5: Success
            return {
                "status": "success",
                "final_sql": sql,
                "data": results,
                "iterations": iterations,
                "repair_history": repair_history
            }
            
        # Failed State
        return {
            "status": "failed",
            "final_sql": sql_candidate if 'sql_candidate' in locals() else None,
            "data": None,
            "iterations": iterations,
            "repair_history": repair_history
        }

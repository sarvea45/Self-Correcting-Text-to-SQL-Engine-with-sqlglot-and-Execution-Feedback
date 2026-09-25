import json
import os
import copy
from src.agent import TextToSQLAgent
from src.db import execute_sql

EVAL_SET_PATH = "data/eval_set.json"
RESULTS_PATH = "results/evaluation_metrics.json"

def compare_results(gold_sql: str, generated_sql: str) -> bool:
    if not generated_sql:
        return False
    # Execute gold
    success_gold, res_gold, _ = execute_sql(gold_sql)
    if not success_gold:
        return False # Faulty gold query in eval set
    
    # Execute generated
    success_gen, res_gen, _ = execute_sql(generated_sql)
    if not success_gen:
        return False
        
    # Compare raw data lengths, and content regardless of order
    if len(res_gold) != len(res_gen):
        return False
        
    gold_set = sorted([str(r) for r in res_gold])
    gen_set = sorted([str(r) for r in res_gen])
    
    return gold_set == gen_set

def run_evaluation():
    with open(EVAL_SET_PATH, 'r') as f:
        eval_data = json.load(f)

    metrics = {
        "configurations": {
            "zero_shot": {
                "accuracy_pct": 0.0,
                "avg_iterations": 0.0
            },
            "syntax_schema_repair_only": {
                "accuracy_pct": 0.0,
                "avg_iterations": 0.0,
                "total_schema_repairs": 0
            },
            "full_pipeline": {
                "accuracy_pct": 0.0,
                "avg_iterations": 0.0,
                "total_semantic_repairs": 0
            }
        }
    }

    os.makedirs(os.path.dirname(RESULTS_PATH), exist_ok=True)
    
    total_q = len(eval_data)
    
    agent_zero = TextToSQLAgent(max_attempts=1)
    correct_zero, iter_zero = 0, 0
    
    agent_ss = TextToSQLAgent(max_attempts=3)
    correct_ss, iter_ss, repairs_ss = 0, 0, 0
    
    agent_full = TextToSQLAgent(max_attempts=3)
    correct_full, iter_full, repairs_full = 0, 0, 0

    print(f"Starting evaluation on {total_q} questions...")
    
    for idx, item in enumerate(eval_data):
        print(f"Evaluating Q{idx+1}/{total_q}...")
        q = item['question']
        gold = item['gold_sql']
        
        # Zero Shot
        res_z = agent_zero.process_query(q, disable_semantics=True)
        iter_zero += res_z['iterations']
        if compare_results(gold, res_z.get('final_sql', '')):
            correct_zero += 1
            
        # Syntax/Schema Only
        res_ss = agent_ss.process_query(q, disable_semantics=True)
        iter_ss += res_ss['iterations']
        repairs_ss += sum(1 for h in res_ss['repair_history'] if h['failure_class'] == 'Schema')
        if compare_results(gold, res_ss.get('final_sql', '')):
            correct_ss += 1
            
        # Full Pipeline
        res_f = agent_full.process_query(q, disable_semantics=False)
        iter_full += res_f['iterations']
        repairs_full += sum(1 for h in res_f['repair_history'] if h['failure_class'] == 'Semantic')
        if compare_results(gold, res_f.get('final_sql', '')):
            correct_full += 1

    # Populate metrics
    metrics['configurations']['zero_shot']['accuracy_pct'] = round((correct_zero / total_q) * 100, 2)
    metrics['configurations']['zero_shot']['avg_iterations'] = round(iter_zero / total_q, 2)
    
    metrics['configurations']['syntax_schema_repair_only']['accuracy_pct'] = round((correct_ss / total_q) * 100, 2)
    metrics['configurations']['syntax_schema_repair_only']['avg_iterations'] = round(iter_ss / total_q, 2)
    metrics['configurations']['syntax_schema_repair_only']['total_schema_repairs'] = repairs_ss
    
    metrics['configurations']['full_pipeline']['accuracy_pct'] = round((correct_full / total_q) * 100, 2)
    metrics['configurations']['full_pipeline']['avg_iterations'] = round(iter_full / total_q, 2)
    metrics['configurations']['full_pipeline']['total_semantic_repairs'] = repairs_full

    with open(RESULTS_PATH, 'w') as f:
        json.dump(metrics, f, indent=2)
        
    print(f"Evaluation complete. Results written to {RESULTS_PATH}")

if __name__ == "__main__":
    run_evaluation()

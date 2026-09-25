# Self-Correcting Text-to-SQL Engine

This repository implements a production-grade Text-to-SQL engine equipped with a deterministic state machine that guides an LLM through a typed repair policy.

## Mechanism Overview
Naive Text-to-SQL systems fail silently when queries execute successfully but produce logically flawed results (like massive Cartesian products). This system catches those errors using three distinct repair loops:
1. **Syntax / Security Guardrails (`sqlglot`)**: Catches basic malformations and prevents prompt injection (e.g., `DROP TABLE`).
2. **Schema Validation**: Catches hallucinated columns or tables by intercepting database engine errors and providing the LLM with the actual catalog.
3. **Semantic Suspicion**: Evaluates successful execution results against heuristics (e.g., abnormally large row counts or unexpected empty results) to catch logical errors before they reach the user.

## Repository Structure
- `src/agent.py`: The deterministic state machine and repair loop.
- `src/heuristics.py`: The semantic sanity checks.
- `src/guardrails.py`: The AST parsing and security layer.
- `src/db.py`: Database execution and catalog retrieval.
- `src/prompts.py`: Distinct repair templates.
- `scripts/evaluate.py`: Batch evaluation script proving the efficacy of the pipeline.
- `api/main.py`: FastAPI endpoint for interactive use.

## How to Run

1. **Environment Variables**: Copy `.env.example` to `.env` and fill in your LLM API credentials (e.g., OpenAI or Gemini).

2. **Start the Infrastructure**:
```bash
docker-compose up -d --build
```
This initializes the PostgreSQL database, seeds the "messy" schema, and starts the FastAPI service.

3. **Evaluate the Pipeline**:
```bash
docker-compose exec api python scripts/evaluate.py
```
This runs the 30-question `eval_set.json` against three configurations (Zero-shot, Schema-repair only, and Full Pipeline) and generates the final metrics in `results/evaluation_metrics.json`.

## Evaluation
The pipeline is evaluated strictly on execution accuracy (does the generated query produce the exact same data as the gold-standard query, regardless of row order?). The batch script also outputs the mean iterations and a breakdown of which failure classes were caught and repaired.

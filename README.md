# Legal AI Demand Letter Generator

Generate professional personal-injury demand letters as PDFs using an LLM grounded on case data via MCP tools and a simple RAG over case documents.

## 1) Dependencies and Setup

- Python 3.10–3.12
- uv (Python package manager)
- Docker + Docker Compose
- API keys
  - OPENAI_API_KEY (required)
  - OPENAI_MODEL (optional; defaults are set in code)

Install uv (macOS):
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Install project dependencies:
```bash
uv sync
```

Environment variables (same shell session you will run commands from):
```bash
export OPENAI_API_KEY="sk-..."     # required
export OPENAI_MODEL="gpt-4o-mini"  # optional
```

Start Postgres with seed data:
```bash
docker compose up -d
```

Notes:
- Database schema and data are seeded from:
  - docker/init/01_schema.sql
  - docker/init/02_data.sql
- If you customize DB settings, ensure they match the connection in the app’s DB layer.

## 2) How to Run

Generate a demand letter (PDF) for the sample case:
```bash
uv run legal-ai generate-demand-llm \
  --case 2024-PI-001 \
  --out outputs/demand_letter_2024-PI-001.pdf
```

- The output defaults to `outputs/demand_letter_<CASE_ID>.pdf` if `--out` is omitted.
- The MCP tool server is launched automatically as a subprocess during generation.

## 3) Code Explanation

High-level flow:
1. CLI parses arguments and calls the generator.
2. The agent is created with strict structured output set to `DemandLetter`.
3. The agent uses MCP tools to ground facts and a RAG tool to fetch citations/snippets.
4. The validated structured output is rendered to a PDF styled like `Sample Demand Letter.md`.

Key files and modules:

- `main.py`
  - CLI entry point.
  - Command: `generate-demand-llm` with `--case` and `--out`.
  - Calls `app.agent_runner.generate_demand_letter_llm(...)`.

- `app/agent_runner.py`
  - Orchestrates the MCP tool server (stdio), builds an agent with:
    - model settings (temperature, tool-choice required)
    - `output_type=DemandLetter` for structured output
  - System and task prompts instruct the agent to use:
    - `get_case_details`, `get_case_documents`, `get_case_timeline`, `get_financial_summary`
    - `search_citations` to populate `citations` with grounded sources/snippets
  - Renders a PDF with ReportLab that follows the style of `Sample Demand Letter.md`:
    - Firm header (centered)
    - Date and recipient block
    - Statement of Facts
    - Injuries Sustained
    - Damages Claimed (numbered items, totals)
    - Settlement Demand
    - Liability Analysis
    - Supporting Documentation (from citations)
    - Time Limit for Response
    - Closing Statement and signature block
    - Enclosures

- `app/mcp_server.py`
  - Exposes MCP tools backed by the data layer and RAG:
    - `get_case_details(case_id)`
    - `get_case_documents(case_id, category?)`
    - `get_case_timeline(case_id, event_type?)`
    - `get_financial_summary(case_id)`
    - `get_party_details(case_id, party_type)`
    - `search_similar_cases(case_type, keywords)` [toy]
    - `search_citations(case_id, query, k=5)` [RAG-backed; returns source/page/snippet]
  - Maintains an in-memory per-case RAG cache.

- `app/rag.py`
  - `SimpleRAG` builds a TF‑IDF index over case documents using pdfminer to extract PDF text.
  - `search(query, k)` returns top chunks and formatted citation strings via `Chunk.cite()`.

- `app/schemas.py`
  - Pydantic models for strict, validated structured output:
    - `DemandLetter` with sections:
      - `header`
      - `introduction`
      - `liability`
      - `injuries_treatment`
      - `economic_damages`
      - `non_economic_damages`
      - `demand`
      - `citations` (list of source/page/snippet)

- `app/case_data.py`
  - Data access to Postgres:
    - `get_case_details`
    - `get_case_documents`
    - `get_case_timeline`
    - `get_financial_summary`
    - `search_similar_cases`

- `docker/`
  - `init/01_schema.sql`, `init/02_data.sql`: DB schema and seed data for the sample case.

- `pyproject.toml`
  - Dependencies and CLI scripts:
    - `legal-ai = "main:main"`
    - `legal-ai-mcp = "app.mcp_server:main"` (server is launched programmatically)

- `Sample Demand Letter.md`
  - Human-readable style reference for the PDF renderer.

## Troubleshooting

- **OPENAI_API_KEY is not set**
  - Ensure the env var is exported in the same shell before running.

- **DB connection issues**
  - Confirm Docker is running: `docker compose up -d`
  - Verify DB settings match in the app’s DB code.

- **Missing citations**
  - Ensure sample documents exist under `sample_docs/…` and that the DB `documents` table points to the correct paths.
  - RAG depends on those files being accessible locally.

- **PDF formatting**
  - Adjust ReportLab styles in `app/agent_runner.py` (e.g., font sizes, spacing) if you want tighter or looser layout.


# Repository Guidelines

## Project Structure & Module Organization
- `src/` – core Python services, agents, and orchestration logic. Key subpackages include `services/` for domain workflows and `infrastructure/` for telemetry.
- `server.py` – FastAPI entrypoint; REST endpoints drive orchestrations and analytics.
- `cli.py` – Typer-based control surface mirroring server APIs for scripted runs.
- `frontend/` – Vite + React dashboard (`src/views/` holds feature pages such as `NewPipeline2View.tsx`).
- `tests/` – Python unit and integration suites; React tests live alongside components when present.
- `data/` – SQLite datasets used for local experimentation. Treat as non-production fixtures.

## Build, Test, and Development Commands
- `python -m venv venv && source venv/bin/activate` – standard virtualenv bootstrap.
- `pip install -r requirements.txt` – install server and agent dependencies.
- `uvicorn server:app --reload` – launch the API for iterative development.
- `python cli.py --help` – inspect CLI verbs; use `python cli.py orchestrate run ...` to trigger pipelines.
- `cd frontend && npm install` – prepare UI dependencies.
- `npm run dev` – start the React dashboard at `http://localhost:5173`.
- `npm run build` – type-check and bundle the UI (resolve TypeScript errors before pushing).

## Coding Style & Naming Conventions
- Python: Black-style 4-space indentation, descriptive snake_case for functions and variables, PascalCase for classes.
- TypeScript/React: Prefer functional components with hooks; camelCase props/state; keep files UTF-8/ASCII.
- Place module-specific tests beside their targets (Python in `tests/`, React next to the view/component).

## Testing Guidelines
- Python tests run via `pytest`; name new tests `test_<feature>.py` and keep shared fixtures in `conftest.py`.
- Frontend tests (when added) should use Vitest/Jest naming (`*.test.tsx`) alongside the component.
- Prioritize coverage for analysis → plan → workflow → execution flows; add regression checks with every bug fix.

## Commit & Pull Request Guidelines
- Write imperative, concise commit messages (e.g., `Add orchestrator polling for UI`). Group related changes; avoid mixing unrelated refactors.
- PRs should state the problem, summarize the fix, list test evidence (`pytest`, `npm run build`), and include screenshots/GIFs for UI updates.
- Reference issue IDs in the PR body (`Fixes #123`) and note any follow-up tasks explicitly.

## Security & Configuration Tips
- Store secrets (OpenAI keys, telemetry endpoints) in `.env`; never commit real credentials.
- Rotate SQLite fixtures when sharing logs; anonymize customer data before export.
- Enable OTEL tracing only when needed—set `OTEL_JAEGER_ENABLED=false` for local work to reduce noise.

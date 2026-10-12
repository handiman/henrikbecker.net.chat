# henrikbecker-py

REST API (FastAPI) hosted as a Cloudflare Python Worker. Entrypoint: `src/main.py` (`Default = asgi.entrypoint(app)`).

## Commands
- `uv sync` – install deps
- `uv run pywrangler dev` – local dev (http://localhost:8787); fails on native Windows, use WSL
- `.\scripts\wsl-dev.ps1` (Windows) / `bash scripts/wsl-dev.sh` (WSL) – syncs the project to `~/henrikbecker.py` in WSL, installs uv/Node if missing, runs `pywrangler dev`
- `uv run pywrangler deploy` – deploy
- `uv run pytest` – tests; `uv run ruff check .` / `uv run ruff format .` – lint/format

## Structure
- `wrangler.jsonc` – Worker config, `python_workers` flag, `RATE_LIMITER` binding
- `src/main.py` – app, CORS, router registration
- `src/api/v1/` – v1 routers (mounted under `/api/v1`)
- `tests/` – pytest; `conftest.py` stubs `workers` and injects a fake `RATE_LIMITER`
- `src/api/rate_limit.py` – rate-limit dependency (per `CF-Connecting-IP`)

## Conventions
- All endpoints are anonymous: every new router must include the `rate_limit` dependency.
- CORS origins are listed in `ALLOWED_ORIGINS` in `src/main.py` (henrikbecker.net, becker-consulting.se); keep it an explicit allowlist, never `*`.
- Bindings are accessed via `request.scope["env"]`; don't hand-write secrets into config (use `wrangler secret put`).
- Python Workers runtime is Pyodide: only pure-Python / Pyodide-supported packages work.

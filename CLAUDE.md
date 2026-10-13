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
- `src/api/v1/ai.py` – `POST /ask/{collection}` and `/ingest/{collection}` (same paths as the old worker on ai.henrikbecker.net, needed by the CV bot; `/ingress` is an alias); ported from the `ai-worker` in henrikbecker.cloudflare, forwards unchanged to `https://henrikbecker.azurewebsites.net/ai/...`. Outbound `fetch` is the `get_fetch` dependency (override in tests)

## Branching and commits
Full details in [CONTRIBUTING.md](CONTRIBUTING.md#making-a-change); the short version:
- Never commit directly to `master`. Branch from `master` as `fix/…`, `feat/…`, `docs/…`, `refactor/…` or `ci/…`, and open a pull request back against `master` (link the issue with `Closes #123`).
- Commit messages: `type(Scope): Subject`, e.g. `fix(API): Return 429 with CORS headers when rate limited`.
- Before pushing: `uv run pytest`, `uv run ruff check .` and `uv run ruff format --check .`; add or update tests for the change.

## Conventions
- All endpoints are anonymous: every new router must include the `rate_limit` dependency.
- CORS origins are listed in `ALLOWED_ORIGINS` in `src/main.py` (henrikbecker.net, becker-consulting.se, lena.fagervall.se, lena-fagervall.github.io, plus localhost:8787/8080 for dev); keep it an explicit allowlist, never `*`.
- Bindings are accessed via `request.scope["env"]`; don't hand-write secrets into config (use `wrangler secret put`).
- Python Workers runtime is Pyodide: only pure-Python / Pyodide-supported packages work.

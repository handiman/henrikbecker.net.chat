# henrikbecker-chat

REST API (FastAPI) hosted as a Cloudflare Python Worker. Entrypoint: `src/main.py` (`Default = asgi.entrypoint(app)`).

## Commands
- `uv sync` – install deps
- `uv run pywrangler dev` – local dev (http://localhost:8787); fails on native Windows, use WSL
- `.\scripts\wsl-dev.ps1` (Windows) / `bash scripts/wsl-dev.sh` (WSL) – syncs the project to `~/henrikbecker.net.chat` in WSL, installs uv/Node if missing, runs `pywrangler dev`
- `uv run pywrangler deploy` – deploy
- `uv run pytest` – tests; `uv run ruff check .` / `uv run ruff format .` – lint/format

## Structure
- `wrangler.jsonc` – Worker config, `python_workers` flag, `AI` and `CV_KV` bindings, `RATE_LIMITER` and `ASK_RATE_LIMITER` rate limits; secret `INGEST_TOKEN` (`wrangler secret put`) Served on workers.dev only (`https://henrikbecker-chat.henrik-becker.workers.dev`), no custom domain
- `src/main.py` – app, CORS, router registration
- `src/api/v1/` – v1 routers (mounted under `/api/v1`)
- `tests/` – pytest; `conftest.py` stubs `workers` and injects fake `RATE_LIMITER`, `ASK_RATE_LIMITER` and `INGEST_TOKEN`
- `src/api/rate_limit.py` – rate-limit dependency (per `CF-Connecting-IP`)
- `src/api/v1/ai.py` – CV bot: `POST /ask/{collection}` (anonymous, body = JSON string, max 500 chars, extra `ASK_RATE_LIMITER`) and `POST /ingest/{collection}` (Bearer `INGEST_TOKEN`, body = CV markdown, max 100 KB; `/ingress` is an alias). Both also under `/ai/...`. Only collection `henrik` exists. Ported from henrikbecker.net/src/henrikbecker.ai (C#/Azure); no Azure involved any more
- `src/api/cvbot/` – `prompt.py` (ported PromptGuard text), `llm.py` (`ask_llm`, the only place that knows Workers AI and the model), `store.py` (KV `CV_KV`, key `cv:<collection>`), `auth.py` (constant-time token check). Tests override the `get_store` / `get_ask_llm` dependencies
- Question battery against a real model: `uv run python scripts/eval_bot.py http://localhost:8787 [--ingest]` (cases in `tests/eval_cases.py`, document in `tests/fixtures/example_cv.md`); not part of `pytest`

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

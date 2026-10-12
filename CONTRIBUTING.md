# Contributing to henrikbecker.py

Thanks for taking an interest. Bug reports, ideas and pull requests are all welcome.

## Before you start

- **Found a bug or have an idea?** Open an [issue](https://github.com/handiman/henrikbecker.py/issues). The templates ask for what's needed.
- **Planning a larger change?** Open an issue first, so we can agree on the approach before you put time into it.
- **Found a security problem?** Don't open a public issue. Email [security@henrikbecker.se](mailto:security@henrikbecker.se) instead.

## How the code is organized

The project is a FastAPI REST API hosted as a Cloudflare Python Worker.

- `wrangler.jsonc`: Worker configuration, including the `RATE_LIMITER` binding.
- `src/main.py`: the FastAPI app, CORS setup and router registration. Also the Worker entrypoint.
- `src/api/v1/`: one module per resource, each exposing a router that is mounted under `/api/v1`.
- `src/api/rate_limit.py`: the rate-limit dependency, keyed on the client IP.

Two rules for new endpoints: the API is anonymous, so every router must be mounted with the `rate_limit` dependency, and CORS stays an explicit allowlist (`ALLOWED_ORIGINS` in `src/main.py`), never `*`.

## Getting set up

You need [uv](https://docs.astral.sh/uv/) and [Node.js](https://nodejs.org/).

```sh
uv sync                    # install dependencies
uv run pywrangler dev      # run locally at http://localhost:8787
```

Then try it with `curl http://localhost:8787/api/v1/hello`.

`pywrangler dev` does not currently work on native Windows; use WSL. On Windows, `.\scripts\wsl-dev.ps1` does it all: it syncs the project into WSL, installs uv and Node if missing, and starts the dev server. The `workers` package only imports inside the Pyodide runtime, so stub it if you unit-test outside the Worker. Never commit secrets: use `wrangler secret put` or a local `.dev.vars` file (already git-ignored).

## Making a change

1. Branch from `master`, named after the kind of change: `fix/…`, `feat/…`, `docs/…`, `refactor/…`, `ci/…`.
2. Add or update tests for what you change.
3. Run `uv run pytest`, `uv run ruff check .` and `uv run ruff format --check .` before you push.
4. Write commit messages as `type(Scope): Subject`, for example `fix(API): Return 429 with CORS headers when rate limited`.5. Open a pull request against `master`. Say what it changes and why, and link the issue it closes (`Closes #123`).


# chat

REST API as a Cloudflare Python Worker (FastAPI).

- `GET /api/v1/ping` → `Pong` (`text/plain`)
- `POST /ask/{collection}`, `POST /ingest/{collection}` (alias `/ingress/{collection}`) → forwarded to Azure
- Rate limited per client IP (see `ratelimits` in `wrangler.jsonc`)
- CORS allowed for henrikbecker.net and becker-consulting.se

```sh
uv sync
uv run pywrangler dev      # http://localhost:8787
uv run pywrangler deploy
```

On Windows, `pywrangler dev` must run in WSL: `.\scripts\wsl-dev.ps1`.

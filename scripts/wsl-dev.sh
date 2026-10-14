#!/usr/bin/env bash
# Run `pywrangler dev` inside WSL, since it does not work on native Windows.
# Syncs this project to the WSL filesystem (keeping a local .dev.vars there), installs uv/Node if missing, then starts the dev server.
# Usage (from WSL):  bash scripts/wsl-dev.sh [pywrangler dev args]
# Usage (from Windows): .\scripts\wsl-dev.ps1 [pywrangler dev args]
set -euo pipefail

SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEST="${WSL_DEV_DIR:-$HOME/henrikbecker.net.chat}"

export PATH="$HOME/.local/bin:$PATH"

if ! command -v uv >/dev/null; then
    echo ">> Installing uv"
    curl -LsSf https://astral.sh/uv/install.sh | sh
fi

export NVM_DIR="$HOME/.nvm"
if [ ! -s "$NVM_DIR/nvm.sh" ]; then
    echo ">> Installing nvm"
    curl -fsSo- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.3/install.sh | bash
fi
# shellcheck disable=SC1091
. "$NVM_DIR/nvm.sh"
command -v node >/dev/null && [[ "$(command -v node)" == "$NVM_DIR"/* ]] || nvm install --lts

echo ">> Syncing $SRC -> $DEST"
mkdir -p "$DEST"
EXCLUDES=(.git .venv .venv-workers python_modules node_modules .wrangler __pycache__ .pytest_cache .ruff_cache .dev.vars)
if command -v rsync >/dev/null; then
    rsync -a --delete "${EXCLUDES[@]/#/--exclude=}" "$SRC/" "$DEST/"
else
    # No rsync: clear stale files (keeping venvs/caches), then copy with tar.
    find "$DEST" -mindepth 1 -maxdepth 1 \
        ! -name .venv ! -name .venv-workers ! -name python_modules \
        ! -name node_modules ! -name .wrangler ! -name .dev.vars -exec rm -rf {} +
    (cd "$SRC" && tar "${EXCLUDES[@]/#/--exclude=}" -cf - .) | tar -xf - -C "$DEST"
fi

cd "$DEST"
uv sync --quiet
echo ">> Starting dev server on http://localhost:8787 (Ctrl+C to stop)"
exec uv run pywrangler dev "$@"

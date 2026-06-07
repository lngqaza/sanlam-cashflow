#!/bin/bash
# SessionStart hook for Claude Code on the web.
set -uo pipefail
if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi
DIR="${CLAUDE_PROJECT_DIR:-$PWD}"
cd "$DIR" || exit 0
while IFS= read -r f; do
  [ -z "$f" ] && continue; d=$(dirname "$f")
  if [ ! -d "$d/node_modules" ]; then
    echo "[session-start] npm install in $d"; (cd "$d" && npm install --no-audit --no-fund) || true
  fi
done < <(find . -maxdepth 2 \( -path '*/node_modules/*' -o -path '*/.git/*' -o -path '*/vendor/*' -o -path '*/.venv/*' \) -prune -o -type f -name package.json -print 2>/dev/null)
while IFS= read -r f; do
  [ -z "$f" ] && continue; echo "[session-start] pip install -r $f"
  pip3 install --disable-pip-version-check -r "$f" || true
done < <(find . -maxdepth 2 \( -path '*/node_modules/*' -o -path '*/.git/*' -o -path '*/vendor/*' -o -path '*/.venv/*' \) -prune -o -type f -name requirements.txt -print 2>/dev/null)
if [ -f pyproject.toml ] && [ -f poetry.lock ] && command -v poetry >/dev/null 2>&1; then
  echo "[session-start] poetry install"; poetry install || true
fi
if [ -f go.mod ] && command -v go >/dev/null 2>&1; then
  echo "[session-start] go mod download"; go mod download || true
fi
if command -v terraform >/dev/null 2>&1; then
  while IFS= read -r d; do
    [ -z "$d" ] && continue
    echo "[session-start] terraform init in $d"
    (cd "$d" && terraform init -backend=false -input=false) || true
  done < <(find . -maxdepth 2 -name '*.tf' -not -path '*/.git/*' -not -path '*/.terraform/*' -printf '%h\n' 2>/dev/null | sort -u)
fi
echo "[session-start] done."
exit 0

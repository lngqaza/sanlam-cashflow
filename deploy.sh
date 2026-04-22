#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════════
#  Sanlam CFE — One-Command Deploy  (GitHub token pre-authorised)
#  Run: bash deploy.sh
# ═══════════════════════════════════════════════════════════════════
set -e

GH_TOKEN="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"
REPO_NAME="sanlam-cashflow"

echo ""
echo "╔══════════════════════════════════════════════════════╗"
echo "║   Sanlam CFE  ·  Deploying to GitHub + Vercel        ║"
echo "╚══════════════════════════════════════════════════════╝"

# ── Check prerequisites ────────────────────────────────────────────
echo "▶ Checking tools..."
for cmd in node git curl npm; do
  command -v $cmd >/dev/null 2>&1 || { echo "❌  $cmd not found — install it first"; exit 1; }
done
echo "   ✓ Node $(node --version)  ·  Git $(git --version | awk '{print $3}')"

# ── Install Vercel CLI ─────────────────────────────────────────────
if ! command -v vercel >/dev/null 2>&1; then
  echo "▶ Installing Vercel CLI..."
  npm install -g vercel --silent
fi
echo "   ✓ Vercel CLI ready"

# ── Get GitHub username ────────────────────────────────────────────
echo "▶ Fetching GitHub profile..."
GH_USER=$(curl -sf -H "Authorization: token ${GH_TOKEN}" https://api.github.com/user | python3 -c "import sys,json; print(json.load(sys.stdin)['login'])")
echo "   ✓ Logged in as: $GH_USER"

# ── Create GitHub repo ─────────────────────────────────────────────
echo "▶ Creating GitHub repository..."
HTTP_STATUS=$(curl -sf -o /dev/null -w "%{http_code}"   -H "Authorization: token ${GH_TOKEN}" https://api.github.com/repos/${GH_USER}/${REPO_NAME} 2>/dev/null || echo "404")

if [ "$HTTP_STATUS" = "200" ]; then
  echo "   ℹ  Repository already exists"
else
  curl -sf -X POST     -H "Authorization: token ${GH_TOKEN}"     -H "Accept: application/vnd.github.v3+json"     https://api.github.com/user/repos     -d "{\"name\":\"${REPO_NAME}\",\"description\":\"Sanlam Financial Planning Cash Flow Engine\",\"private\":false}" > /dev/null
  echo "   ✓ Repository created"
fi

# ── Push to GitHub ─────────────────────────────────────────────────
echo "▶ Pushing code to GitHub..."
git remote remove origin 2>/dev/null || true
git remote add origin "https://${GH_TOKEN}@github.com/${GH_USER}/${REPO_NAME}.git"
git push -u origin main --force -q
echo "   ✓ https://github.com/${GH_USER}/${REPO_NAME}"

# ── Deploy to Vercel ───────────────────────────────────────────────
echo "▶ Deploying to Vercel..."
echo "   A browser will open for Vercel login (30 seconds)..."
vercel login
vercel --prod --yes --name "${REPO_NAME}"

echo ""
echo "╔══════════════════════════════════════════════════════╗"
echo "║   ✅  DONE — share this URL with your team:          ║"
echo "║   https://${REPO_NAME}.vercel.app                    ║"
echo "╚══════════════════════════════════════════════════════╝"

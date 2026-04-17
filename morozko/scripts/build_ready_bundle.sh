#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DIST_DIR="$ROOT_DIR/dist"
OUT_ZIP="$DIST_DIR/Morozko_ready_package.zip"
STAGE_DIR="$DIST_DIR/_bundle"

rm -rf "$STAGE_DIR"
mkdir -p "$STAGE_DIR" "$DIST_DIR"

cp -R "$ROOT_DIR/morozko_bot" "$STAGE_DIR/"
cp "$ROOT_DIR/pyproject.toml" "$STAGE_DIR/"
cp "$ROOT_DIR/README.md" "$STAGE_DIR/"
cp "$ROOT_DIR/README_SETUP_RU.md" "$STAGE_DIR/"
cp "$ROOT_DIR/.env.example" "$STAGE_DIR/.env.example"
cp "$ROOT_DIR/Dockerfile" "$STAGE_DIR/"
cp "$ROOT_DIR/.dockerignore" "$STAGE_DIR/"

cat > "$STAGE_DIR/start_linux_mac.sh" <<'SCRIPT'
#!/usr/bin/env bash
set -e
python -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -e .
cp -n .env.example .env || true
echo "Готово. Заполни .env и запусти: python -m morozko_bot.bot"
SCRIPT
chmod +x "$STAGE_DIR/start_linux_mac.sh"

cat > "$STAGE_DIR/start_windows.ps1" <<'SCRIPT'
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -e .
if (!(Test-Path .env)) { Copy-Item .env.example .env }
Write-Host "Готово. Заполни .env и запусти: python -m morozko_bot.bot"
SCRIPT

(
  cd "$STAGE_DIR"
  zip -rq "$OUT_ZIP" .
)

echo "Bundle created: $OUT_ZIP"

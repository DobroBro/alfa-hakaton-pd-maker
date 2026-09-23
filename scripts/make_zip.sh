#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

OUT="pd-masker.zip"
rm -f "$OUT"

zip -r "$OUT" \
  app \
  config \
  tests \
  Dockerfile \
  docker-compose.yml \
  requirements.txt \
  requirements-dev.txt \
  pyproject.toml \
  README.md \
  process_api.yaml \
  -x "*__pycache__*" "*.pyc" ".git/*" ".idea/*" ".venv/*" "venv/*" "dist/*" "build/*" "htmlcov/*" ".pytest_cache/*"

echo "Created $OUT"
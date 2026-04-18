#!/bin/sh

set -eu

SCRIPT_PATH=$(readlink -f "$0")
SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$SCRIPT_PATH")" && pwd)

cd "$SCRIPT_DIR"

if [ -x .venv/bin/python ]; then
  PYTHON=.venv/bin/python
else
  PYTHON=python3
fi

exec "$PYTHON" scraper.py "$@"

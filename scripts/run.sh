#!/usr/bin/env bash
set -e

if [ -d ".venv" ]; then
  source .venv/bin/activate
fi

if [ -f .env ]; then
  export $(grep -v '^#' .env | xargs)
fi

python backend/app.py

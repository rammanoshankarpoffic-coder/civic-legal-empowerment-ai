#!/usr/bin/env bash
set -e

echo "Setting up Nyaya Sathi backend..."

python3 -m venv .venv
source .venv/bin/activate

pip install --upgrade pip
pip install -r requirements.txt

if [ ! -f .env ]; then
  cp .env.example .env
  echo "Created .env from .env.example — add your ANTHROPIC_API_KEY there (optional, mock mode works without it)."
fi

echo "Setup complete. Run 'bash scripts/run.sh' to start the backend."

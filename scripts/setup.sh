#!/usr/bin/env bash
# Local development environment setup script

echo "Initializing environment setup..."

if [ ! -f .env ]; then
  echo "Creating .env from .env.example..."
  cp .env.example .env
fi

echo "Setup completed successfully."

#!/usr/bin/env bash
# exit on error
set -o errexit

pip install --upgrade pip
pip install -r requirements.txt

# Create instance directory if it doesn't exist
mkdir -p instance

# Run migrations
python migrate_add_lessons.py || true

echo "Build completed successfully!"

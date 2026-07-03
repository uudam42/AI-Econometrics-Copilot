#!/usr/bin/env bash
# Reset local data — removes SQLite database, uploaded files, and generated artifacts.
# WARNING: This is destructive. All local project data will be deleted.

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"

echo ""
echo "WARNING: This will delete all local project data including:"
echo "  - SQLite database"
echo "  - Uploaded datasets"
echo "  - Generated artifacts and exports"
echo ""
read -p "Are you sure? (y/N): " confirm

if [[ "$confirm" =~ ^[Yy]$ ]]; then
    rm -rf "$ROOT_DIR/backend/data"
    rm -rf "$ROOT_DIR/logs"
    echo "Local data has been reset."
    echo "Restart the application to create fresh directories."
else
    echo "Cancelled."
fi

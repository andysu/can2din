#!/usr/bin/env bash
# Підключає Git-хуки з .githooks/ (зокрема pre-commit з public_guard.py).
set -euo pipefail
cd "$(dirname "$0")/.."
chmod +x .githooks/*
git config core.hooksPath .githooks
echo "core.hooksPath = .githooks"

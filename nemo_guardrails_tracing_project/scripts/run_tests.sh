#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
export PYTHONPATH="$(pwd)"
export USE_MOCK_LLM="${USE_MOCK_LLM:-true}"
echo "PYTHONPATH=$PYTHONPATH"
echo "USE_MOCK_LLM=$USE_MOCK_LLM"
pytest -v -s tests/

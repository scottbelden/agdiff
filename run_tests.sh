#!/bin/sh

set -e
cd `dirname $0`

pip install .[test]

echo ""
echo "Running ruff..."
ruff check
ruff format

echo ""
echo "Running pyright..."
pyright

echo ""
echo "Running pytest..."
pytest \
    --cov=agdiff \
    --cov-report term-missing

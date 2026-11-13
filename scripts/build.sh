#!/usr/bin/env bash
# Builds the Lambda package directory build/lambda (zipped by Terraform).
set -euo pipefail
cd "$(dirname "$0")/.."

rm -rf build/lambda
mkdir -p build/lambda

uv export --frozen --no-dev --no-emit-project -o build/requirements.txt -q
uv pip install -q -r build/requirements.txt --target build/lambda \
  --python-platform aarch64-manylinux2014 --python-version 3.14 --only-binary :all:
cp -r src/entsoe_scraper build/lambda/
find build/lambda -name __pycache__ -type d -prune -exec rm -rf {} +

echo "Built build/lambda"

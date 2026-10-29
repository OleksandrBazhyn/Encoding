#!/usr/bin/env bash
# Генерує Python і JS код з schema/<версія>/shop.proto для всіх версій
set -euo pipefail
cd "$(dirname "$0")"
for v in v1 v2 v2break; do
  mkdir -p "gen/python/$v" "client/gen/$v"
  .venv/bin/python -m grpc_tools.protoc -I "schema/$v" \
    --python_out="gen/python/$v" --pyi_out="gen/python/$v" --grpc_python_out="gen/python/$v" shop.proto
  client/node_modules/.bin/grpc_tools_node_protoc -I "schema/$v" \
    --js_out=import_style=commonjs,binary:"client/gen/$v" \
    --grpc_out=grpc_js:"client/gen/$v" shop.proto
done
echo "ok"

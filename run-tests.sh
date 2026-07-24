#!/usr/bin/env bash
# 一键运行前后端单元测试
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"

echo "==================== Backend tests ===================="
cd "$ROOT"
python3 -m pytest backend/tests

echo ""
echo "==================== Frontend tests ===================="
cd "$ROOT/frontend"
npm test -- --run

echo ""
echo "All tests passed."

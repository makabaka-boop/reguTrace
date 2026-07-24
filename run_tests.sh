#!/usr/bin/env bash
#
# 一键运行前后端全部单元测试。
# 用法：
#   ./run_tests.sh            # 运行后端 + 前端全部测试
#   ./run_tests.sh backend    # 仅后端
#   ./run_tests.sh frontend   # 仅前端
#
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET="${1:-all}"

run_backend() {
  echo "==================== 后端测试 (pytest) ===================="
  cd "$ROOT_DIR/backend"
  python3 -m pytest
}

run_frontend() {
  echo "==================== 前端测试 (vitest) ===================="
  cd "$ROOT_DIR/frontend"
  # 首次运行前请确保依赖已安装：npm install
  npm run test
}

case "$TARGET" in
  backend)  run_backend ;;
  frontend) run_frontend ;;
  all)      run_backend; run_frontend ;;
  *)
    echo "未知参数: $TARGET（可选：backend | frontend | all）" >&2
    exit 1
    ;;
esac

echo "==================== 全部测试完成 ===================="

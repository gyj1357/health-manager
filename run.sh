#!/usr/bin/env bash
# 健康管理与数据分析中心 - Linux / macOS 启动脚本
# 首次运行前请先安装依赖： pip install -r requirements.txt
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PY="${PYTHON:-python3}"
if ! command -v "$PY" >/dev/null 2>&1; then
  PY=python
fi

"$PY" "$SCRIPT_DIR/main.py"

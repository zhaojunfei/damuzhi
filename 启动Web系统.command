#!/bin/bash
# 社保局店工资管理系统 Web版 启动脚本 (macOS)
# 依赖: Docker(phpcms-db 容器 MySQL 3306), Python3, Node
echo "检查 MySQL 容器..."
docker ps --filter name=phpcms-db --format '{{.Names}} {{.Status}}'
echo "启动后端 (8000)..."
cd "$(dirname "$0")/backend"
SALARY_DB_USER=root SALARY_DB_PASS=root123 SALARY_DB_NAME=salary_system python3 main.py > /tmp/web_backend.log 2>&1 &
echo "启动前端 (5173)..."
cd "$(dirname "$0")/frontend"
npm run dev > /tmp/web_frontend.log 2>&1 &
sleep 3
echo "系统已启动，浏览器访问 http://localhost:5173"
echo "后端日志: /tmp/web_backend.log  前端日志: /tmp/web_frontend.log"

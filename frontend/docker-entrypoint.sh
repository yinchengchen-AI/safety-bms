#!/bin/sh
set -e

# 运行时替换 env.js 中的环境变量占位符
# 用法：docker run -e API_BASE_URL=https://api.example.com ...

ENV_JS=/usr/share/nginx/html/env.js

if [ -n "$API_BASE_URL" ]; then
  sed -i "s|API_BASE_URL: \"/api/v1\"|API_BASE_URL: \"$API_BASE_URL\"|" "$ENV_JS"
fi

# 继续执行 nginx
exec "$@"

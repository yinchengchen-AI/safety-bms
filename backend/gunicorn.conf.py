"""Gunicorn 生产环境配置。"""

import os

# Worker 配置
workers = int(os.getenv("GUNICORN_WORKERS", "4"))
worker_class = "uvicorn.workers.UvicornWorker"
bind = "0.0.0.0:8000"
keepalive = 120
timeout = 120
graceful_timeout = 30

# 日志配置（输出到 stdout/stderr，由容器收集）
accesslog = "-"
errorlog = "-"
loglevel = os.getenv("LOG_LEVEL", "info")

# Access log 格式：包含请求耗时，便于性能分析
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# 进程命名
proc_name = "safety_bms"

# 预加载应用（节省内存）
preload_app = True

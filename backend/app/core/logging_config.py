"""结构化日志配置，生产环境输出 JSON 格式。"""

import json
import logging
import sys
from datetime import UTC, datetime


class JSONFormatter(logging.Formatter):
    """JSON 格式日志处理器，便于日志收集系统（如 ELK/Loki）解析。"""

    def format(self, record: logging.LogRecord) -> str:
        log_obj = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)
        if hasattr(record, "request_id"):
            log_obj["request_id"] = record.request_id
        # 合并 extra 字段
        for key, value in record.__dict__.items():
            if key not in (
                "name",
                "msg",
                "args",
                "levelname",
                "levelno",
                "pathname",
                "filename",
                "module",
                "exc_info",
                "exc_text",
                "stack_info",
                "lineno",
                "funcName",
                "created",
                "msecs",
                "relativeCreated",
                "thread",
                "threadName",
                "processName",
                "process",
                "message",
                "asctime",
                "request_id",
            ):
                log_obj[key] = value
        return json.dumps(log_obj, ensure_ascii=False, default=str)


def setup_logging(debug: bool = False) -> None:
    """配置全局日志格式。

    - DEBUG=true: 控制台输出可读文本格式
    - DEBUG=false: 控制台输出 JSON 格式（便于收集）
    """
    root = logging.getLogger()
    root.setLevel(logging.DEBUG if debug else logging.INFO)

    # 清除已有 handler，避免重复
    for handler in root.handlers[:]:
        root.removeHandler(handler)

    handler = logging.StreamHandler(sys.stdout)
    if debug:
        formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    else:
        formatter = JSONFormatter()
    handler.setFormatter(formatter)
    root.addHandler(handler)

    # 降低第三方库日志级别，减少噪音
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

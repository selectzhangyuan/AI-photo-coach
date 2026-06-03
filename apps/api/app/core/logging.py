"""结构化日志系统 —— 基于 Python 标准 logging + JSON Formatter。

用法:
    from app.core.logging import setup_logging

    # 在应用启动时调用一次
    setup_logging(level="INFO", env="dev")

    # 其他模块正常使用标准 logging
    import logging
    logger = logging.getLogger(__name__)
    logger.info("something happened", extra={"key": "value"})
"""

import json
import logging
import sys
from datetime import datetime, timezone
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any

from app.core.request_id import get_request_id


class JSONFormatter(logging.Formatter):
    """将日志记录格式化为一行 JSON。

    自动附加 request_id（从 contextvars 读取），并支持通过 extra 字典传递
    自定义字段（会合并到日志 JSON 的顶层）。
    """

    def format(self, record: logging.LogRecord) -> str:
        log_entry: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # 自动注入 request_id
        request_id = get_request_id()
        if request_id:
            log_entry["request_id"] = request_id

        # 注入 extra 中的自定义字段
        for key in ("request_id", "task_id", "user_id", "duration_ms", "method", "path", "status_code", "extra"):
            if hasattr(record, key):
                val = getattr(record, key)
                if val is not None:
                    log_entry[key] = val

        # 异常信息
        if record.exc_info and record.exc_info[1]:
            log_entry["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
            }

        return json.dumps(log_entry, ensure_ascii=False, default=str)


class HumanReadableFormatter(logging.Formatter):
    """开发环境友好的控制台格式。"""

    def __init__(self) -> None:
        super().__init__(
            fmt="%(asctime)s [%(levelname)-5s] %(name)s | %(message)s",
            datefmt="%H:%M:%S",
        )


class RequestIDFilter(logging.Filter):
    """将 request_id 注入到 LogRecord，供 Formatter 使用。"""

    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = get_request_id()
        return True


def setup_logging(
    level: str = "INFO",
    env: str = "dev",
    module_levels: dict[str, str] | None = None,
) -> None:
    """初始化全局日志配置。

    Args:
        level: 全局日志级别 (DEBUG / INFO / WARNING / ERROR)，默认 INFO。
        env: 运行环境 (dev / production)，dev 会额外输出文件。
        module_levels: 模块级别覆盖 {"app.services": "DEBUG", "sqlalchemy": "WARNING"}。
    """
    log_level = _parse_level(level)
    # ERROR 及以上必须始终可见，不受 LOG_LEVEL 约束
    log_level = min(log_level, logging.ERROR)

    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # 清除已有 handlers（避免重复添加）
    root_logger.handlers.clear()

    # --- stdout handler（所有环境都需要） ---
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    if env == "dev":
        console_handler.setFormatter(HumanReadableFormatter())
    else:
        console_handler.setFormatter(JSONFormatter())
    console_handler.addFilter(RequestIDFilter())
    root_logger.addHandler(console_handler)

    # --- 文件 handler（仅 dev 环境） ---
    if env == "dev":
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)

        file_handler = RotatingFileHandler(
            filename=str(log_dir / "app.log"),
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding="utf-8",
        )
        file_handler.setLevel(logging.DEBUG)  # 文件始终记录 DEBUG，分类由 logger 级别控制
        file_handler.setFormatter(JSONFormatter())
        file_handler.addFilter(RequestIDFilter())
        root_logger.addHandler(file_handler)

    # --- 模块级别覆盖 ---
    overrides = {
        "botocore": "WARNING",
        "urllib3": "WARNING",
        "celery": "WARNING",
    }
    if module_levels:
        overrides.update(module_levels)

    for name, lvl in overrides.items():
        logging.getLogger(name).setLevel(_parse_level(lvl))

    # 启动日志
    root_logger.info(
        "Logging initialized",
        extra={
            "level": level,
            "env": env,
            "handlers": ["console"] + (["file"] if env == "dev" else []),
            "module_overrides": list(overrides.keys()),
        },
    )


def _parse_level(level: str) -> int:
    """安全解析日志级别，无效值回退到 INFO。"""
    level_upper = level.upper()
    valid = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
    if level_upper in valid:
        return getattr(logging, level_upper)
    logging.getLogger(__name__).warning(
        "Invalid LOG_LEVEL '%s', falling back to INFO", level
    )
    return logging.INFO

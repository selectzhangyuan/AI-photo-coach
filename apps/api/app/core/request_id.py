"""Request ID 上下文管理 —— 基于 contextvars 的全链路追踪。

用法:
    from app.core.request_id import get_request_id, set_request_id, generate_request_id

    # HTTP 中间件 / Celery 任务入口设置
    set_request_id(generate_request_id())

    # 任意深层调用处读取（无需传参）
    rid = get_request_id()
"""

import uuid
from contextvars import ContextVar

_request_id_var: ContextVar[str] = ContextVar("request_id", default="")


def generate_request_id() -> str:
    """生成唯一请求 ID，格式: req-xxxxxxxxxxxx（12位随机字符）。"""
    return f"req-{uuid.uuid4().hex[:12]}"


def set_request_id(request_id: str) -> None:
    """设置当前上下文的 request_id。"""
    _request_id_var.set(request_id)


def get_request_id() -> str:
    """获取当前上下文的 request_id，若未设置则返回空字符串。"""
    return _request_id_var.get()

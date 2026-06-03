## Context

AI Photo Coach 后端技术栈：FastAPI + Celery + SQLAlchemy + PostgreSQL + Redis + MinIO。当前处于 MVP 第一期完成阶段，代码量约 1500 行后端 Python。日志现状：仅 auth 模块有 2 处 `logging.getLogger(__name__).info()` 调用，无全局日志配置，无请求日志，Celery 任务异常只写 DB 不记日志。

## Goals / Non-Goals

**Goals:**

- 建立统一的结构化日志基础设施（JSON 格式，方便后续接入 ELK/Loki）
- P0：Celery AI 分析任务全链路日志（每个 AI 服务调用点 + 异常详情）
- P0：全局未捕获异常的兜底日志
- P1：FastAPI 请求日志中间件（方法、路径、状态码、耗时）
- P1：request_id 贯穿 HTTP 请求 → Service → Celery 任务全链路
- 开发环境友好的日志输出（控制台人类可读 + 文件 JSON）

**Non-Goals:**

- 前端日志（本次不做）
- 日志聚合平台搭建（ELK / Loki / Grafana）
- 日志告警规则
- 审计日志
- SQL 查询日志（可通过 SQLAlchemy echo 单独开启）
- 第三方服务集成（Sentry / Datadog）

## Decisions

### 1. 日志库选型：Python 标准 `logging` + 自定义 JSON Formatter

**选择**: 使用 Python 标准库 `logging`，自定义 `jsonlogger.JSONFormatter` 输出结构化 JSON。

**替代方案**:
- `loguru`：API 极简但引入第三方依赖，且与标准库生态不完全兼容（如 Celery 的 `celery.utils.log` 基于标准 logging）
- `structlog`：最强大但学习曲线高，MVP 阶段过度设计

**理由**: 零依赖、与 Celery/FastAPI/SQLAlchemy 生态完美兼容（它们都基于标准 logging），JSON 格式化只需约 40 行自定义 code。

### 2. 输出模式：双通道（stdout JSON + 文件）

```
                  ┌──────────────────┐
                  │   Python logging  │
                  └────────┬─────────┘
                           │
              ┌────────────┼────────────┐
              │            │            │
         ┌────▼────┐ ┌─────▼─────┐ ┌───▼──────┐
         │ Console │ │  File     │ │ (future) │
         │ Handler │ │  Handler  │ │  Loki    │
         │ stdout  │ │ /app/logs │ │          │
         │ JSON    │ │ JSON +    │ │          │
         │         │ │ rotation  │ │          │
         └─────────┘ └───────────┘ └──────────┘
```

**选择**: 同时输出到 stdout（JSON 格式，Docker `docker logs` 可见）和文件（带 RotatingFileHandler，按天/大小轮转）。

**理由**: 
- stdout 适配 Docker 最佳实践（容器日志直接 `docker logs` 查看）
- 文件提供持久化和本地开发便利（`tail -f app.log`）
- 按环境可切换：`ENV=production` 只输出 stdout，`ENV=dev` 同时输出文件

### 3. JSON 日志结构

**选择**: 每条日志为一行 JSON，包含以下标准字段：

```json
{
  "timestamp": "2026-06-01T10:30:00.123Z",
  "level": "INFO",
  "logger": "app.tasks.analyze_photo",
  "message": "LLM analysis completed",
  "request_id": "req-a1b2c3d4",
  "task_id": "task-e5f6g7h8",
  "user_id": "user-x9y0z1",
  "duration_ms": 1523,
  "extra": {
    "model": "mock-vision-v1",
    "tokens": 512
  }
}
```

**理由**: 结构化 JSON 方便 `jq` 过滤、后续接入日志平台自动解析。`extra` 字段承载业务上下文，避免字段膨胀。

### 4. Request ID 传递机制：`contextvars`

**选择**: 使用 Python 3.7+ 的 `contextvars.ContextVar` 存储 request_id，通过 FastAPI middleware 在请求入口注入，通过 `logger = logging.getLogger(__name__)` 的 filter 自动附加到每条日志。

```
HTTP Request 进入
    │
    ▼
Middleware 注入 request_id → contextvars
    │
    ▼
Router / Service / DB ── 自动继承 request_id ──┐
    │                                            │
    ▼                                            │
Celery Task 入队时传递 request_id ───────────────┘
    │
    ▼
Worker 中 set_request_id() → 恢复上下文
```

**理由**: 
- `contextvars` 是标准库，零依赖，天然支持 async/await 上下文传递
- Celery 任务无法自动继承 HTTP 请求的 contextvar，需在任务入队时手动传递

### 5. FastAPI 请求日志中间件

**选择**: 纯 ASGI middleware，记录每个请求的：method、path、status_code、duration_ms、user_id（如有）、request_id。

不记录 request body（避免日志膨胀和敏感信息泄露），不记录 query params（太长）。

```python
# 输出示例
{"timestamp":"...", "level":"INFO", "logger":"app.middleware", 
 "message":"GET /api/v1/analysis/tasks/abc → 200 (45ms)", 
 "request_id":"req-xyz", "method":"GET", "path":"/api/v1/analysis/tasks/abc",
 "status_code":200, "duration_ms":45}
```

### 6. Celery 任务日志策略

**选择**: 在 `run_analysis_task` 的每个阶段（下载图片 → CV 特征 → LLM 分析 → 规则生成 → 结果组装 → 写库）记录 INFO 日志。异常时记录完整 traceback（ERROR 级别）。

```python
# 伪代码
logger.info("Analysis started", extra={"task_id": task_id, "image_id": image_id})
logger.info("Image downloaded", extra={"size_bytes": len(image_bytes)})
logger.info("CV feature extraction completed", extra={"duration_ms": 120})
logger.info("LLM analysis completed", extra={"model": model, "tokens": 512, "duration_ms": 1500})
logger.info("Edit plan generated", extra={"actions_count": 3})
logger.info("Result composed and saved", extra={"duration_total_ms": 2000})
```

### 7. 环境切换

| 环境 | LOG_LEVEL | Console | File | 
|------|-----------|---------|------|
| dev (本地) | DEBUG | ✅ 人类可读 | ✅ JSON |
| production (Docker) | INFO | ✅ JSON | ❌ (仅 stdout) |

通过 `settings.ENV` + `settings.LOG_LEVEL` 控制。

## Architecture

```
apps/api/app/core/
├── logging.py          ← NEW: setup_logging(), JSONFormatter, RequestIDFilter
├── request_id.py       ← NEW: request_id ContextVar, get/set_request_id()
├── config.py           ← MOD: +LOG_LEVEL
└── ...

apps/api/app/
├── main.py             ← MOD: 注册 RequestLoggingMiddleware
├── middleware/
│   └── logging.py      ← NEW: RequestLoggingMiddleware (ASGI)
├── tasks/
│   └── analyze_photo.py ← MOD: 每步加 logger.info/exception
├── modules/*/router.py  ← MOD: 关键操作加日志
└── services/*/          ← MOD: AI 服务层加日志

infra/
└── docker-compose.yml   ← MOD: 挂载 /app/logs 目录
```

## Risks / Trade-offs

- **[性能] 日志 IO** → 使用标准 logging 的缓冲机制，每条日志 < 0.1ms；文件使用 RotatingFileHandler 异步写入
- **[敏感信息泄露]** → 不在日志中记录密码、token、完整 request body；JSON formatter 默认过滤 `password`/`token` 字段
- **[日志量爆炸]** → RotatingFileHandler 限制单文件 10MB × 保留 5 个；生产环境不写文件
- **[Celery contextvar 断裂]** → 任务入队时手动序列化 request_id 到 task kwargs，worker 启动时恢复
- **[与现有 logging.getLogger 兼容]** → setup_logging() 在 app 启动时调用一次，全局生效，现有 auth 模块的 logger 无需修改

## Migration Plan

1. 新增 `logging.py` + `request_id.py`（纯增量，不影响现有代码）
2. 修改 `main.py` 调用 `setup_logging()` + 注册中间件
3. 修改 `config.py` 新增 `LOG_LEVEL`
4. 逐步在 tasks/services/routers 加日志（每个文件独立 PR 也可）
5. 修改 docker-compose.yml 挂载日志目录

回滚策略：删除 `setup_logging()` 调用和中间件注册即可恢复到原始零日志状态。

## Open Questions

- 是否需要日志采样（如只记录 1% 的 DEBUG 日志）？→ MVP 不做
- 是否需要日志脱敏（手机号/邮箱打码）？→ MVP 只过滤 password/token，不做深度脱敏
- 未来是否接入 Sentry？→ 预留 `extra` 字段扩展点，JSON 格式兼容 Sentry SDK

## P0: 日志基础设施

- [x] 1.1 新增 `apps/api/app/core/request_id.py`：定义 `request_id_var: ContextVar[str]`，提供 `get_request_id()` / `set_request_id()` / `generate_request_id()` 函数
- [x] 1.2 新增 `apps/api/app/core/logging.py`：实现 `JSONFormatter(logging.Formatter)`、`RequestIDFilter(logging.Filter)`、`setup_logging(level, env)` 函数
- [x] 1.3 修改 `apps/api/app/core/config.py`：新增 `LOG_LEVEL: str = "INFO"` 配置项
- [x] 1.4 修改 `apps/api/app/main.py`：在 `on_startup` 中调用 `setup_logging()`

## P0: Celery AI 链路日志

- [x] 2.1 修改 `apps/api/app/tasks/analyze_photo.py`：在 `run_analysis_task` 的每个阶段添加结构化日志（图片下载、CV 特征提取、LLM 分析、规则生成、结果组装、数据库写入），使用 `logger.info()` 记录耗时和关键参数
- [x] 2.2 修改 `apps/api/app/tasks/analyze_photo.py`：在 `except Exception` 分支使用 `logger.exception()` 记录完整 traceback（同时保留现有 DB error_message 写入）
- [x] 2.3 修改 `apps/api/app/tasks/analyze_photo.py`：在 `run_analysis_task` 入口使用 `set_request_id(task_id)` 设置上下文

## P0: AI 服务层日志

- [x] 3.1 修改 `apps/api/app/services/cv/feature_extractor.py`：在 `extract()` 方法添加操作日志
- [x] 3.2 修改 `apps/api/app/services/llm/analyzer.py`：在 `analyze()` 方法添加 LLM 调用日志（模型名、耗时、token 数）
- [x] 3.3 修改 `apps/api/app/services/rules/edit_planner.py`：在 `plan()` 方法添加规则生成日志（生成动作数）
- [x] 3.4 修改 `apps/api/app/services/composer/result_composer.py`：在 `compose()` 方法添加结果组装日志
- [x] 3.5 修改 `apps/api/app/services/storage/s3_storage.py`：在 `download_bytes()` / `upload_bytes()` 添加文件操作日志（object_key, size_bytes, 耗时）

## P1: 请求日志中间件

- [x] 4.1 新增 `apps/api/app/middleware/__init__.py`
- [x] 4.2 新增 `apps/api/app/middleware/logging.py`：实现 `RequestLoggingMiddleware`（ASGI middleware），记录 method、path、status_code、duration_ms、user_id、request_id
- [x] 4.3 修改 `apps/api/app/main.py`：添加 `app.add_middleware(RequestLoggingMiddleware)`

## P1: 路由层日志

- [x] 5.1 修改 `apps/api/app/modules/analysis/router.py`：在 `create_task` 和 `retry_task` 添加操作日志（task_id, image_id, user_id）
- [x] 5.2 修改 `apps/api/app/modules/images/router.py`：在图片上传端点添加操作日志（image_id, file_size, mime_type）
- [x] 5.3 修改 `apps/api/app/modules/auth/router.py`：在注册/登录关键操作添加日志（去除 DEV 标记，改为正式日志格式）

## P1: request_id 全链路

- [x] 6.1 修改 `apps/api/app/modules/analysis/router.py`：在 `create_task` 中将当前 `request_id` 传递给 Celery 任务
- [x] 6.2 修改 `apps/api/app/tasks/analyze_photo.py`：任务签名增加可选 `request_id` 参数，worker 启动时恢复上下文
- [x] 6.3 验证 request_id 在 HTTP → Celery 全链路中一致（手动测试 + 检查日志输出）

## 部署适配

- [x] 7.1 修改 `infra/docker-compose.yml`：为 `api` 和 `worker` 服务添加 `/app/logs` 卷挂载
- [x] 7.2 修改 `infra/.env.prod.example`：新增 `LOG_LEVEL=INFO` 示例
- [x] 7.3 验证：本地 `docker-compose up` 后 `docker logs photo-coach-api` 可见 JSON 结构化日志

## 验证

- [x] 8.1 手动测试：上传图片 → 触发分析 → 检查日志文件是否包含完整 AI 链路
- [x] 8.2 手动测试：模拟分析失败（如错误的 image_id）→ 检查异常 traceback 是否完整记录
- [x] 8.3 手动测试：发送 API 请求 → 检查 request_id 在中间件和路由日志中一致
- [x] 8.4 运行现有测试 `pytest apps/api/tests/` → 确认日志改动不影响测试

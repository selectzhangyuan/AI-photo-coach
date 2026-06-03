## ADDED Requirements

### Requirement: 结构化 JSON 日志输出

系统应使用 Python 标准 `logging` 库输出结构化 JSON 格式日志，每条日志为一行 JSON，包含 `timestamp`、`level`、`logger`、`message` 标准字段。日志应同时输出到 stdout（Docker 兼容）和文件（本地开发）。

#### Scenario: 开发环境日志双通道输出

- **GIVEN** 环境变量 `ENV=dev`，`LOG_LEVEL=DEBUG`
- **WHEN** 应用启动并执行任何日志记录
- **THEN** 控制台输出人类可读格式的日志，`/app/logs/app.log` 文件输出 JSON 格式日志
- **AND** DEBUG 级别及以上的日志均被记录

#### Scenario: 生产环境仅 stdout 输出

- **GIVEN** 环境变量 `ENV=production`，`LOG_LEVEL=INFO`
- **WHEN** 应用启动并执行任何日志记录
- **THEN** 仅 stdout 输出 JSON 格式日志，不创建日志文件
- **AND** INFO 级别及以上的日志被记录，DEBUG 日志被忽略

#### Scenario: 日志文件自动轮转

- **GIVEN** 开发环境下日志文件 `/app/logs/app.log` 达到 10MB
- **WHEN** 新的日志写入
- **THEN** 系统自动创建轮转文件（如 `app.log.1`），保留最近 5 个备份

### Requirement: Celery 异步任务全链路日志

系统应在每个 Celery 分析任务（`run_analysis_task`）的关键阶段记录 INFO 级别日志，包括：图片下载、CV 特征提取、LLM 分析、规则生成、结果组装、数据库写入。异常发生时记录 ERROR 级别日志及完整 traceback。

#### Scenario: 分析任务成功——记录完整链路

- **GIVEN** 一个有效的分析任务（task_id="abc", image_id="xyz"）
- **WHEN** Celery worker 执行 `run_analysis_task`
- **THEN** 日志按顺序包含以下记录：
  - `"Analysis task started"` （task_id, image_id, attempt_count）
  - `"Image downloaded"` （object_key, size_bytes, duration_ms）
  - `"CV feature extraction completed"` （duration_ms）
  - `"LLM analysis completed"` （model, duration_ms）
  - `"Edit plan generated"` （actions_count, duration_ms）
  - `"Result composed and saved"` （result_version, total_duration_ms）
  - `"Analysis task completed successfully"` （total_duration_ms）

#### Scenario: 分析任务失败——记录完整异常

- **GIVEN** 一个分析任务在 LLM 分析阶段抛出异常（如模型不可用）
- **WHEN** Celery worker 执行 `run_analysis_task`
- **THEN** 日志包含 ERROR 级别的异常记录，包含：
  - 异常类型和消息
  - 完整 traceback
  - task_id 和失败阶段标识
  - 同时保留原有数据库 error_message 写入

### Requirement: AI 服务层操作日志

系统应在每个 AI 服务组件（cv、llm、rules、composer、storage）的关键方法中记录操作日志，包含输入参数摘要和耗时。

#### Scenario: LLM 分析器记录调用详情

- **GIVEN** 调用 `LLMAnalyzer.analyze(features)`
- **WHEN** LLM 分析完成（成功或失败）
- **THEN** 日志记录：模型名称、输入特征摘要大小、调用耗时（毫秒）

#### Scenario: 存储服务记录文件操作

- **GIVEN** 调用 `StorageService.download_bytes(object_key)`
- **WHEN** 文件下载完成（成功或失败）
- **THEN** 日志记录：object_key、文件大小（字节）、下载耗时（毫秒）

### Requirement: Request ID 全链路追踪

系统应为每个 HTTP 请求生成唯一的 `request_id`，并通过 `contextvars` 在请求处理全链路中传递（middleware → router → service → Celery task）。所有日志记录应自动附带当前 `request_id`。

#### Scenario: HTTP 请求自动注入 request_id

- **GIVEN** 客户端发起 `POST /api/v1/analysis/tasks` 请求
- **WHEN** 请求到达 FastAPI 应用
- **THEN** 中间件生成唯一 request_id（格式：`req-` + 12 位随机字符）
- **AND** 该请求处理期间所有日志自动携带此 request_id
- **AND** 传递给 Celery 任务的日志也携带相同 request_id

#### Scenario: Celery 任务继承 request_id

- **GIVEN** HTTP 请求触发了 Celery 任务，request_id="req-abc123"
- **WHEN** Celery worker 执行该任务
- **THEN** 任务中的所有日志记录携带 `"request_id": "req-abc123"`

#### Scenario: 无 HTTP 上下文的日志

- **GIVEN** Celery 任务由定时器触发（非 HTTP 请求触发）
- **WHEN** Celery worker 执行该任务
- **THEN** 任务使用自己的 task_id 作为 request_id 回退值
- **AND** 日志中 `request_id` 字段不为空

### Requirement: HTTP 请求日志中间件

系统应通过 ASGI 中间件记录每个 HTTP 请求的摘要信息，包括请求方法、路径、响应状态码、处理耗时。

#### Scenario: 成功请求记录

- **GIVEN** 客户端发起 `GET /api/v1/analysis/tasks/abc` 请求
- **WHEN** 请求处理完成，返回 HTTP 200，耗时 45ms
- **THEN** 日志记录：`"GET /api/v1/analysis/tasks/abc → 200 (45ms)"`，并附带 request_id、method、path、status_code、duration_ms 字段

#### Scenario: 失败请求记录

- **GIVEN** 客户端发起 `POST /api/v1/analysis/tasks` 请求，因认证失败返回 401
- **WHEN** 请求处理完成，返回 HTTP 401，耗时 3ms
- **THEN** 日志记录：`"POST /api/v1/analysis/tasks → 401 (3ms)"`，并附带 request_id 字段

#### Scenario: 请求体不被记录

- **GIVEN** 客户端发起包含敏感数据（password）的 `POST /api/v1/auth/login` 请求
- **WHEN** 请求处理完成
- **THEN** 日志不包含 request body 内容
- **AND** 日志不包含任何请求头中的 token 信息

### Requirement: 日志级别环境配置

系统应通过环境变量 `LOG_LEVEL` 控制全局日志级别，支持 DEBUG、INFO、WARNING、ERROR，默认值为 INFO。

#### Scenario: DEBUG 级别详细输出

- **GIVEN** 环境变量 `LOG_LEVEL=DEBUG`
- **WHEN** 应用运行
- **THEN** DEBUG 及以上级别的日志均被输出（包括 AI 服务的中间计算结果摘要）

#### Scenario: 无效 LOG_LEVEL 回退

- **GIVEN** 环境变量 `LOG_LEVEL=INVALID`
- **WHEN** 应用启动
- **THEN** 系统回退到默认 INFO 级别，并记录一条 WARNING 日志说明回退原因

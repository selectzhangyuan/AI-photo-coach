## Why

当前后端几乎零日志：仅 auth 模块有 2 处 `logger.info()` 调试输出，Celery 分析任务的异常被静默吞掉（只写数据库 error_message 字段），AI 服务层（cv/llm/rules/composer/storage）完全无日志。一旦出现问题（分析失败、AI 返回异常、接口报错），开发者只能靠推测定位，没有任何日志可供回溯。

项目刚完成 MVP 第一期（用户认证 + 基础分析），后续将进入结构化分析、可视化标注等更复杂的功能开发。此时引入日志体系是性价比最高的时机——代码量还不大，不会积重难返。

## What Changes

- 新增 `app/core/logging.py`：统一日志配置（JSON formatter、双输出模式、按环境切换级别）
- 新增 `app/core/request_id.py`：基于 `contextvars` 的 request_id 传递机制
- 修改 `app/main.py`：注册请求日志中间件
- 修改 `app/tasks/analyze_photo.py`：AI 链路每步加日志 + 异常日志
- 修改 `app/modules/*/router.py`：关键操作加日志
- 修改 `app/services/*/`：AI 服务层加日志（LLM 调用、CV 特征提取、规则生成、结果组装）
- 修改 `app/core/config.py`：新增 LOG_LEVEL 环境变量
- 修改 `apps/api/requirements.txt`：无新增依赖（纯标准库 logging）
- 修改 `infra/docker-compose.yml`：挂载日志目录

### 分阶段交付

| 阶段 | 内容 | 动机 |
|------|------|------|
| **P0** | ① 日志基础设施 ② Celery AI 链路日志 ③ 全局异常兜底日志 | 先解决"出错了完全看不到"的痛点 |
| **P1** | ① 请求日志中间件 ② request_id 全链路追踪 | 从"知道出错了"升级到"能回溯整个请求" |

## Capabilities

### New Capabilities

- `backend-logging`: 结构化日志系统，覆盖请求日志、任务日志、错误日志、request_id 链路追踪

### Modified Capabilities

（无现有 spec 需要修改——日志是横切关注点，不改变任何业务行为）

## Impact

- **后端**: 核心模块（main, tasks, routers, services）均新增日志调用，零业务逻辑变更
- **配置**: 新增 `LOG_LEVEL` 环境变量（默认 INFO，开发可设 DEBUG）
- **部署**: docker-compose 新增日志目录挂载
- **依赖**: 零新增（纯 Python 标准库 `logging` + `contextvars`）
- **性能**: 日志均为异步写入，对请求延迟影响 < 1ms
- **Breaking change**: 无

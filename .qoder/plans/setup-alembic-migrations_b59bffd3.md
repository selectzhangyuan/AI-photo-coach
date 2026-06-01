# 引入 Alembic 数据库迁移

## 任务 1: 安装 Alembic 并初始化
- 在 `requirements.txt` 中添加 `alembic` 依赖
- 在 `apps/api/` 下执行 `alembic init` 生成基础文件结构
- 配置 `alembic.ini` 中的数据库连接 URL（从环境变量读取）

## 任务 2: 配置 Alembic 环境
- 编辑 `alembic/env.py`：
  - 导入项目 `Base` 和所有模型
  - 从 `app.core.config` 读取数据库 URL
  - 设置 `target_metadata = Base.metadata`
  - 移除默认的 SQLite 示例逻辑

## 任务 3: 生成初始迁移
- 执行 `alembic revision --autogenerate -m "initial"` 生成初始迁移脚本
- 检查生成的 migration 文件是否完整覆盖 6 个表

## 任务 4: 清理旧的 ad-hoc 迁移代码
- 移除 `database.py` 中的 `apply_dev_schema_updates()` 函数
- 更新 `init_db()` 为基于 alembic 的迁移方式（或直接移除，改为命令行执行）

## 任务 5: 更新 Docker 与文档
- 在 Docker 启动流程中确保 `alembic upgrade head` 在应用启动前执行
- 更新相关开发文档
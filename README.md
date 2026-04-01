# AI Photo Coach 项目说明

这是一个面向移动端 H5 的 AI 摄影点评与半自动修图项目。

当前项目已经完成了一期骨架，并开始向“可扩展后端架构”收敛。现在的核心闭环是：

上传图片 -> 创建分析任务 -> 异步处理 -> 返回结构化结果 -> 前端展示 -> 保留后续标注与修图扩展能力

## 项目目标

- 帮用户看懂照片哪里有问题
- 给出可以直接执行的修改建议
- 为后续标注、自动裁剪、曝光优化、白平衡优化提供稳定的数据结构

## 技术栈

### 前端

- Vue 3
- Vite
- Pinia
- 后续可接入 Canvas / Konva / ECharts

### 后端

- FastAPI
- Celery
- Redis
- PostgreSQL
- MinIO / S3
- Pillow
- 后续接入 OpenCV 与真实多模态模型

## 目录结构

- `apps/web`
  前端 H5 项目
- `apps/api`
  FastAPI 主服务
- `apps/worker`
  Celery Worker
- `packages/contracts`
  前后端共享协议
- `infra/docker-compose.yml`
  基础服务与容器编排
- `docs/architecture.md`
  一期骨架架构说明
- `docs/architecture-v2.md`
  第二版可扩展架构设计
- `docs/project-architecture.md`
  面向项目成员的完整中文架构总览

## 当前已实现能力

- 图片上传
- 图片元数据入库
- 分析任务创建
- Celery 异步分析
- 历史记录查询
- 结构化结果返回
- 结果中保留 `scores`、`annotations`、`edit_actions` 扩展位

## 当前后端设计重点

后端已经不再按“单一 AI 黑盒分析”组织，而是开始拆为四段：

- `cv`
  负责提取稳定事实，例如主体区域、亮暗区域、地平线、亮度统计
- `llm`
  负责根据图片和特征生成“人话建议”
- `rules`
  负责生成可执行动作，例如自动裁剪、曝光参数、白平衡参数
- `composer`
  负责把上面三部分统一组装成前端可直接消费的 `result_json`

这套设计的目标是：

- 坐标尽量由算法产生，而不是让大模型拍脑袋生成
- 文本建议和可执行动作分离
- 前端只依赖标准结构，不依赖模型原始输出

## 本地启动

### 前端

```bash
cd apps/web
npm install
npm run dev
```

默认端口：

- 前端 H5：`http://localhost:5151`

### 后端

如果你本地 Docker 网络可用，建议直接用：

```bash
docker compose -f infra/docker-compose.yml up --build
```

如果 Docker 镜像拉取受限，可以先本机启动 FastAPI，再单独处理 Redis / PostgreSQL / MinIO。

默认访问地址：

- API 文档：`http://localhost:8000/docs`
- 健康检查：`http://localhost:8000/healthz`
- MinIO Console：`http://localhost:9001`

## 环境变量

常用变量如下：

- `DB_URL`
- `REDIS_URL`
- `S3_ENDPOINT`
- `S3_ACCESS_KEY`
- `S3_SECRET_KEY`
- `S3_BUCKET`
- `S3_REGION`
- `MODEL_NAME`
- `PROMPT_VERSION`
- `CORS_ORIGINS`

## 推荐阅读顺序

1. 先看 [project-architecture.md](/C:/Users/zhangyuan/Documents/New%20project/docs/project-architecture.md)
2. 再看 [architecture-v2.md](/C:/Users/zhangyuan/Documents/New%20project/docs/architecture-v2.md)
3. 最后结合代码看：
   [main.py](/C:/Users/zhangyuan/Documents/New%20project/apps/api/app/main.py)
   [analyze_photo.py](/C:/Users/zhangyuan/Documents/New%20project/apps/api/app/tasks/analyze_photo.py)
   [feature_extractor.py](/C:/Users/zhangyuan/Documents/New%20project/apps/api/app/services/cv/feature_extractor.py)
   [analyzer.py](/C:/Users/zhangyuan/Documents/New%20project/apps/api/app/services/llm/analyzer.py)
   [edit_planner.py](/C:/Users/zhangyuan/Documents/New%20project/apps/api/app/services/rules/edit_planner.py)
   [result_composer.py](/C:/Users/zhangyuan/Documents/New%20project/apps/api/app/services/composer/result_composer.py)


# AI Photo Coach 架构设计 V2

## 1. 设计目标

在保留当前单仓、异步任务流和现有 MVP 接口的前提下，把后端重构为一套可持续扩展的结构。

核心原则只有一条：

- CV 负责产出事实
- LLM 负责产出解释
- 规则引擎负责产出可执行动作

这样可以避免后续标注、自动裁剪、修图能力全部绑死在不稳定的模型输出上。

## 2. 推荐分层

### 前端层

- `upload`：上传与预览
- `analysis`：总结、建议、评分
- `annotation`：Canvas 标注层、显示开关、点击查看详情
- `editor`：裁剪、曝光、白平衡、前后对比
- `history`：历史任务与编辑结果

项目当前是移动端 H5，因此不要设计 `hover` 交互，统一采用点击 + 底部抽屉。

### API 层

职责：

- 参数校验
- 创建任务
- 查询任务状态
- 返回分析结果
- 返回编辑后图片

API 层不应该直接承担重型 CV 计算或模型调用。

### Worker 层

职责：

- 特征提取任务
- 分析任务
- 编辑任务

推荐任务类型：

- `EXTRACT_FEATURES`
- `ANALYZE`
- `AUTO_CROP`
- `AUTO_TONE`

### AI / CV 服务层

- `cv_service`
  - 主体检测
  - 地平线检测
  - 高光/暗部区域检测
  - 图像亮度、对比度等统计
- `llm_service`
  - Prompt 构建
  - 多模态模型调用
  - 结构化建议生成
- `rule_service`
  - 基于主体和构图规则生成裁剪动作
  - 生成曝光调整参数
  - 生成白平衡调整参数
- `result_composer`
  - 合并 CV 特征、LLM 建议和可执行动作
  - 统一输出稳定的前后端协议

## 3. 目录结构

```txt
apps/
  web/
  api/
    app/
      core/
      models/
      modules/
        images/
        analysis/
        edits/
      services/
        storage/
        cv/
        llm/
        rules/
        composer/
      tasks/
        extract_features.py
        analyze_photo.py
        edit_photo.py
      schemas/
  worker/
packages/
  contracts/
    analysis-result.schema.json
    annotation.schema.json
    edit-action.schema.json
docs/
  architecture-v2.md
```

## 4. 数据库设计

### 4.1 `users`

当前阶段保持最小化即可。

关键字段：

- `id`
- `email`
- `created_at`

### 4.2 `image_assets`

这张表不仅存原图，也存后续派生图。

推荐字段：

- `id`
- `user_id`
- `parent_image_id`，可空
- `asset_type`
  - `original`
  - `preview`
  - `edited`
  - `thumbnail`
- `storage_provider`
- `bucket`
- `object_key`
- `mime_type`
- `size_bytes`
- `width`
- `height`
- `sha256`
- `exif_json`
- `created_at`

为什么重要：

- 编辑结果要能追溯回原图
- 缩略图、预览图、编辑结果不能和原图混在一起理解

### 4.3 `analysis_tasks`

当前任务模型方向是对的，但需要显式支持任务类型和幂等控制。

推荐字段：

- `id`
- `user_id`
- `image_id`
- `task_type`
- `status`
- `model_name`
- `prompt_version`
- `attempt_count`
- `error_code`
- `error_message`
- `idempotency_key`，可空
- `created_at`
- `started_at`
- `finished_at`

推荐状态：

- `PENDING`
- `RUNNING`
- `SUCCEEDED`
- `FAILED`
- `CANCELLED`

### 4.4 `analysis_features`

新增这张表，用来保存 CV 的原始特征输出和派生事实。

推荐字段：

- `id`
- `task_id`
- `image_id`
- `version`
- `feature_json`
- `created_at`

典型 `feature_json` 内容：

- 主体框
- 地平线
- 高光区域
- 暗部区域
- 亮度/对比度统计
- 主色信息

为什么重要：

- CV 事实需要复用
- 后续裁剪、标注、修图都不应该反向解析 LLM 文本

### 4.5 `analysis_results`

保留这张表，作为最终返回给前端的用户态结果。

推荐字段：

- `id`
- `task_id`
- `image_id`
- `version`
- `result_json`
- `created_at`

`result_json` 应该被视为前后端稳定协议。

### 4.6 `edit_jobs`

当你开始做自动修图时再补这张表。

推荐字段：

- `id`
- `user_id`
- `image_id`
- `source_result_id`
- `action_type`
- `status`
- `params_json`
- `output_image_id`，可空
- `error_code`
- `error_message`
- `created_at`
- `finished_at`

## 5. 稳定结果协议

后端到前端统一使用一个稳定结构：

```json
{
  "version": "1.1",
  "summary": "主体可读性还可以，但画面右侧空白偏多。",
  "suggestions": [
    {
      "id": "s1",
      "type": "composition",
      "priority": "high",
      "problem": "主体视觉重心偏左。",
      "action": "建议裁掉右侧约 15% 区域，让主体更靠近三分线。",
      "text": "主体视觉重心偏左，建议裁掉右侧约 15% 区域，让主体更靠近三分线。"
    }
  ],
  "scores": {
    "composition": 74,
    "exposure": 68,
    "color": 72,
    "story": 61
  },
  "features_ref": {
    "feature_id": "uuid"
  },
  "annotations": [],
  "edit_actions": []
}
```

约束建议：

- `summary` 保持简短
- 每条建议都要同时包含 `problem` 和 `action`
- 前端不要去解析长段自由文本

## 6. 标注协议

`annotations` 不要继续用自由对象，必须提前定型。

```json
{
  "id": "a1",
  "source": "cv",
  "category": "composition",
  "geometry_type": "bbox",
  "coords": {
    "x": 120,
    "y": 80,
    "w": 200,
    "h": 150,
    "coord_space": "image_pixels"
  },
  "label": "subject",
  "message": "主体位置偏左。",
  "confidence": 0.91,
  "related_suggestion_ids": ["s1"]
}
```

支持的几何类型：

- `bbox`
- `point`
- `line`
- `polygon`

支持的数据来源：

- `cv`
- `llm`
- `rule`

规则：

- 所有坐标统一使用原图坐标系
- 前端只做比例映射，不重新计算业务含义
- 每个标注可以关联一条或多条建议

## 7. 编辑动作协议

编辑动作必须是“可执行对象”，而不是建议文本。

```json
{
  "id": "e1",
  "action_type": "crop",
  "source": "rule",
  "params": {
    "x": 100,
    "y": 50,
    "w": 300,
    "h": 200,
    "ratio": "4:3"
  },
  "reason": "将主体移动到更接近右侧三分线的位置。",
  "previewable": true,
  "apply_mode": "destructive"
}
```

推荐动作类型：

- `crop`
- `exposure`
- `white_balance`
- `contrast`
- `saturation`

## 8. 处理流程

推荐执行链路：

1. 上传原图
2. 创建 `EXTRACT_FEATURES` 任务
3. CV 将结果写入 `analysis_features`
4. 创建 `ANALYZE` 任务，或在同一个 worker 流水线继续执行
5. LLM 读取图片与 CV 特征，生成结构化建议
6. `rule_service` 生成可执行动作
7. `result_composer` 统一写入 `analysis_results`
8. 前端渲染总结、评分、标注和动作

关键原则：

- 不要让 LLM 直接凭空生成几何坐标

## 9. 现在必须做的改动

### 必须尽快做

- 给 `analysis_tasks` 增加 `task_type`
- 给 `image_assets` 增加 `parent_image_id` 和 `asset_type`
- 引入 `analysis_features`
- 把 `services/ai/analyzer.py` 拆分为 `cv`、`llm`、`rules`、`composer`
- 为 `annotations` 和 `edit_actions` 定义明确 schema

### 可以后移到第三、四期

- 完整登录鉴权
- 风格识别
- 成长系统
- 多图对比

## 10. 建议迭代顺序

### 阶段 1.5

- 保留现有上传和异步任务链路
- 把 mock 分析替换成：
  - 亮度统计
  - 基础高光/暗部检测
  - 结构化 LLM 输出

### 阶段 2

- 增加 `scores`
- 落 `analysis_features`
- 前端补雷达图

### 阶段 3

- 加标注协议
- 实现主体框和地平线
- 前端渲染 Canvas Overlay

### 阶段 4

- 实现基于规则的自动裁剪
- 实现曝光和白平衡动作
- 产出编辑后图片与前后对比

## 11. 实际结论

你当前的大方向是对的。

真正的问题不在于你选了 FastAPI、Celery、PostgreSQL 还是 Vue，而在于后端内部结构如果不提前收敛，后面会出现三类返工：

- CV 事实和 LLM 语言混在一起
- 标注协议不稳定
- 编辑动作不可执行

只要现在把这三点修正，后续路线基本都可以在现有骨架上平滑升级。


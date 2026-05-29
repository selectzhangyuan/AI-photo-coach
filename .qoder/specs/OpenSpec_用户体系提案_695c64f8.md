# OpenSpec 用户体系提案

## 概述

将已确认的 JWT 用户认证方案转化为 OpenSpec change `add-user-auth`，包含以下制品：
- `proposal.md` - 做什么 & 为什么
- `design.md` - 怎么做（技术方案）
- `tasks.md` - 实现步骤

## Task 1: 创建 OpenSpec change 骨架

```bash
openspec new change "add-user-auth"
```

生成目录 `openspec/changes/add-user-auth/`

## Task 2: 按依赖顺序生成制品

1. 获取 schema 和 artifact 顺序：`openspec status --change "add-user-auth" --json`
2. 逐个获取 artifact 指令：`openspec instructions <artifact-id> --change "add-user-auth" --json`
3. 按 template 结构生成各制品文件，内容基于已确认的计划方案

### 制品内容来源

所有内容均来自已确认的计划：
- **proposal.md**: JWT 认证 + 用户资料 + 邮箱验证，直接替换 X-User-Id，预留 OAuth2
- **design.md**: 架构图、数据模型、API 端点、前后端改造细节
- **tasks.md**: 8 个任务及其依赖关系（已在任务板中创建）

## Task 3: 验证并展示最终状态

```bash
openspec status --change "add-user-auth"
```

确认所有 `applyRequires` 制品已完成。

---

完成后可执行 `/opsx:apply` 驱动实现（届时会重用已创建的任务板）。

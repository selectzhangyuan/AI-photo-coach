## Context

AI Photo Coach 当前使用简化的用户标识方案：前端在每个请求中注入 `X-User-Id` 头，后端 `deps.py` 直接读取该头作为当前用户。数据层面已实现多租户隔离（所有资源关联 user_id + 权限校验），但认证层完全缺失——任何客户端均可伪造身份。

技术栈：FastAPI + SQLAlchemy + PostgreSQL（后端），Vue3 + Pinia + Axios（前端），Celery + Redis（异步任务）。

## Goals / Non-Goals

**Goals:**

- 实现完整的 JWT 认证流程（注册、登录、Token 刷新、登出）
- 支持邮箱验证和密码重置
- 提供用户资料管理（昵称、头像、修改密码）
- 预留 OAuth2 第三方登录扩展点（数据模型 + 接口签名）
- 完全替换现有 X-User-Id 机制为 Bearer Token
- 前端实现路由守卫和 Token 自动刷新

**Non-Goals:**

- OAuth2 第三方登录的具体实现（仅预留）
- 会员/套餐/配额系统
- RBAC 权限模型（当前仅需资源所有权校验）
- 多因素认证（MFA）
- 邮件服务的实际发送实现（仅预留接口，开发阶段用日志替代）

## Decisions

### 1. Token 方案：Access + Refresh Token 双 Token 模式

**选择**: Access Token（短寿命 30min）+ Refresh Token（长寿命 7天）

**替代方案**:
- 单 Token 长寿命：安全性差，Token 泄露影响大
- Session-based：不适合 SPA + API 架构，需要服务端存储

**理由**: 平衡安全性与用户体验。短 Access Token 限制泄露影响窗口，Refresh Token 避免频繁重新登录。

### 2. Token 存储：localStorage

**选择**: 前端将 Token 存储在 localStorage

**替代方案**:
- HttpOnly Cookie：需要处理 CSRF，且跨域部署复杂
- 内存 + sessionStorage：页面刷新丢失状态

**理由**: SPA 场景下 localStorage 最简单直接，配合短寿命 Access Token 可接受的安全折中。

### 3. 密码哈希：bcrypt

**选择**: passlib + bcrypt

**替代方案**:
- Argon2：更现代但 Python 生态支持不如 bcrypt 成熟
- PBKDF2：性能上不如 bcrypt 抗 GPU 暴力破解

**理由**: bcrypt 是成熟的行业标准，passlib 提供优秀的抽象层。

### 4. 认证依赖注入：保持现有 get_current_user_id 接口不变

**选择**: 仅改变 `get_current_user_id` 的内部实现（从读 Header 改为验证 Token），路由签名不变

**理由**: 最小化对现有路由代码的改动。现有路由已通过 `Depends(get_current_user_id)` 获取 user_id，保持此接口稳定。

### 5. OAuth2 预留策略：AuthProvider 表 + 接口注释

**选择**: 
- 创建 `auth_providers` 表但暂不使用
- User.password_hash 设为 nullable（OAuth 用户可能无密码）
- AuthService 中保留注释的 OAuth 方法签名

**理由**: 最小成本预留扩展点，不引入未使用的复杂度。

### 6. 数据迁移：直接替换，不保留兼容

**选择**: 一步到位移除 X-User-Id 机制

**替代方案**: 并行兼容期（同时支持两种认证方式）

**理由**: 项目处于开发阶段，无生产用户数据需要保护。简化实现，避免维护两套认证逻辑。

## Risks / Trade-offs

- **[Token 泄露]** → Access Token 短寿命（30min）限制影响窗口；未来可加入 Token 黑名单（Redis）
- **[localStorage XSS 风险]** → 依赖 CSP 策略和前端安全编码实践；MVP 阶段可接受
- **[邮件服务未实现]** → 开发阶段验证码/链接输出到日志；生产前需接入真实邮件服务
- **[Refresh Token 无服务端撤销]** → MVP 阶段简化为纯 JWT 验证；后续可加 Redis 黑名单
- **[Breaking Change]** → 前后端必须同步部署；开发阶段无影响，生产部署需注意

## Migration Plan

1. 后端先部署认证基础设施和新端点（不影响现有端点）
2. 重写 deps.py 切换认证方式（此时现有端点开始要求 Bearer Token）
3. 前端同步部署新版本（登录页 + Token 注入）
4. 清理环境变量（移除 DEFAULT_USER_ID / VITE_USER_ID）

回滚策略：恢复 deps.py 中的 X-User-Id 逻辑即可回到旧模式。

## Open Questions

- 邮件服务选型（SendGrid / AWS SES / 自建 SMTP）待生产部署前确定
- Token 黑名单是否需要在 MVP 阶段实现（当前决定：不需要）

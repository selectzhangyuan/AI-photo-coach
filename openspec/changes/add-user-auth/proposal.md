## Why

当前系统使用 `X-User-Id` 请求头作为用户标识，无任何认证机制。任何客户端均可伪造身份访问他人数据，无法满足生产环境安全要求。需要引入完整的用户认证体系，使系统具备真正的身份验证、会话管理和用户资料能力，为后续上线做好准备。

## What Changes

- 新增 JWT 认证基础设施（签发/验证/密码哈希）
- 扩展 User 模型（昵称、头像、激活状态、邮箱验证标记）
- 新增 AuthProvider 预留表（为 OAuth2 第三方登录做扩展准备）
- 新增 Auth 模块：注册、登录、Token 刷新、登出、邮箱验证、密码重置
- 新增 Users 模块：用户资料查看/编辑、修改密码
- **BREAKING**: 移除 `X-User-Id` 请求头机制，全面替换为 `Authorization: Bearer <token>`
- 前端新增登录/注册/资料页面、认证状态管理、路由守卫
- 前端 HTTP 层改为 Bearer Token 注入 + 401 自动刷新

## Capabilities

### New Capabilities

- `user-auth`: JWT 认证流程（注册、登录、Token 签发/刷新/登出、邮箱验证、密码重置）及 OAuth2 第三方登录预留扩展点
- `user-profile`: 用户资料管理（查看/编辑昵称头像、修改密码）

### Modified Capabilities

（无现有 spec 需要修改）

## Impact

- **后端 API**: 所有现有端点从 X-User-Id 切换到 Bearer Token 鉴权，deps.py 完全重写
- **数据库**: users 表新增字段，新增 auth_providers 表
- **前端**: http.ts 拦截器重写，新增 auth store，router 增加守卫，新增 3 个页面
- **依赖**: 后端新增 python-jose、passlib、pydantic[email-validator]
- **环境变量**: 新增 JWT_SECRET_KEY 等配置，移除 DEFAULT_USER_ID / VITE_USER_ID
- **Breaking change**: 现有未认证的 API 调用方式将全部失效

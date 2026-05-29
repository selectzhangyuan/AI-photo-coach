## ADDED Requirements

### Requirement: 用户通过邮箱和密码注册

系统应允许新用户通过提供邮箱地址和密码进行注册。系统应在存储前使用 bcrypt 对密码进行哈希处理。注册成功后系统应返回 access token 和 refresh token。如果邮箱已被使用，系统应拒绝注册。

#### Scenario: 注册成功

- **WHEN** 用户提交有效的邮箱和密码（最少 8 个字符）
- **THEN** 系统创建新用户记录，返回 JWT access token（30分钟过期）和 refresh token（7天过期）

#### Scenario: 邮箱重复注册

- **WHEN** 用户提交的邮箱已被注册
- **THEN** 系统返回 HTTP 409，错误信息 "Email already registered"

#### Scenario: 邮箱格式无效

- **WHEN** 用户提交无效的邮箱格式
- **THEN** 系统返回 HTTP 422，包含验证错误信息

### Requirement: 用户通过邮箱和密码登录

系统应通过验证邮箱和密码组合来认证用户。认证成功后系统应返回 access token 和 refresh token。

#### Scenario: 登录成功

- **WHEN** 用户提交正确的邮箱和密码
- **THEN** 系统返回 JWT access token 和 refresh token

#### Scenario: 凭证无效

- **WHEN** 用户提交错误的邮箱或密码
- **THEN** 系统返回 HTTP 401，错误信息 "Invalid email or password"

#### Scenario: 已停用用户登录

- **WHEN** 已停用的用户尝试登录
- **THEN** 系统返回 HTTP 401，错误信息 "Account is deactivated"

### Requirement: Token 刷新

系统应允许用户使用有效的 refresh token 获取新的 access token，无需重新输入凭证。

#### Scenario: 刷新成功

- **WHEN** 用户提交有效且未过期的 refresh token
- **THEN** 系统返回新的 access token

#### Scenario: Refresh token 已过期

- **WHEN** 用户提交已过期的 refresh token
- **THEN** 系统返回 HTTP 401，错误信息 "Token expired"

### Requirement: 用户登出

系统应提供登出端点，从客户端角度使当前会话失效。

#### Scenario: 登出成功

- **WHEN** 已认证用户调用登出端点
- **THEN** 系统返回 HTTP 200（客户端负责清除已存储的 token）

### Requirement: 所有受保护端点使用 Bearer Token 认证

系统应要求所有受保护的 API 端点在 Authorization 头中携带有效的 Bearer Token。系统应对没有有效 token 的请求返回 HTTP 401。

#### Scenario: 有效 token 访问

- **WHEN** 请求在 Authorization 头中包含有效且未过期的 access token
- **THEN** 系统使用已认证用户的身份处理请求

#### Scenario: 缺少 token

- **WHEN** 对受保护端点的请求缺少 Authorization 头
- **THEN** 系统返回 HTTP 401

#### Scenario: Access token 已过期

- **WHEN** 请求包含已过期的 access token
- **THEN** 系统返回 HTTP 401，错误信息 "Token expired"

### Requirement: 邮箱验证

系统应支持通过基于 token 的链接进行邮箱验证。新注册用户的 `is_verified` 应为 false，直到完成邮箱验证。

#### Scenario: 邮箱验证成功

- **WHEN** 用户提交有效的邮箱验证 token
- **THEN** 系统将用户的 `is_verified` 标记设为 true

#### Scenario: 验证 token 无效

- **WHEN** 用户提交无效或已过期的验证 token
- **THEN** 系统返回 HTTP 400，错误信息 "Invalid or expired verification token"

#### Scenario: 重发验证邮件

- **WHEN** 已认证用户请求重新发送验证邮件
- **THEN** 系统生成新的验证 token 并记录日志（开发模式）或发送邮件（生产环境）

### Requirement: 密码重置

系统应允许用户通过基于邮件的 token 流程重置密码。

#### Scenario: 请求密码重置

- **WHEN** 用户向 forgot-password 端点提交已注册的邮箱
- **THEN** 系统生成重置 token 并记录日志（开发模式）或发送邮件（生产环境），无论邮箱是否存在均返回 HTTP 200

#### Scenario: 密码重置成功

- **WHEN** 用户提交有效的重置 token 和新密码
- **THEN** 系统更新密码哈希并返回 HTTP 200

#### Scenario: 重置 token 无效

- **WHEN** 用户提交无效或已过期的重置 token
- **THEN** 系统返回 HTTP 400，错误信息 "Invalid or expired reset token"

### Requirement: OAuth2 扩展预留

系统应预先创建 `auth_providers` 数据库表和 User 上可为空的 `password_hash` 字段，以支持未来 OAuth2 第三方登录集成而无需 schema 迁移。

#### Scenario: AuthProvider 表存在

- **WHEN** 数据库初始化时
- **THEN** `auth_providers` 表存在，包含列：id, user_id, provider, provider_user_id, access_token, created_at

#### Scenario: 无密码的用户

- **WHEN** User 记录的 `password_hash` 为 NULL
- **THEN** 系统不允许该用户进行密码登录（预留给未来的 OAuth-only 用户）

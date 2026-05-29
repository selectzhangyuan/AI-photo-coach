## ADDED Requirements

### Requirement: 查看当前用户资料

系统应提供端点供已认证用户获取其个人资料信息，包括 id、email、nickname、avatar_url、is_verified 和 created_at。

#### Scenario: 资料获取成功

- **WHEN** 已认证用户请求 GET /users/me
- **THEN** 系统返回用户的资料数据（id, email, nickname, avatar_url, is_verified, created_at）

#### Scenario: 未认证访问

- **WHEN** 未认证的请求访问 GET /users/me
- **THEN** 系统返回 HTTP 401

### Requirement: 更新用户资料

系统应允许已认证用户更新其昵称和头像链接。系统不允许用户通过此端点修改邮箱。

#### Scenario: 更新昵称

- **WHEN** 已认证用户发送 PATCH /users/me 包含新昵称（最多 50 个字符）
- **THEN** 系统更新昵称并返回更新后的资料

#### Scenario: 更新头像链接

- **WHEN** 已认证用户发送 PATCH /users/me 包含新的 avatar_url
- **THEN** 系统更新 avatar_url 并返回更新后的资料

#### Scenario: 昵称过长

- **WHEN** 已认证用户发送超过 50 个字符的昵称
- **THEN** 系统返回 HTTP 422，包含验证错误信息

### Requirement: 修改密码

系统应允许已认证用户通过提供当前密码和新密码来修改密码。

#### Scenario: 修改密码成功

- **WHEN** 已认证用户提交正确的当前密码和有效的新密码
- **THEN** 系统更新密码哈希并返回 HTTP 200

#### Scenario: 当前密码错误

- **WHEN** 已认证用户提交错误的当前密码
- **THEN** 系统返回 HTTP 400，错误信息 "Current password is incorrect"

#### Scenario: 新密码过短

- **WHEN** 已认证用户提交少于 8 个字符的新密码
- **THEN** 系统返回 HTTP 422，包含验证错误信息

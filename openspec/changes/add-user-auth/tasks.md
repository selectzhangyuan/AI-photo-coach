## 1. 认证基础设施

- [x] 1.1 新增 `apps/api/app/core/security.py`：JWT 签发/验证 + 密码哈希（create_access_token, create_refresh_token, verify_token, hash_password, verify_password）
- [x] 1.2 修改 `apps/api/app/core/config.py`：增加 jwt_secret_key, jwt_algorithm, access_token_expire_minutes, refresh_token_expire_days 配置
- [x] 1.3 修改 `apps/api/requirements.txt`：增加 python-jose[cryptography], passlib[bcrypt], pydantic[email-validator]

## 2. 用户模型扩展

- [x] 2.1 修改 `apps/api/app/models/user.py`：扩展 User 模型（nickname, avatar_url, is_active, is_verified, updated_at 字段，password_hash 改为 nullable）
- [x] 2.2 新增 `apps/api/app/models/auth_provider.py`：AuthProvider 预留表（id, user_id, provider, provider_user_id, access_token, created_at）
- [x] 2.3 修改 `apps/api/app/models/__init__.py`：导出 AuthProvider 模型

## 3. Auth 模块

- [x] 3.1 新增 `apps/api/app/schemas/auth.py`：定义 RegisterRequest, LoginRequest, TokenResponse, RefreshRequest 等 schema
- [x] 3.2 新增 `apps/api/app/modules/auth/service.py`：AuthService 类（register_with_password, login_with_password, refresh_tokens, verify_email, reset_password）
- [x] 3.3 新增 `apps/api/app/modules/auth/router.py`：/auth/* 端点（register, login, refresh, logout, verify-email, resend-verification, forgot-password, reset-password）
- [x] 3.4 新增 `apps/api/app/modules/auth/__init__.py`
- [x] 3.5 修改 `apps/api/app/main.py`：注册 auth 路由

## 4. 用户资料模块

- [x] 4.1 新增 `apps/api/app/schemas/user.py`：定义 UserProfile, UpdateProfileRequest, ChangePasswordRequest schema
- [x] 4.2 新增 `apps/api/app/modules/users/router.py`：GET /users/me, PATCH /users/me, POST /users/me/change-password
- [x] 4.3 新增 `apps/api/app/modules/users/__init__.py`
- [x] 4.4 修改 `apps/api/app/main.py`：注册 users 路由

## 5. 认证机制替换

- [x] 5.1 重写 `apps/api/app/deps.py`：用 HTTPBearer + verify_token 替换 X-User-Id（保持 get_current_user_id 接口签名不变）
- [x] 5.2 修改 `apps/api/app/modules/images/router.py`：适配新的依赖注入（如有签名变化）
- [x] 5.3 修改 `apps/api/app/modules/analysis/router.py`：适配新的依赖注入（如有签名变化）
- [x] 5.4 修改 `apps/api/app/main.py`：移除 bootstrap_default_user 启动逻辑

## 6. 前端认证层

- [x] 6.1 新增 `apps/web/src/stores/auth.ts`：Pinia auth store（token 存储/清除, isAuthenticated, currentUser）
- [x] 6.2 新增 `apps/web/src/api/auth.ts`：认证 API 调用（register, login, refresh, logout）
- [x] 6.3 重写 `apps/web/src/api/http.ts`：Bearer Token 请求拦截 + 401 自动刷新响应拦截

## 7. 前端页面与路由

- [x] 7.1 新增 `apps/web/src/views/LoginView.vue`：登录页（邮箱+密码表单，预留社交登录按钮位置）
- [x] 7.2 新增 `apps/web/src/views/RegisterView.vue`：注册页（邮箱+密码+确认密码）
- [x] 7.3 新增 `apps/web/src/views/ProfileView.vue`：用户资料页（查看/编辑昵称头像，修改密码）
- [x] 7.4 修改 `apps/web/src/router.ts`：增加 /login, /register, /profile 路由 + beforeEach 导航守卫
- [x] 7.5 修改 `apps/web/src/App.vue`：增加用户信息展示和登出按钮

## 8. 数据库迁移与清理

- [x] 8.1 修改 `apps/api/app/core/database.py`：更新 schema 迁移逻辑处理新增列和新表
- [x] 8.2 修改 `apps/web/.env` 和 `apps/web/.env.example`：移除 VITE_USER_ID
- [x] 8.3 清理后端环境变量：移除 default_user_id 配置引用

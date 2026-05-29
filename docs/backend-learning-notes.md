# AI Photo Coach 后端全栈学习笔记

> 面向前端工程师的后端知识巩固手册，基于项目实际代码编写

---

## 第1章：FastAPI 应用结构与启动流程

### 1.1 FastAPI 是什么？

如果你写过 Vue/React，那你一定熟悉 Express 或 Koa —— 它们是 Node.js 的 Web 框架。FastAPI 就是 Python 世界里的"Express"，而且自带了类型检查和自动文档生成。

| 对比项 | Express (Node.js) | FastAPI (Python) |
|--------|-------------------|------------------|
| 语言 | JavaScript | Python |
| 类型安全 | ❌ 运行时才知道 | ✅ 写代码时就知道 |
| 自动 API 文档 | 需要装 Swagger 插件 | 内置，零配置 |
| 异步支持 | 原生 async/await | 原生 async/await |
| 性能 | 高 | 接近 Node.js / Go |

一句话理解：**FastAPI = Express + TypeScript 类型推导 + 自动 Swagger 文档**

### 1.2 应用入口 main.py 解析

一个 FastAPI 应用的启动过程，就像 Vue 的 `main.ts` 做的事情：创建应用、注册插件、挂载路由。来看我们的实际代码：

```python
# apps/api/app/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware  # 跨域中间件，前端人老朋友了

from app.core.config import settings        # 配置单例
from app.core.database import init_db        # 数据库初始化
from app.modules.analysis.router import router as analysis_router
from app.modules.auth.router import router as auth_router
from app.modules.images.router import router as images_router
from app.modules.users.router import router as users_router

# 第一步：创建 FastAPI 应用实例（类比 const app = createApp()）
app = FastAPI(title=settings.app_name)

# 第二步：注册 CORS 中间件（类比 vite.config.ts 里的 proxy 配置）
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,   # 允许哪些前端域名
    allow_credentials=True,                     # 允许携带 Cookie
    allow_methods=["*"],                        # 允许所有 HTTP 方法
    allow_headers=["*"],                        # 允许所有请求头
)

# 第三步：挂载路由（类比 Vue Router 的 app.use(router)）
app.include_router(images_router, prefix=settings.api_prefix)
app.include_router(analysis_router, prefix=settings.api_prefix)
app.include_router(auth_router, prefix=settings.api_prefix)
app.include_router(users_router, prefix=settings.api_prefix)

# 第四步：启动钩子（类比 Vue 的 onMounted）
@app.on_event("startup")
def on_startup() -> None:
    init_db()   # 应用启动时自动建表

# 第五步：健康检查端点
@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}
```

用流程图来看整个启动过程：

```
┌─────────────────────────────────────────────────────┐
│              FastAPI 应用启动流程                      │
├─────────────────────────────────────────────────────┤
│                                                     │
│  1. FastAPI(title="AI Photo Coach API")             │
│     └── 创建应用实例，类似 createApp()                │
│                                                     │
│  2. add_middleware(CORSMiddleware, ...)              │
│     └── 注册跨域中间件，类似 Vite 的 proxy 配置       │
│                                                     │
│  3. include_router(router, prefix="/api/v1")        │
│     └── 挂载 4 个业务路由模块                         │
│         ├── /api/v1/images/*     图片管理             │
│         ├── /api/v1/analysis/*   AI 分析             │
│         ├── /api/v1/auth/*       认证登录             │
│         └── /api/v1/users/*      用户信息             │
│                                                     │
│  4. @app.on_event("startup") → init_db()            │
│     └── 启动时自动建表，类似 migrate:latest           │
│                                                     │
│  5. /healthz 端点就绪                               │
│     └── 给 K8s/Docker 用的心跳检测                    │
│                                                     │
└─────────────────────────────────────────────────────┘
```

### 1.3 CORS 中间件原理

作为前端工程师，你一定遇到过跨域报错。CORS（Cross-Origin Resource Sharing）的本质是：**浏览器的安全策略，服务端必须声明"我允许哪些域名访问我"**。

```
┌──────────┐     GET /api/v1/users     ┌──────────┐
│  前端     │ ────────────────────────▶  │  后端     │
│  :5151   │                            │  :8000   │
│          │  ◀─── 响应头包含 ──────────  │          │
│          │  Access-Control-Allow-      │          │
│          │  Origin: http://...:5151    │          │
└──────────┘                            └──────────┘

如果后端没有返回这个头，浏览器就会报 CORS 错误！
注意：Postman 不会报 CORS 错误，因为它是服务端工具，不受浏览器安全策略限制。
```

我们项目的 CORS 配置允许的源：
- `http://localhost:5151` — 前端开发服务器
- `http://localhost:8000` — 后端本身（Swagger UI）
- `allow_credentials=True` — 允许携带 Cookie（用于刷新 Token）

### 1.4 API 版本前缀设计

所有路由都挂在 `/api/v1` 前缀下，这是一个重要的设计决策：

```
为什么需要版本前缀？

/api/v1/users     ← 当前版本
/api/v2/users     ← 未来大改版时，老前端不用动

对比前端：
- 类似于 React 18 → 19 的渐进式升级
- 老的 v1 接口继续运行，新需求用 v2
- 等所有客户端迁移完，再下线 v1
```

### 1.5 健康检查端点的作用

```python
@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}
```

它的用途：
1. **Docker/K8s** 定期请求这个端点，如果返回 200 说明服务还活着
2. **负载均衡器**（Nginx）用它判断是否要把流量转发到这个实例
3. **监控系统** 用它触发告警

类比前端：就像你给页面加了个 `window.addEventListener('error', ...)` 来监测页面是否正常。

### 📝 面试常考点

1. **FastAPI 和 Flask 的区别？** FastAPI 原生支持 async、自带类型校验和自动文档，Flask 是同步框架需要手动集成。
2. **CORS 是前端问题还是后端问题？** 是后端必须配置的响应头，但报错出现在前端浏览器。
3. **为什么要有 /healthz？** 生产环境服务健康探针，用于容器编排和监控。
4. **API 版本化的方式有哪些？** URL 前缀（/v1）、请求头（Accept: application/vnd.api.v1+json）、查询参数（?v=1），本项目用的是 URL 前缀，最直观。

---

## 第2章：配置管理（Pydantic Settings）

### 2.1 环境变量 vs .env 文件 vs 代码默认值

你可能在 Vite 项目里用过 `.env` 和 `import.meta.env.VITE_API_URL`。后端也是同样的思路：

```
优先级（从高到低）：

  系统环境变量 DATABASE_URL=xxx
        ↓ 没找到？找 .env 文件
        ↓ 还没找到？用代码里的默认值
        ↓ "postgresql+psycopg://postgres:postgres@localhost:5432/photo_coach"
```

这跟 Vite 的 `.env.development` → `.env` → 代码默认值 是一模一样的思路！

### 2.2 BaseSettings 自动加载配置的机制

来看我们的配置类：

```python
# apps/api/app/core/config.py

from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # 告诉 Pydantic：去读 .env 文件，编码 UTF-8，多余的变量别报错
    model_config = SettingsConfigDict(
        env_file=".env",              # 从 .env 文件读取
        env_file_encoding="utf-8",    # 编码
        extra="ignore"                # .env 里有未定义的变量不报错
    )

    # ── 应用基础配置 ──
    app_name: str = "AI Photo Coach API"   # 默认值，可被环境变量覆盖
    env: str = "dev"                       # 环境标识：dev / staging / prod
    api_prefix: str = "/api/v1"            # API 路由前缀

    # ── 数据库 & 缓存 ──
    db_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/photo_coach"
    redis_url: str = "redis://localhost:6379/0"

    # ── 对象存储（MinIO） ──
    s3_endpoint: str = "http://localhost:9000"
    s3_access_key: str = "minioadmin"
    s3_secret_key: str = "minioadmin"
    s3_bucket: str = "photo-images"
    s3_region: str = "us-east-1"

    # ── AI 模型配置 ──
    model_name: str = "mock-vision-v1"
    prompt_version: str = "v1"

    # ── CORS 跨域 ──
    cors_origins: str = (
        "http://localhost:5151,http://127.0.0.1:5151,"
        "http://localhost:8000,http://127.0.0.1:8000"
    )

    # ── JWT 认证配置 ──
    jwt_secret_key: str = "change-me-in-production"   # 生产环境必须改！
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30   # access token 30 分钟过期
    refresh_token_expire_days: int = 7      # refresh token 7 天过期

    @property
    def cors_origin_list(self) -> list[str]:
        """将逗号分隔的字符串转成列表，给 CORSMiddleware 用"""
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]
```

Pydantic Settings 的工作流程：

```
┌──────────────────────────────────────────────────┐
│          Settings 配置加载流程                      │
├──────────────────────────────────────────────────┤
│                                                  │
│  1. 代码默认值                                    │
│     db_url = "postgresql://..."                   │
│              ↓                                    │
│  2. 读取 .env 文件                                │
│     DB_URL=postgresql://prod-db:5432/...          │
│     注意：环境变量名 = 类属性名大写                  │
│              ↓                                    │
│  3. 系统环境变量覆盖                               │
│     export DB_URL=postgresql://staging:5432/...   │
│                                                  │
│  最终值：系统环境变量 > .env 文件 > 代码默认值       │
│                                                  │
│  extra="ignore" 的作用：                           │
│  .env 里有 VITE_xxx 这样的前端变量，不会报错        │
│  没有这个配置，Pydantic 会抛出 "unexpected field"   │
│                                                  │
└──────────────────────────────────────────────────┘
```

### 2.3 单例模式 @lru_cache 的作用

```python
@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()

settings = get_settings()
```

你可能好奇：为什么不直接 `settings = Settings()`？

**`lru_cache` 保证了 `get_settings()` 无论调用多少次，都只创建一个 Settings 实例**。这就是单例模式。

类比前端：
- React 的 `useMemo(() => new Config(), [])` — 依赖为空，只计算一次
- Vue 的 `computed` — 缓存计算结果

```
没有 lru_cache：
  每次 import settings → new Settings() → 重新解析 .env → 浪费！

有了 lru_cache：
  第一次调用 get_settings() → 创建实例 + 缓存
  后续调用 → 直接返回缓存 ✅
```

### 2.4 关键配置项说明表

| 配置项 | 类型 | 默认值 | 说明 | 前端类比 |
|--------|------|--------|------|----------|
| `app_name` | str | "AI Photo Coach API" | 应用名称 | `package.json` 的 name |
| `env` | str | "dev" | 运行环境 | `import.meta.env.MODE` |
| `api_prefix` | str | "/api/v1" | 路由前缀 | Vite 的 baseURL 配置 |
| `db_url` | str | PostgreSQL 连接串 | 数据库地址 | 无直接类比 |
| `redis_url` | str | redis://localhost:6379/0 | 缓存地址 | 无直接类比 |
| `s3_*` | str | MinIO 配置 | 对象存储 | AWS S3 SDK 配置 |
| `cors_origins` | str | 逗号分隔的域名 | CORS 允许源 | vite.config.ts 的 proxy |
| `jwt_secret_key` | str | "change-me-..." | JWT 签名密钥 | 无直接类比 |
| `access_token_expire_minutes` | int | 30 | Access Token 有效期 | — |
| `refresh_token_expire_days` | int | 7 | Refresh Token 有效期 | — |

### 📝 面试常考点

1. **BaseSettings 是怎么加载配置的？** 按优先级合并：环境变量 > .env 文件 > 代码默认值，和 Vite 的 `.env` 机制一模一样。
2. **@lru_cache 的作用是什么？** 缓存函数返回值，实现单例模式。`maxsize=1` 表示只缓存一个结果，下次调用直接返回。
3. **为什么 extra="ignore" 很重要？** 项目中前后端可能共用一个 .env 文件，里面有 `VITE_xxx` 前端变量，没有 `extra="ignore"` Pydantic 会抛出"多余字段"错误。
4. **环境变量名和属性名如何映射？** 默认规则是属性名大写，如 `db_url` 对应环境变量 `DB_URL`。也可以用 `Field(alias="DATABASE_URL")` 自定义映射。

---

## 第3章：数据库与 ORM（SQLAlchemy）

### 3.1 关系型数据库基础概念

如果你只用过 localStorage 和 IndexedDB，可以这样理解：

| 概念 | 数据库世界 | 前端世界 |
|------|-----------|---------|
| 数据库 | PostgreSQL 实例 | 一个 IndexedDB 数据库 |
| 表 (Table) | users、images 等 | IndexedDB 的 Object Store |
| 行 (Row) | 一条用户记录 | 一个 JS 对象 |
| 列 (Column) | email、name 等字段 | 对象的属性 |
| 主键 (PK) | id（唯一标识） | 对象的 keyPath |
| 外键 (FK) | user_id → users.id | 手动维护的对象引用 |
| 索引 (Index) | 加速查询 | IndexedDB 的 index |
| SQL | 查询语言 | IDB 的 getAll/get 等方法 |

最大的区别：**关系型数据库有严格的结构（Schema），IndexedDB 是 Schema-free 的。**

### 3.2 连接池概念与 pool_pre_ping

```python
# apps/api/app/core/database.py

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

# 创建数据库引擎
engine = create_engine(settings.db_url, pool_pre_ping=True)
#                                      👆 这是什么？

# 创建会话工厂
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
```

**连接池**是什么？想象一个餐厅的例子：

```
没有连接池：
  每来一个请求 → 建立新连接 → 查数据 → 关闭连接
  像每次吃饭都重新排队找座位 🐌

有连接池：
  提前准备好 5 个连接 → 请求来了直接用 → 用完还回来
  像餐厅有预约座，来了就坐 ⚡

┌─────────────────────────────────────────┐
│            数据库连接池                    │
├─────────────────────────────────────────┤
│                                         │
│   请求1 ──▶ [连接A] ──▶ 查询 ──▶ 归还    │
│   请求2 ──▶ [连接B] ──▶ 查询 ──▶ 归还    │
│   请求3 ──▶ [连接C] ──▶ 查询 ──▶ 归还    │
│   请求4 ──▶ 等待连接空闲...              │
│                                         │
└─────────────────────────────────────────┘
```

**pool_pre_ping** 的作用：每次从池里拿连接前，先 ping 一下看连接是否还活着。就像你打电话前先拨号看看有没有信号，避免拿了个断线的连接浪费时间去查。

**autoflush=False, autocommit=False** 意味着：
- 不会自动把修改刷到数据库（需要手动 `db.commit()`）
- 不会自动提交事务（需要显式控制）
- 这给开发者完全的事务控制权，避免意外写入脏数据

### 3.3 ORM 映射：Python 类 = 数据库表

ORM（Object-Relational Mapping）的核心思想：**用 Python 类来操作数据库，不用写 SQL**。

```python
# 不用 ORM（写原生 SQL）：
cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
row = cursor.fetchone()

# 用 ORM（写 Python）：
user = db.query(User).filter(User.email == email).first()
#          👆 这是在操作 Python 对象，ORM 会自动翻译成 SQL！
```

类比前端：ORM 就像 Vuex/Pinia，你操作的是 store 里的响应式对象，框架自动帮你同步到"数据源"。

所有模型都继承自同一个基类：

```python
# apps/api/app/models/base.py

from sqlalchemy.orm import declarative_base

Base = declarative_base()
# 这个 Base 就像一个"模型基座"
# 所有模型类继承它，SQLAlchemy 才知道这是一个数据库表模型
```

### 3.4 五个核心模型详解

#### ① User 模型 — 用户表

```python
# apps/api/app/models/user.py

class User(Base):
    __tablename__ = "users"   # 对应数据库的表名

    # 主键：UUID，自动生成
    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # 邮箱：唯一、不能为空
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)

    # 密码哈希：可为空（OAuth 用户没有密码）
    password_hash: Mapped[str | None] = mapped_column(String, nullable=True)

    # 昵称、头像：可选信息
    nickname: Mapped[str | None] = mapped_column(String(50), nullable=True)
    avatar_url: Mapped[str | None] = mapped_column(String, nullable=True)

    # 状态字段
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)    # 是否激活
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False) # 是否验证邮箱

    # 时间戳：created_at 由数据库自动填充
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    # updated_at 每次更新时自动更新
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), onupdate=func.now(), nullable=True
    )
```

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | UUID | PK, 自动生成 | 全局唯一标识 |
| email | String(255) | UNIQUE, NOT NULL | 登录凭证 |
| password_hash | String | NULLABLE | bcrypt 哈希值 |
| nickname | String(50) | NULLABLE | 显示名称 |
| avatar_url | String | NULLABLE | 头像链接 |
| is_active | Boolean | 默认 True | 软删除标记 |
| is_verified | Boolean | 默认 False | 邮箱验证 |
| created_at | DateTime | 服务器默认值 | 创建时间 |
| updated_at | DateTime | onupdate 自动更新 | 修改时间 |

#### ② ImageAsset 模型 — 图片资产表

```python
# apps/api/app/models/image_asset.py

class ImageAsset(Base):
    __tablename__ = "image_assets"
    # 联合唯一约束：同一个 bucket 里不能存两个相同 object_key 的文件
    __table_args__ = (
        UniqueConstraint("bucket", "object_key", name="uq_bucket_object_key"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # 外键：属于哪个用户（CASCADE = 用户删了，图片也删）
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )

    # 自关联外键：编辑后的图片指向原图（SET NULL = 原图删了，parent 变 NULL，但编辑图还在）
    parent_image_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("image_assets.id", ondelete="SET NULL"), nullable=True
    )

    asset_type: Mapped[str] = mapped_column(String(16), nullable=False, default="original")
    storage_provider: Mapped[str] = mapped_column(String(16), nullable=False, default="minio")
    bucket: Mapped[str] = mapped_column(String(128), nullable=False)      # 存储桶名
    object_key: Mapped[str] = mapped_column(Text, nullable=False)         # 文件路径
    mime_type: Mapped[str] = mapped_column(String(64), nullable=False)    # 如 image/jpeg
    size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)    # 文件大小
    width: Mapped[int | None] = mapped_column(Integer, nullable=True)     # 图片宽度
    height: Mapped[int | None] = mapped_column(Integer, nullable=True)    # 图片高度
    sha256: Mapped[str | None] = mapped_column(String(64), nullable=True) # 文件哈希，用于去重
    exif_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)   # EXIF 信息
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
```

关键设计亮点：
- **`ondelete="CASCADE"`**：用户删除 → 所有图片自动删除（像 Vue 组件卸载时清理子组件）
- **`ondelete="SET NULL"`**：原图删除 → 编辑图的 parent_image_id 变 NULL，但编辑图不删除
- **联合唯一约束**：`bucket + object_key` 组合必须唯一，防止重复上传
- **sha256 字段**：文件内容哈希，用于秒传/去重检测

#### ③ AnalysisTask 模型 — 分析任务表

```python
# apps/api/app/models/analysis_task.py

class AnalysisTask(Base):
    __tablename__ = "analysis_tasks"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    image_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("image_assets.id", ondelete="CASCADE"), nullable=False
    )
    task_type: Mapped[str] = mapped_column(String(32), nullable=False, default="ANALYZE")
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="PENDING")
    model_name: Mapped[str] = mapped_column(String(64), nullable=False)
    prompt_version: Mapped[str] = mapped_column(String(32), nullable=False)
    attempt_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)   # 重试次数
    idempotency_key: Mapped[str | None] = mapped_column(String(128), nullable=True)   # 幂等键
    error_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # 复合索引：加速按用户+时间、按状态+时间的查询
    __table_args__ = (
        Index("idx_analysis_tasks_user_created", "user_id", "created_at"),
        Index("idx_analysis_tasks_status_created", "status", "created_at"),
    )
```

这个表就像一个"任务队列的持久化记录"。类比前端：像 Redux/Pinia 里存的异步请求状态（loading / success / error）。

任务状态流转：
```
PENDING ──▶ PROCESSING ──▶ SUCCESS
   │              │
   └──────────────┴──▶ FAILED（可重试，attempt_count++）
```

#### ④ AnalysisResult 模型 — 分析结果表

```python
# apps/api/app/models/analysis_result.py

class AnalysisResult(Base):
    __tablename__ = "analysis_results"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # task_id 是 UNIQUE 的 —— 一个任务只有一个结果
    task_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("analysis_tasks.id", ondelete="CASCADE"),
        nullable=False, unique=True
    )
    image_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("image_assets.id", ondelete="CASCADE"), nullable=False
    )
    version: Mapped[str] = mapped_column(String(16), nullable=False, default="1.1")
    result_json: Mapped[dict] = mapped_column(JSON, nullable=False)  # AI 分析的完整结果
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # 复合索引 + GIN 索引
    __table_args__ = (
        Index("idx_analysis_results_image_created", "image_id", "created_at"),
        Index("idx_analysis_results_result_json_gin", "result_json", postgresql_using="gin"),
    )
```

重点：`task_id` 有 `unique=True`，保证了 **一个任务只能有一个分析结果**（1:1 关系）。

`postgresql_using="gin"` 是 PostgreSQL 特有的 GIN 索引，可以加速 JSON 字段内部查询，比如：
```sql
-- 有了 GIN 索引，这种查询会很快
SELECT * FROM analysis_results WHERE result_json @> '{"score": 85}';
```

类比前端：就像给一个大 JSON 对象建了倒排索引，类似 Elasticsearch 的思路。

#### ⑤ AnalysisFeature 模型 — 分析特征表

```python
# apps/api/app/models/analysis_feature.py

class AnalysisFeature(Base):
    __tablename__ = "analysis_features"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    task_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("analysis_tasks.id", ondelete="CASCADE"),
        nullable=False, unique=True
    )
    image_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("image_assets.id", ondelete="CASCADE"), nullable=False
    )
    version: Mapped[str] = mapped_column(String(16), nullable=False, default="1.0")
    feature_json: Mapped[dict] = mapped_column(JSON, nullable=False)  # 特征数据
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index("idx_analysis_features_image_created", "image_id", "created_at"),
        Index("idx_analysis_features_feature_json_gin", "feature_json", postgresql_using="gin"),
    )
```

AnalysisFeature 和 AnalysisResult 结构类似，但存储的内容不同：
- **AnalysisResult**：AI 分析的最终结论（评分、建议等）
- **AnalysisFeature**：AI 提取的中间特征（面部位置、光线参数等原始数据）

类比前端：Result 是渲染给用户看的 UI 数据，Feature 是背后驱动 UI 的原始计算数据。

#### ⑥ AuthProvider 模型 — 第三方登录绑定表（预留）

```python
# apps/api/app/models/auth_provider.py

class AuthProvider(Base):
    """第三方登录绑定记录 - 预留表，暂不启用"""
    __tablename__ = "auth_providers"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.id"), index=True)
    provider: Mapped[str] = mapped_column(String(20))          # "google", "github", "wechat"
    provider_user_id: Mapped[str] = mapped_column(String)      # 第三方平台的用户 ID
    access_token: Mapped[str | None] = mapped_column(String, nullable=True)  # 第三方 token
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
```

这是为将来接入 Google/GitHub/微信 登录预留的表。一个用户可以绑定多个第三方账号（1:N 关系）。

### 3.5 外键关系与级联删除

```
级联删除策略对比：

┌────────────────────────────────────────────────────────┐
│  ondelete="CASCADE"  — 级联删除                         │
│  用户删除 → 该用户的所有图片、任务 全部自动删除            │
│  类比：Vue 组件卸载时，子组件也跟着卸载                    │
│                                                        │
│  ondelete="SET NULL" — 置空                             │
│  原图删除 → 编辑图的 parent_image_id 变 NULL，编辑图保留  │
│  类比：DOM 节点移除后，ref 引用自动变 null                │
│                                                        │
│  不设 ondelete        — 受限（RESTRICT）                 │
│  有引用时删除父记录 → 数据库报错阻止                      │
│  类比：尝试删除被其他组件依赖的模块，会编译报错             │
└────────────────────────────────────────────────────────┘
```

### 3.6 索引设计与查询优化

为什么需要索引？想象在字典里找字：
- 没有目录（无索引） → 从第一页翻到最后一页，O(n)
- 有目录（有索引） → 先查目录找到页码，O(log n)

我们项目中的索引设计：

| 索引 | 表 | 字段 | 用途 |
|------|-----|------|------|
| idx_analysis_tasks_user_created | analysis_tasks | (user_id, created_at) | 查某用户的任务列表（按时间排序） |
| idx_analysis_tasks_status_created | analysis_tasks | (status, created_at) | 查某状态的任务（如待处理的） |
| idx_analysis_results_image_created | analysis_results | (image_id, created_at) | 查某图片的所有分析结果 |
| idx_analysis_results_result_json_gin | analysis_results | result_json (GIN) | JSON 内部字段查询 |
| idx_analysis_features_feature_json_gin | analysis_features | feature_json (GIN) | JSON 内部字段查询 |
| uq_bucket_object_key | image_assets | (bucket, object_key) | 唯一约束，防重复文件 |

### 3.7 UUID vs 自增 ID 的选择

我们项目全部使用 UUID 作为主键，为什么？

| 对比项 | 自增 ID (1,2,3...) | UUID |
|--------|---------------------|------|
| 可预测性 | ✅ 可预测（爬虫友好） | ❌ 不可预测（安全） |
| 分布式 | ❌ 多库会冲突 | ✅ 全局唯一 |
| 信息泄露 | ⚠️ 看ID就知道用户量 | ✅ 看不出来 |
| 存储 | 4 字节 | 16 字节 |
| 索引性能 | ✅ B+树插入友好 | ⚠️ 随机插入稍慢 |

对于我们这种面向 C 端的应用，UUID 的安全优势更重要。

### 3.8 数据库 ER 关系图

```
┌─────────────────┐       ┌──────────────────────┐       ┌───────────────────┐
│     users       │       │    image_assets       │       │  analysis_tasks   │
├─────────────────┤       ├──────────────────────┤       ├───────────────────┤
│ *id        UUID │◀──┐   │ *id             UUID │◀──┐   │ *id          UUID │
│  email    STR   │   │   │  user_id    UUID(FK) │   │   │  user_id   UUID(FK)│──▶ users
│  password_hash  │   │   │  parent_image_id(FK) │   │   │  image_id  UUID(FK)│──▶ image_assets
│  nickname  STR  │   │   │  asset_type    STR   │   │   │  task_type    STR  │
│  avatar_url STR │   │   │  storage_provider    │   │   │  status       STR  │
│  is_active BOOL │   │   │  bucket         STR  │   │   │  model_name   STR  │
│  is_verified    │   │   │  object_key     TXT  │   │   │  prompt_version    │
│  created_at DT  │   │   │  mime_type      STR  │   │   │  attempt_count INT │
│  updated_at DT  │   │   │  size_bytes    BIG   │   │   │  idempotency_key   │
│                 │   │   │  width         INT   │   │   │  error_code   STR  │
│                 │   │   │  height        INT   │   │   │  error_message TXT │
│                 │   │   │  sha256        STR   │   │   │  created_at   DT   │
│                 │   │   │  exif_json    JSON   │   │   │  started_at   DT   │
│                 │   │   │  created_at    DT    │   │   │  finished_at  DT   │
└─────────────────┘   │   └──────────────────────┘   │   └───────────────────┘
       │              │            │                  │            │
       │              │            │                  │            │
       ▼              │            │                  │            ▼
┌─────────────────┐   │            │                  │   ┌───────────────────┐
│ auth_providers  │   │            │                  │   │ analysis_results  │
├─────────────────┤   │            │                  │   ├───────────────────┤
│ *id        UUID │   │            │                  │   │ *id          UUID │
│  user_id  FK ──┘   │            │                  │   │  task_id  FK(UQ)  │──▶ analysis_tasks
│  provider   STR    │            │                  │   │  image_id     FK  │──▶ image_assets
│  provider_user_id  │            │                  │   │  version      STR │
│  access_token STR  │            │                  │   │  result_json JSON │
│  created_at  DT    │            │                  │   │  created_at   DT  │
└─────────────────┘   │            │                  │   └───────────────────┘
                      │            │                  │
                      │            │                  │   ┌───────────────────┐
                      │            │                  │   │ analysis_features │
                      │            │                  │   ├───────────────────┤
                      └────────────┼──────────────────│   │ *id          UUID │
                      image_assets.id 被              │   │  task_id  FK(UQ)  │──▶ analysis_tasks
                      parent_image_id 自引用          │   │  image_id     FK  │──▶ image_assets
                                                   │   │  version      STR │
                                                   │   │  feature_json JSON │
                                                   │   │  created_at   DT  │
                                                   │   └───────────────────┘

关系总结：
  User 1:N ImageAsset        （一个用户多张图片）
  User 1:N AnalysisTask      （一个用户多个分析任务）
  ImageAsset 1:N AnalysisTask（一张图片可多次分析）
  AnalysisTask 1:1 AnalysisResult   （一个任务一个结果）
  AnalysisTask 1:1 AnalysisFeature  （一个任务一组特征）
  ImageAsset 自引用: parent_image_id → image_assets.id
  User 1:N AuthProvider      （一个用户可绑定多个第三方账号）
```

### 📝 面试常考点

1. **ORM 是什么？有什么优缺点？** 用面向对象的方式操作数据库，优点是开发效率高、不用写 SQL，缺点是复杂查询性能可能不如原生 SQL。
2. **CASCADE 和 SET NULL 的区别？** CASCADE 是父记录删除时子记录也删，SET NULL 是子记录保留但外键置空。
3. **为什么要用连接池？** 避免频繁创建/销毁连接的开销，复用连接提高性能。
4. **UUID 和自增 ID 怎么选？** C 端应用选 UUID（防爬虫、防信息泄露、分布式友好），内部系统可用自增 ID（性能更好）。
5. **GIN 索引是什么？** PostgreSQL 的通用倒排索引，专门用于加速 JSON/数组等复杂类型的查询。

---

## 第4章：认证与安全（JWT + bcrypt）

### 4.1 密码为什么不能存明文

想象一下：如果数据库被黑客拖库了，密码是明文存储的...

```
数据库泄露场景：

  存明文 ❌：
  ┌──────────────────────────────┐
  │ email          │ password     │
  │ zhang@mail.com │ 123456      │  ← 黑客直接看到密码！
  │ li@mail.com    │ myPassword! │  ← 用户在多个网站用同一密码...
  └──────────────────────────────┘
  后果：所有使用相同密码的网站全部沦陷

  存哈希 ✅：
  ┌──────────────────────────────────────────────────────────┐
  │ email          │ password_hash                             │
  │ zhang@mail.com │ $2b$12$R9h/cIPz0gi.URNNX...            │
  │ li@mail.com    │ $2b$12$kHG3q7vJ8fN2pXz1mR...           │
  └──────────────────────────────────────────────────────────┘
  黑客看到哈希也无法还原出原始密码！
```

### 4.2 bcrypt 哈希原理

bcrypt 是专门为密码设计的哈希算法，它有三个特点：

1. **加盐（Salt）**：每次哈希都会随机生成不同的盐值，同样密码的哈希结果不同
2. **慢速**：故意设计得很慢（可调节 cost factor），让暴力破解成本极高
3. **不可逆**：无法从哈希值反推出原始密码

```
bcrypt 哈希结构：
$2b$12$R9h/cIPz0gi.URNNX3h2OeXkPG.Y1m4H9bKDVvQvMqRqF6N3aXmGK
 │  │  │  │
 │  │  │  └── 哈希值（基于密码+盐计算出的结果）
 │  │  └── 盐值（随机生成的22个字符）
 │  └── cost factor（计算轮数 2^12 = 4096 次）
 └── 算法版本

前端类比：
  bcrypt 像是一个"超级慢的 MD5"
  MD5 一秒能算几百万次 → 容易暴力破解
  bcrypt 一秒只能算几千次 → 暴力破解不现实
```

我们的代码实现：

```python
# apps/api/app/core/security.py

from passlib.context import CryptContext

# 创建密码哈希上下文，使用 bcrypt 算法
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    """对明文密码进行 bcrypt 哈希"""
    return pwd_context.hash(password)
    # 输入: "123456"
    # 输出: "$2b$12$R9h/cIPz0gi.URNNX3h2OeXkPG.Y1m4H9bKDVvQvMqRqF6N3aXmGK"

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证明文密码与哈希是否匹配"""
    return pwd_context.verify(plain_password, hashed_password)
    # 输入: ("123456", "$2b$12$R9h/cIP...")
    # 输出: True 或 False
```

### 4.3 JWT 结构解析

JWT（JSON Web Token）是前后端分离项目最常用的认证方案。它就是一个经过签名的字符串，包含三部分：

```
JWT Token 结构：Header.Payload.Signature

eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NTY3OC0xMjM0LTU2NzgtOTAwMC0xMjM0NTY3ODkwMDAiLCJleHAiOjE3MDAwMDAwMDAsInR5cGUiOiJhY2Nlc3MifQ.abc123signature

┌────────────────────────────┬──────────────────────────────────────────────┬──────────────────┐
│        Header              │              Payload                         │   Signature      │
│  {"alg":"HS256","typ":"JWT"}│  {"sub":"user-uuid","exp":1700000000,     │  HMACSHA256(     │
│                            │   "type":"access"}                          │  header.payload,  │
│  Base64 编码               │  Base64 编码                                │  secret_key)     │
│  ❌ 不加密，可解码          │  ❌ 不加密，可解码                           │  ✅ 不可伪造     │
└────────────────────────────┴──────────────────────────────────────────────┴──────────────────┘

注意：Payload 不加密！不要放敏感信息（如密码）！
签名保证了 Token 不能被篡改 —— 改了 Payload，Signature 对不上，验证失败！
```

类比前端：
- JWT 就像一张**演唱会门票**
- Header = 门票的排版格式
- Payload = 你的座位号、演出时间
- Signature = 验票口的防伪钢印（没有密钥造不了假票）

### 4.4 双 Token 设计：access_token + refresh_token

为什么要两个 Token？想想你的手机 App 登录后能保持很久，但网站过一会儿就要重新登录...

```
┌─────────────────────────────────────────────────────────────┐
│                    双 Token 设计                              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  access_token（短期）                                        │
│  ├── 有效期：30 分钟                                         │
│  ├── 用途：每次请求携带，验证身份                              │
│  └── 类比：门禁卡（短期有效，丢了风险小）                       │
│                                                             │
│  refresh_token（长期）                                       │
│  ├── 有效期：7 天                                            │
│  ├── 用途：只在 access_token 过期时使用，换一个新的            │
│  └── 类比：身份证（长期有效，不轻易出示）                       │
│                                                             │
│  为什么不只用一个长期 Token？                                  │
│  如果 Token 被盗：                                           │
│  ├── 长期 Token → 黑客可以一直用，直到你改密码 😱             │
│  └── 短期 Token → 30 分钟后自动失效，损失有限 😌              │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 4.5 Token 生成、验证、过期处理的完整代码流程

```python
# apps/api/app/core/security.py

from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError, ExpiredSignatureError

# ── Token 载荷的数据模型 ──
class TokenPayload(BaseModel):
    sub: str                    # Subject = 用户 ID
    exp: datetime | None = None # 过期时间
    type: str = "access"        # Token 类型：access / refresh

# ── 生成 Access Token ──
def create_access_token(subject: str, expires_delta: timedelta | None = None) -> str:
    """创建 access token，默认 30 分钟过期"""
    if expires_delta is None:
        expires_delta = timedelta(minutes=settings.access_token_expire_minutes)  # 30 分钟
    expire = datetime.now(timezone.utc) + expires_delta
    to_encode = {"sub": subject, "exp": expire, "type": "access"}
    return jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    # 返回类似：eyJhbGciOiJIUzI1NiJ9.eyJzdWIi...

# ── 生成 Refresh Token ──
def create_refresh_token(subject: str) -> str:
    """创建 refresh token，7 天过期"""
    expires_delta = timedelta(days=settings.refresh_token_expire_days)  # 7 天
    expire = datetime.now(timezone.utc) + expires_delta
    to_encode = {"sub": subject, "exp": expire, "type": "refresh"}
    return jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)

# ── 验证 Token ──
def verify_token(token: str) -> TokenPayload:
    """验证并解码 JWT token，失败时抛出 401"""
    try:
        payload = jwt.decode(
            token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm]
        )
        sub: str | None = payload.get("sub")
        if sub is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token payload invalid",
            )
        return TokenPayload(sub=sub, type=payload.get("type", "access"))

    except ExpiredSignatureError:
        # Token 过期了 → 前端需要用 refresh_token 换新的
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired",
        )

    except JWTError:
        # Token 无效（被篡改、格式错误等）
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalid",
        )
```

### 4.6 认证流程时序图

```
┌──────┐                              ┌──────┐                    ┌──────┐
│ 前端 │                              │ 后端 │                    │ 数据库│
└──┬───┘                              └──┬───┘                    └──┬───┘
   │                                     │                           │
   │  1. POST /api/v1/auth/login         │                           │
   │     { email, password }             │                           │
   │ ──────────────────────────────────▶ │                           │
   │                                     │  2. 查询用户              │
   │                                     │ ────────────────────────▶ │
   │                                     │ ◀──── user 记录 ─────────│
   │                                     │                           │
   │                                     │  3. verify_password()     │
   │                                     │     对比明文 vs 哈希       │
   │                                     │                           │
   │                                     │  4. create_access_token() │
   │                                     │     create_refresh_token()│
   │  ◀────────────────────────────────  │                           │
   │  { access_token, refresh_token }    │                           │
   │                                     │                           │
   │  5. 存储到 localStorage             │                           │
   │                                     │                           │
   │  ═══════ 正常请求 ═══════            │                           │
   │                                     │                           │
   │  6. GET /api/v1/users/me            │                           │
   │     Authorization: Bearer <access>  │                           │
   │ ──────────────────────────────────▶ │                           │
   │                                     │  7. verify_token()        │
   │                                     │  8. get_current_user()    │
   │  ◀────────────────────────────────  │                           │
   │  { user data }                      │                           │
   │                                     │                           │
   │  ═══════ Token 过期 ═══════          │                           │
   │                                     │                           │
   │  9. GET /api/v1/users/me            │                           │
   │     Authorization: Bearer <过期token>│                           │
   │ ──────────────────────────────────▶ │                           │
   │                                     │  10. verify_token() 抛出  │
   │                                     │      ExpiredSignatureError│
   │  ◀────────────────────────────────  │                           │
   │  401 { detail: "Token expired" }    │                           │
   │                                     │                           │
   │  11. POST /api/v1/auth/refresh      │                           │
   │      { refresh_token }              │                           │
   │ ──────────────────────────────────▶ │                           │
   │                                     │  12. verify_token()       │
   │                                     │      检查 type="refresh"  │
   │                                     │  13. create_access_token()│
   │  ◀────────────────────────────────  │                           │
   │  { access_token: "新的" }            │                           │
   │                                     │                           │
   │  14. 用新 token 重新发送请求         │                           │
   │ ──────────────────────────────────▶ │                           │
   │                                     │                           │
```

### 4.7 对比前端 localStorage/cookie 存储 token 的实践

| 方案 | 优点 | 缺点 | 本项目选择 |
|------|------|------|-----------|
| localStorage | 简单易用、跨标签页共享 | XSS 攻击可窃取 | ✅ access_token |
| Cookie (HttpOnly) | 防 XSS、自动携带 | CSRF 攻击风险 | refresh_token 备选 |
| sessionStorage | 关标签页就清除 | 不跨标签页 | ❌ 不适合 |
| 内存（JS变量） | 最安全 | 刷新页面就没了 | ❌ 不实用 |

推荐实践（本项目采用）：
- **access_token** 存 localStorage（短期，XSS 风险有限）
- **refresh_token** 存 HttpOnly Cookie（长期，防 XSS 窃取）
- 前端每次请求在 `Authorization: Bearer <token>` 头中携带 access_token

### 📝 面试常考点

1. **JWT 和 Session 的区别？** JWT 是无状态的，服务端不存储会话信息；Session 是有状态的，服务端要存储 session_id。JWT 更适合前后端分离和分布式部署。
2. **bcrypt 和 MD5 的区别？** bcrypt 加盐+慢速，专为密码设计；MD5 无盐+快速，已被证明不安全，不要用来存密码！
3. **为什么需要 refresh_token？** 减少 access_token 被盗的风险。短期 token 自动过期，长期 token 只在刷新时使用，减少暴露。
4. **JWT 的 Payload 能放敏感信息吗？** 不能！Payload 只是 Base64 编码，不是加密，任何人都能解码看到内容。
5. **Token 过期了前端该怎么处理？** 拦截 401 响应 → 用 refresh_token 请求新 access_token → 重试原请求 → 如果 refresh_token 也过期则跳转登录页。

---

## 第5章：依赖注入模式

### 5.1 FastAPI 的 Depends() 机制

如果你用过 Vue 的 `provide/inject` 或 React 的 `Context`，那依赖注入你已经理解了一半：

```
前端（Vue）：
  父组件 provide('db', dbConnection)
  子组件 inject('db')   → 自动拿到 dbConnection

后端（FastAPI）：
  定义 get_db()  → "提供者"（provide）
  路由函数参数 db: Session = Depends(get_db)  → "注入者"（inject）
  FastAPI 自动调用 get_db() 并把结果传给路由函数
```

核心思想：**我不自己创建依赖，我告诉框架"我需要什么"，框架自动给我。**

好处在哪？
1. **解耦**：路由函数不需要知道数据库连接怎么创建的
2. **测试友好**：测试时可以替换成 Mock 的依赖
3. **复用**：同一个依赖可以被多个路由共享

### 5.2 数据库会话注入 get_db() 的 Generator 模式

```python
# apps/api/app/core/database.py

def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()   # 第一步：创建数据库会话
    try:
        yield db          # 第二步：把会话交给路由函数使用
    finally:
        db.close()        # 第三步：请求结束后自动关闭会话
```

这个 Generator 模式的执行流程：

```
┌─────────────────────────────────────────────────────┐
│          get_db() 的生命周期                          │
├─────────────────────────────────────────────────────┤
│                                                     │
│  1. 请求进来                                        │
│     ↓                                               │
│  2. FastAPI 调用 get_db()                           │
│     ↓                                               │
│  3. db = SessionLocal()   ← 创建数据库连接            │
│     ↓                                               │
│  4. yield db              ← 暂停，把 db 传给路由函数   │
│     ↓                                               │
│  5. 路由函数执行（使用 db 查询/修改数据）               │
│     ↓                                               │
│  6. 路由函数返回                                     │
│     ↓                                               │
│  7. 继续执行 finally 块                               │
│     db.close()           ← 自动关闭连接，归还连接池    │
│     ↓                                               │
│  8. 响应返回给客户端                                  │
│                                                     │
└─────────────────────────────────────────────────────┘

类比前端：
  就像 Vue 的 onMounted/onUnmounted 生命周期
  onMounted  → db = SessionLocal()  创建连接
  执行期间   → yield db             使用连接
  onUnmounted → db.close()          清理连接
```

### 5.3 认证守卫 get_current_user() 的链式依赖

这是依赖注入最强大的地方 —— **依赖可以嵌套！**

```python
# apps/api/app/deps.py

"""依赖注入 - JWT Bearer Token 认证"""
import uuid

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import verify_token
from app.models.user import User

# HTTPBearer 会自动从请求头提取 Authorization: Bearer <token>
security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),  # 依赖1：提取 Token
    db: Session = Depends(get_db),                                   # 依赖2：获取数据库连接
) -> User:
    """从 Bearer Token 获取当前用户"""
    # 1. 验证 Token 有效性
    payload = verify_token(credentials.credentials)

    # 2. 从数据库查询用户
    user = db.get(User, uuid.UUID(payload.sub))

    # 3. 检查用户是否存在且激活
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    # 4. 返回 User 对象，后续路由可以直接使用
    return user


def get_current_user_id(
    current_user: User = Depends(get_current_user),  # 依赖3：依赖 get_current_user！
) -> uuid.UUID:
    """获取当前用户 ID（保持向后兼容的接口签名）"""
    return current_user.id
```

链式依赖的调用过程：

```
┌─────────────────────────────────────────────────────────────────┐
│              链式依赖注入调用链                                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  路由函数:                                                       │
│  def my_route(user: User = Depends(get_current_user)):          │
│                                                                 │
│  FastAPI 解析依赖树：                                             │
│                                                                 │
│  my_route                                                       │
│    └── Depends(get_current_user)                                │
│          ├── Depends(security)  ← 从请求头提取 Bearer Token      │
│          │     └── HTTPBearer() 自动解析                         │
│          │         Authorization: Bearer eyJhbGci...             │
│          │                     ↓                                 │
│          │     credentials.credentials = "eyJhbGci..."           │
│          │                                                       │
│          └── Depends(get_db)    ← 获取数据库会话                  │
│                ├── db = SessionLocal()                           │
│                ├── yield db                                      │
│                └── (请求结束后 db.close())                        │
│                                                                 │
│  get_current_user 执行：                                         │
│    1. verify_token(credentials.credentials)  → 解析 Token         │
│    2. db.get(User, uuid.UUID(payload.sub))   → 查询用户           │
│    3. 检查 user.is_active                                         │
│    4. 返回 User 对象                                              │
│                                                                 │
│  最终：my_route 拿到了完整的 User 对象，可以直接用！               │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

更高级的嵌套 —— `get_current_user_id` 依赖 `get_current_user`：

```
get_current_user_id
  └── Depends(get_current_user)
        ├── Depends(security)
        └── Depends(get_db)

三层嵌套！FastAPI 会按顺序从内到外解析：
  security → get_db → get_current_user → get_current_user_id
```

### 5.4 依赖注入的好处：解耦、测试友好

**好处1：解耦**

```python
# ❌ 不用依赖注入（耦合严重）
def my_route():
    db = SessionLocal()       # 路由函数自己创建连接
    token = request.headers.get("Authorization")  # 自己解析请求头
    payload = verify_token(token)  # 自己验证 Token
    user = db.get(User, payload.sub)  # 自己查用户
    # ... 业务逻辑
    db.close()

# ✅ 用依赖注入（清爽！）
def my_route(user: User = Depends(get_current_user)):
    # user 已经准备好了，直接写业务逻辑
    return user
```

**好处2：测试友好**

```python
# 测试时，可以轻松替换依赖
from unittest.mock import MagicMock

def test_my_route():
    mock_user = User(email="test@test.com")
    mock_db = MagicMock()

    # 用 app.dependency_overrides 替换真实依赖
    app.dependency_overrides[get_db] = lambda: mock_db
    app.dependency_overrides[get_current_user] = lambda: mock_user

    # 现在请求不会真正连数据库，而是用 Mock 对象
    response = client.get("/api/v1/users/me")
    assert response.status_code == 200
```

类比前端：
- 就像 Vue Test Utils 里用 `shallowMount` 替换子组件
- 或者用 MSW（Mock Service Worker）拦截 API 请求
- 核心思想都是一样的：**用假的替代真的，专注于测试当前逻辑**

### 📝 面试常考点

1. **什么是依赖注入？** 一种设计模式，由外部提供依赖而不是自己创建，实现解耦。
2. **FastAPI 的 Depends() 和 Vue 的 provide/inject 有什么异同？** 都是依赖注入，但 FastAPI 的 Depends 是声明式的（写在参数里），Vue 的是上下文式的（通过组件树传递）。
3. **Generator 模式在依赖注入中的作用？** 用 yield 实现资源的自动创建和清理，类似 try/finally，保证连接一定被关闭。
4. **链式依赖是什么？** 一个依赖可以依赖另一个依赖，FastAPI 会自动递归解析整个依赖树。
5. **依赖注入为什么有利于测试？** 可以在不修改业务代码的情况下替换成 Mock 对象，隔离外部依赖。

---

## 第6章：API 路由与 Pydantic Schema

### 6.1 路由定义与 HTTP 方法映射

如果你写过 Vue Router，那你已经理解了路由的概念。只不过前端路由管的是"URL → 组件"，后端路由管的是"URL + 方法 → 处理函数"。

```
前端路由（Vue Router）：
  /login    → LoginView.vue     （不管 GET 还是 POST，都渲染同一个组件）
  /history  → HistoryView.vue

后端路由（FastAPI）：
  POST /api/v1/auth/login     → login()     （创建 Session）
  GET  /api/v1/analysis/tasks → get_tasks()  （读取数据）
  同一个 URL，不同 HTTP 方法，对应不同处理函数！
```

HTTP 方法对照表：

| HTTP 方法 | 用途 | 前端类比 | 幂等性 |
|-----------|------|----------|--------|
| GET | 获取资源 | 浏览页面 | ✅ 多次请求结果一样 |
| POST | 创建资源 | 提交表单 | ❌ 每次创建新资源 |
| PUT | 全量更新 | 替换整个表单 | ✅ 多次更新结果一样 |
| PATCH | 部分更新 | 修改单个字段 | ✅ |
| DELETE | 删除资源 | 删除操作 | ✅ |

FastAPI 用装饰器来声明路由，非常直观：

```python
# apps/api/app/modules/auth/router.py

from fastapi import APIRouter

# 创建路由器，prefix 是路由前缀，tags 用于 Swagger 文档分组
router = APIRouter(prefix="/auth", tags=["认证"])

# @router.post 声明这是一个 POST 端点
# "/register" 拼上 prefix，完整路径是 /api/v1/auth/register
@router.post("/register", response_model=TokenResponse)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    """用户注册"""
    ...

@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    """用户登录"""
    ...
```

类比前端：
- `APIRouter` 就像 Vue Router 的 `createRouter()`
- `prefix="/auth"` 就像 Vue Router 的 `base` 配置
- `@router.post("/register")` 就像 Vue Router 的 `{ path: "/register", component: ... }`
- `tags=["认证"]` 就像 Vue Router 的 `meta: { group: "认证" }` 用于导航分组

### 6.2 Pydantic 请求体验证

前端用 Yup/Zod 做表单验证，后端用 Pydantic 做请求体验证。核心思想一模一样：**定义数据结构 + 验证规则，不合法就报错**。

```
前端（Zod）：
  const schema = z.object({
    email: z.string().email(),
    password: z.string().min(8),
  });
  schema.parse(formData);  // 不合法就抛异常

后端（Pydantic）：
  class LoginRequest(BaseModel):
    email: EmailStr              # 必须是合法邮箱
    password: str                # 必须是字符串
  LoginRequest(**request_body)  # 不合法就返回 422
```

来看我们项目的实际 Schema 定义：

```python
# apps/api/app/schemas/auth.py

from pydantic import BaseModel, EmailStr, Field

class RegisterRequest(BaseModel):
    """注册请求体 —— 前端 POST 过来的数据必须长这样"""
    email: EmailStr                          # 必须是合法邮箱格式
    password: str = Field(..., min_length=8) # 密码最少 8 位，... 表示必填
    nickname: str | None = None              # 昵称可选，默认 None

class LoginRequest(BaseModel):
    """登录请求体"""
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    """登录成功后返回的响应体"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"   # 默认值

class RefreshRequest(BaseModel):
    """刷新 Token 请求体"""
    refresh_token: str

class ResetPasswordRequest(BaseModel):
    """重置密码请求体"""
    token: str
    new_password: str = Field(..., min_length=8)  # 新密码也要至少 8 位
```

```python
# apps/api/app/schemas/analysis.py

from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime
from typing import Any

class CreateAnalysisTaskRequest(BaseModel):
    """创建分析任务请求"""
    image_id: UUID   # 必须是合法的 UUID 格式

class CreateAnalysisTaskResponse(BaseModel):
    """创建分析任务响应"""
    task_id: UUID
    task_type: str = "ANALYZE"  # 默认值
    status: str

class AnalysisTaskDetailResponse(BaseModel):
    """分析任务详情响应"""
    task_id: UUID
    image_id: UUID
    task_type: str
    status: str
    model_name: str
    prompt_version: str
    attempt_count: int
    error_code: str | None = None      # 可选字段
    error_message: str | None = None
    created_at: datetime
    started_at: datetime | None = None
    finished_at: datetime | None = None
    result: dict[str, Any] | None = None

class RetryTaskResponse(BaseModel):
    """重试任务响应"""
    task_id: UUID
    task_type: str = Field(default="ANALYZE")
    status: str = Field(default="PENDING")
```

Pydantic 验证失败时，FastAPI 自动返回 422 响应：

```json
// 前端发送 { "email": "not-an-email", "password": "123" }
// 后端返回 422 Unprocessable Entity：
{
  "detail": [
    {
      "type": "value_error",
      "loc": ["body", "email"],
      "msg": "value is not a valid email address",
      "input": "not-an-email"
    },
    {
      "type": "string_too_short",
      "loc": ["body", "password"],
      "msg": "String should have at least 8 characters",
      "input": "123"
    }
  ]
}
```

类比前端：就像 Zod 的 `schema.parse()` 失败时抛出的错误信息，只不过后端自动帮你转成了 HTTP 422 响应。

### 6.3 response_model 自动序列化与 from_attributes

```python
# apps/api/app/schemas/user.py

class UserProfile(BaseModel):
    """用户资料响应"""
    id: uuid.UUID
    email: str
    nickname: str | None = None
    avatar_url: str | None = None
    is_verified: bool = False
    created_at: datetime

    # 关键配置！告诉 Pydantic：可以从 ORM 对象（SQLAlchemy Model）直接读取属性
    model_config = {"from_attributes": True}
```

`from_attributes = True` 是什么意思？

```
没有 from_attributes：
  user = db.query(User).first()  # 返回 SQLAlchemy ORM 对象
  # 不能直接传给 Pydantic！需要手动转字典：
  profile = UserProfile(id=user.id, email=user.email, ...)

有了 from_attributes：
  user = db.query(User).first()
  profile = UserProfile.model_validate(user)  # 直接从 ORM 对象读取属性！
  # 或者配合 response_model，FastAPI 自动完成转换
```

`response_model` 的作用：

```python
@router.get("/me", response_model=UserProfile)
def get_me(user: User = Depends(get_current_user)):
    # 返回的是 SQLAlchemy 的 User ORM 对象
    return user
    # FastAPI 发现 response_model=UserProfile，自动做：
    # 1. 用 UserProfile.model_validate(user) 转换
    # 2. 只输出 UserProfile 定义的字段（password_hash 被过滤掉了！）
    # 3. 自动转成 JSON 返回
```

类比前端：
- `response_model` 就像 TypeScript 的类型守卫，保证返回的数据结构正确
- `from_attributes` 就像 `class-transformer` 的 `@Exclude()` 装饰器，自动从类实例提取数据
- 过滤掉 `password_hash` 是关键安全特性！

### 6.4 文件上传 UploadFile 的处理流程

文件上传和普通 JSON 请求不一样，前端用 `FormData`，后端用 `UploadFile`：

```
前端发送文件：
  const formData = new FormData();
  formData.append('file', selectedFile);
  fetch('/api/v1/images/upload', {
    method: 'POST',
    body: formData,        // 注意：不能手动设 Content-Type，浏览器会自动加 boundary
  });

后端接收文件：
  @router.post("/upload")
  async def upload_image(file: UploadFile = File(...)):
      # FastAPI 自动解析 multipart/form-data
      content = await file.read()  # 读取文件字节
      file.content_type           # 如 image/jpeg
      file.filename               # 原始文件名
```
```

来看完整的图片上传流程代码：

```python
# apps/api/app/modules/images/router.py

@router.post("/upload", response_model=ImageUploadResponse)
async def upload_image(
    file: UploadFile = File(...),        # File(...) 表示必填的文件上传
    db: Session = Depends(get_db),       # 注入数据库会话
    user_id: uuid.UUID = Depends(get_current_user_id),  # 注入当前用户 ID
) -> ImageUploadResponse:
    # 1. 校验文件类型
    if file.content_type is None or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Only image files are supported")

    # 2. 读取文件内容
    content = await file.read()  # 异步读取，注意是 await
    if not content:
        raise HTTPException(status_code=400, detail="Empty file")

    # 3. 用 PIL 验证图片有效性，并获取宽高
    try:
        image = Image.open(BytesIO(content))
        width, height = image.size
    except UnidentifiedImageError as exc:
        raise HTTPException(status_code=400, detail="Invalid image file") from exc

    # 4. 生成唯一的对象存储路径：{user_id}/{日期}/{随机UUID}{扩展名}
    extension = Path(file.filename or "").suffix.lower()
    if not extension:
        extension = ".jpg"
    date_part = datetime.now(timezone.utc).strftime("%Y%m%d")
    object_key = f"{user_id}/{date_part}/{uuid.uuid4().hex}{extension}"

    # 5. 计算文件哈希（用于去重/秒传）
    sha256 = hashlib.sha256(content).hexdigest()

    # 6. 上传到 MinIO 对象存储
    storage = get_storage_service()
    storage.upload_bytes(object_key=object_key, content=content, content_type=file.content_type)

    # 7. 创建数据库记录
    image_asset = ImageAsset(
        user_id=user_id,
        parent_image_id=None,
        asset_type="original",
        storage_provider="minio",
        bucket=storage.bucket,
        object_key=object_key,
        mime_type=file.content_type,
        size_bytes=len(content),
        width=width,
        height=height,
        sha256=sha256,
        exif_json=None,
    )
    db.add(image_asset)
    db.commit()
    db.refresh(image_asset)  # 刷新获取数据库生成的 id

    # 8. 返回上传结果
    return ImageUploadResponse(
        image_id=image_asset.id,
        mime_type=image_asset.mime_type,
        size_bytes=image_asset.size_bytes,
        width=image_asset.width,
        height=image_asset.height,
        object_key=image_asset.object_key,
    )
```

```python
# apps/api/app/schemas/image.py

class ImageUploadResponse(BaseModel):
    """图片上传响应 —— 告诉前端上传成功了"""
    image_id: UUID           # 图片唯一 ID，后续分析时要用
    mime_type: str           # 文件 MIME 类型
    size_bytes: int          # 文件大小
    width: int | None        # 图片宽度
    height: int | None       # 图片高度
    object_key: str          # 存储路径
```

上传流程图：

```
┌──────────┐    FormData     ┌──────────┐    bytes     ┌──────────┐    put_object    ┌──────────┐
│  前端     │ ─────────────▶ │  FastAPI  │ ──────────▶ │  MinIO   │ ◀──────────────  │  后端    │
│  :5151   │  file=blob     │  :8000   │  upload     │  :9000   │  storage.upload  │  代码    │
└──────────┘                └──────────┘              └──────────┘                  └──────────┘
                                 │                                                      │
                                 │  创建 ImageAsset 记录                                  │
                                 │  db.add() → db.commit()                              │
                                 │                                                      │
                                 └──▶ 返回 { image_id, mime_type, size_bytes, ... } ◀─────┘
```

### 6.5 自动生成 OpenAPI 文档（/docs）

FastAPI 最酷的功能之一：**写了路由和 Schema，Swagger 文档就自动生成了！**

```
你只需要写这些代码：
  @router.post("/login", response_model=TokenResponse)
  def login(payload: LoginRequest, ...): ...

FastAPI 自动生成：
  ┌─────────────────────────────────────┐
  │  Swagger UI  (http://localhost:8000/docs)  │
  │                                       │
  │  POST /api/v1/auth/login              │
  │  Request Body:                        │
  │    { "email": "string",              │
  │      "password": "string" }           │
  │  Response 200:                        │
  │    { "access_token": "string",        │
  │      "refresh_token": "string",       │
  │      "token_type": "bearer" }         │
  │                                       │
  │  还有 "Try it out" 按钮，可以直接测试！ │
  └─────────────────────────────────────┘

类比前端：
  类似 Storybook，但 Storybook 要手动写 stories
  FastAPI 的文档是完全自动的，零额外代码！
```

### 6.6 完整的路由端点表格

| 模块 | 方法 | 路径 | 功能 | 认证 |
|------|------|------|------|------|
| auth | POST | /api/v1/auth/register | 用户注册 | ❌ |
| auth | POST | /api/v1/auth/login | 用户登录 | ❌ |
| auth | POST | /api/v1/auth/refresh | 刷新 Token | ❌ |
| auth | POST | /api/v1/auth/logout | 登出 | ❌ |
| auth | POST | /api/v1/auth/verify-email | 邮箱验证 | ❌ |
| auth | POST | /api/v1/auth/forgot-password | 忘记密码 | ❌ |
| auth | POST | /api/v1/auth/reset-password | 重置密码 | ❌ |
| images | POST | /api/v1/images/upload | 上传图片 | ✅ |
| analysis | POST | /api/v1/analysis/tasks | 创建分析任务 | ✅ |
| analysis | GET | /api/v1/analysis/tasks/{task_id} | 获取任务详情 | ✅ |
| analysis | GET | /api/v1/analysis/history | 分析历史列表 | ✅ |
| analysis | POST | /api/v1/analysis/tasks/{task_id}/retry | 重试失败任务 | ✅ |

### 📝 面试常考点

1. **GET 和 POST 的区别？** GET 幂等且可缓存，参数在 URL；POST 非幂等，参数在请求体。敏感数据必须用 POST。
2. **Pydantic 的 Field(...) 中 ... 是什么意思？** 表示必填字段，没有默认值。等价于 TypeScript 的非可选属性。
3. **from_attributes 有什么用？** 让 Pydantic 可以直接从 ORM 对象（如 SQLAlchemy Model）读取属性，省去手动转字典的步骤。
4. **文件上传为什么用 multipart/form-data？** 因为 JSON 只能传文本，二进制文件需要用 multipart 编码，每个字段有独立的 Content-Type。
5. **422 和 400 的区别？** 400 是请求语法错误，422 是语法正确但语义不对（如邮箱格式错误）。Pydantic 验证失败返回 422。
6. **response_model 怎么保证安全性？** 只输出 Schema 中定义的字段，自动过滤掉敏感字段如 password_hash。

---

## 第7章：异步任务处理（Celery + Redis）

### 7.1 为什么需要异步任务

想象你在前端遇到过这样的场景：点击"导出报告"按钮后，页面卡住了 30 秒... 这就是因为导出操作在主线程执行，阻塞了 UI 渲染。

后端也一样：AI 分析一张照片可能需要 5-30 秒，如果让用户等 30 秒才返回响应，体验极差！

```
同步处理（❌ 体验差）：
  用户上传图片 → 请求后端 → 后端执行 AI 分析（30秒）→ 返回结果
  用户在等 30 秒期间：页面转圈圈、无法操作、可能超时

异步处理（✅ 体验好）：
  用户上传图片 → 请求后端 → 后端立即返回 task_id
  用户可以继续浏览，前端定时查询任务状态
  AI 分析完成后 → 前端拿到结果并展示
```

前端类比：
- 同步 = `setTimeout(() => {}, 0)` 阻塞主线程（其实并不会阻塞，但概念类似）
- 异步 = `Web Worker` 在后台线程处理，主线程不受影响
- 或者类比 `Promise`：发出去不用等，等好了回调通知我

### 7.2 消息队列概念：生产者/消费者模式

Celery 的核心是**消息队列**，它遵循经典的"生产者/消费者"模式：

```
┌──────────────────────────────────────────────────────────────────┐
│                消息队列：生产者/消费者模式                         │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────┐     发送任务      ┌──────────┐     取出任务    ┌──────────┐ │
│  │ 生产者    │ ──────────────▶  │  Redis    │ ─────────────▶ │ 消费者    │ │
│  │ (API)    │   "分析图片123"   │  (队列)   │               │ (Worker)  │ │
│  └──────────┘                   └──────────┘               └──────────┘ │
│                                                                  │
│  前端类比：就像 EventBus                                        │
│  $emit('analyze', taskId)  →  EventBus  →  $on('analyze', handler)│
│  生产者发布事件            →  事件总线   →  消费者处理事件           │
│                                                                  │
│  为什么不直接在 API 里执行？                                      │
│  1. API 进程只负责接收请求，不负责耗时计算                         │
│  2. Worker 可以独立扩展（加机器就行）                              │
│  3. Worker 挂了不影响 API，任务还在队列里等着                      │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

关键组件：

| 组件 | 角色 | 前端类比 |
|------|------|----------|
| Producer（生产者） | API 路由，发送任务到队列 | `eventBus.$emit()` |
| Broker（消息代理） | Redis，存储任务消息 | EventBus 事件总线 |
| Worker（消费者） | Celery 进程，执行任务 | `eventBus.$on()` 回调 |
| Backend（结果存储） | Redis，存储任务结果 | 组件的 data 状态 |

### 7.3 Celery 配置详解

```python
# apps/api/app/core/celery_app.py

from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "ai_photo_coach",           # 应用名称，用于标识
    broker=settings.redis_url,  # 消息代理：任务从哪里取
    backend=settings.redis_url, # 结果存储：任务结果存哪里
    include=["app.tasks.analyze_photo"],  # 告诉 Celery 去哪里找任务函数
)

celery_app.conf.update(
    task_track_started=True,    # 追踪任务是否已开始（状态：STARTED）
    timezone="Asia/Shanghai",   # 时区
    enable_utc=False,           # 不用 UTC 时间
    task_routes={
        # 路由配置：不同任务发到不同队列
        # 就像前端不同类型的事件发到不同的 channel
        "app.tasks.analyze_photo.run_analysis_task": {
            "queue": "analysis"  # 分析任务走 analysis 队列
        },
    },
)
```

配置解读：

- **broker**：Redis 充当消息队列，API 把"请分析图片"的消息发到 Redis，Worker 从 Redis 取消息执行
- **backend**：也是 Redis，Worker 执行完把结果存到 Redis，API 可以查询
- **task_routes**：队列路由，就像快递分拣中心 —— 不同类型的任务走不同的通道，互不干扰
- **task_track_started**：开启后任务会有 STARTED 状态，否则从 PENDING 直接到 SUCCESS/FAILURE

### 7.4 run_analysis_task 完整任务流程代码与注释

这是整个异步分析的核心代码，建议逐行阅读：

```python
# apps/api/app/tasks/analyze_photo.py

import uuid
from datetime import datetime, timezone
from sqlalchemy import select

from app.core.celery_app import celery_app      # Celery 实例
from app.core.database import SessionLocal       # 注意：不是 get_db()！
from app.models.analysis_feature import AnalysisFeature
from app.models.analysis_result import AnalysisResult
from app.models.analysis_task import AnalysisTask
from app.models.image_asset import ImageAsset
from app.services.composer.result_composer import get_result_composer
from app.services.cv.feature_extractor import get_feature_extractor
from app.services.llm.analyzer import get_llm_analyzer
from app.services.rules.edit_planner import get_edit_planner
from app.services.storage.s3_storage import get_storage_service


@celery_app.task(name="app.tasks.analyze_photo.run_analysis_task")
def run_analysis_task(task_id: str) -> None:
    """Celery 任务函数 —— 在 Worker 进程中异步执行"""

    # ⚠️ 注意：Celery Worker 里不能用 Depends(get_db)，因为没有 HTTP 请求上下文
    # 必须手动创建数据库会话
    db = SessionLocal()
    task_uuid = uuid.UUID(task_id)

    try:
        # ── 第1步：更新任务状态为 RUNNING ──
        task = db.get(AnalysisTask, task_uuid)
        if task is None:
            return  # 任务不存在，直接返回

        task.status = "RUNNING"               # 状态：PENDING → RUNNING
        task.started_at = datetime.now(timezone.utc)  # 记录开始时间
        task.attempt_count += 1               # 重试次数 +1
        db.commit()

        # ── 第2步：下载原始图片 ──
        image = db.get(ImageAsset, task.image_id)
        if image is None:
            raise ValueError("Image not found")

        storage = get_storage_service()
        image_bytes = storage.download_bytes(image.object_key)  # 从 MinIO 下载

        # ── 第3步：四段式管道处理 ──
        feature_extractor = get_feature_extractor()
        llm_analyzer = get_llm_analyzer()
        edit_planner = get_edit_planner()
        result_composer = get_result_composer()

        # 3a. CV 特征提取
        feature_json = feature_extractor.extract(
            image_bytes=image_bytes, mime_type=image.mime_type
        )

        # 3b. 保存特征数据（支持重试时更新）
        existing_feature = db.execute(
            select(AnalysisFeature).where(AnalysisFeature.task_id == task.id)
        ).scalar_one_or_none()
        if existing_feature:
            existing_feature.feature_json = feature_json
            existing_feature.version = feature_json.get("version", "1.0")
            db.flush()
            feature_id = existing_feature.id
        else:
            feature = AnalysisFeature(
                task_id=task.id, image_id=task.image_id,
                version=feature_json.get("version", "1.0"),
                feature_json=feature_json,
            )
            db.add(feature)
            db.flush()
            feature_id = feature.id

        # 3c. LLM 分析评分
        llm_result = llm_analyzer.analyze(features=feature_json)

        # 3d. 规则引擎生成编辑建议
        edit_actions = edit_planner.plan(
            features=feature_json, suggestions=llm_result["suggestions"]
        )

        # 3e. 组装最终结果
        result_json = result_composer.compose(
            feature_id=str(feature_id), features=feature_json,
            llm_result=llm_result, edit_actions=edit_actions,
        )

        # ── 第4步：保存分析结果 ──
        existing_result = db.execute(
            select(AnalysisResult).where(AnalysisResult.task_id == task.id)
        ).scalar_one_or_none()
        if existing_result:
            existing_result.result_json = result_json
            existing_result.version = result_json.get("version", "1.1")
        else:
            db.add(AnalysisResult(
                task_id=task.id, image_id=task.image_id,
                version=result_json.get("version", "1.1"),
                result_json=result_json,
            ))

        # ── 第5步：标记任务成功 ──
        task.status = "SUCCEEDED"
        task.error_code = None
        task.error_message = None
        task.finished_at = datetime.now(timezone.utc)
        db.commit()

    except Exception as exc:
        # ── 异常处理：标记任务失败 ──
        db.rollback()  # 回滚未提交的修改
        failed_task = db.get(AnalysisTask, task_uuid)
        if failed_task:
            failed_task.status = "FAILED"
            failed_task.error_code = exc.__class__.__name__     # 如 "ValueError"
            failed_task.error_message = str(exc)[:500]           # 截断，避免太长
            failed_task.finished_at = datetime.now(timezone.utc)
            db.commit()
    finally:
        db.close()  # 一定要手动关闭！没有 Depends(get_db) 自动帮你关了
```

关键点解读：

1. **Worker 里必须用 `SessionLocal()` 而不是 `Depends(get_db)`**：因为 Celery Worker 没有 HTTP 请求上下文，依赖注入不工作
2. **`@celery_app.task` 装饰器**：把普通函数注册为 Celery 任务
3. **重试时更新而非重复创建**：检查 `existing_feature` / `existing_result`，有则更新，无则新建
4. **异常处理写 error_code + error_message**：方便前端展示错误信息和排查问题

### 7.5 任务状态流转

```
┌──────────────────────────────────────────────────────────────────┐
│                    任务状态流转图                                  │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  用户点击"分析"                                                   │
│       │                                                          │
│       ▼                                                          │
│  ┌─────────┐     Worker 取到任务     ┌─────────┐                │
│  │ PENDING │ ──────────────────────▶ │ RUNNING │                │
│  └─────────┘                         └─────────┘                │
│       │                                  │                      │
│       │                              ┌───┴───┐                   │
│       │                              │       │                   │
│       │                              ▼       ▼                   │
│       │                     ┌──────────┐ ┌────────┐             │
│       │                     │SUCCEEDED │ │ FAILED │             │
│       │                     └──────────┘ └────────┘             │
│       │                                      │                   │
│       │                                      │ 用户点击"重试"    │
│       │                                      ▼                   │
│       │                              ┌─────────┐                │
│       └────────────────────────────▶ │ PENDING │ (attempt_count+1)│
│                                      └─────────┘                │
│                                                                  │
│  对应 API：                                                       │
│  POST /api/v1/analysis/tasks      → 创建任务（PENDING）          │
│  GET  /api/v1/analysis/tasks/:id  → 查询任务状态                  │
│  POST /api/v1/analysis/tasks/:id/retry → 重试失败任务             │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

### 7.6 错误处理与重试机制

路由层的重试逻辑：

```python
# apps/api/app/modules/analysis/router.py

@router.post("/tasks/{task_id}/retry", response_model=RetryTaskResponse)
def retry_task(
    task_id: uuid.UUID,
    db: Session = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> RetryTaskResponse:
    task = db.get(AnalysisTask, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    if task.user_id != user_id:
        raise HTTPException(status_code=403, detail="No permission for this task")
    # 只有 FAILED 或 SUCCEEDED 的任务才能重试
    if task.status not in {"FAILED", "SUCCEEDED"}:
        raise HTTPException(status_code=400, detail="Task is still running")

    # 重置任务状态
    task.status = "PENDING"
    task.error_code = None
    task.error_message = None
    task.started_at = None
    task.finished_at = None
    db.commit()

    # 重新投递到 Celery 队列
    run_analysis_task.delay(str(task.id))
    return RetryTaskResponse(task_id=task.id, task_type=task.task_type, status=task.status)
```

### 7.7 前端轮询策略配合

后端只提供查询接口，轮询逻辑在前端实现：

```javascript
// 前端伪代码：轮询任务状态
async function pollTaskStatus(taskId) {
  const interval = setInterval(async () => {
    const res = await fetch(`/api/v1/analysis/tasks/${taskId}`);
    const data = await res.json();

    if (data.status === 'SUCCEEDED') {
      clearInterval(interval);
      // 展示分析结果
      showAnalysisResult(data.result);
    } else if (data.status === 'FAILED') {
      clearInterval(interval);
      // 展示错误信息，提供重试按钮
      showError(data.error_message);
    }
    // 否则继续轮询（PENDING / RUNNING）
  }, 2000); // 每 2 秒查询一次
}
```

类比前端：
- 就像 `setInterval` 轮询 WebSocket 状态
- 或者类似 `useQuery` 的 `refetchInterval` 配置
- 更好的方案是用 WebSocket 实时推送，但轮询实现更简单

### 7.8 任务执行流程图

```
┌───────┐                         ┌───────┐                    ┌───────┐                    ┌───────┐
│ 前端  │                         │  API  │                    │ Redis │                    │Worker │
└──┬────┘                         └──┬────┘                    └──┬────┘                    └──┬────┘
   │                                 │                            │                            │
   │ POST /analysis/tasks            │                            │                            │
   │ { image_id }                    │                            │                            │
   │───────────────────────────────▶ │                            │                            │
   │                                 │ 创建 AnalysisTask(PENDING) │                            │
   │                                 │──────────────────────────▶ │                            │
   │                                 │ run_analysis_task.delay()  │                            │
   │                                 │                            │                            │
   │ { task_id, status: PENDING }    │                            │                            │
   │◀─────────────────────────────── │                            │                            │
   │                                 │                            │  Worker 取出任务            │
   │                                 │                            │◀───────────────────────────│
   │                                 │                            │                            │
   │   GET /analysis/tasks/:id       │                            │                            │
   │───────────────────────────────▶ │                            │                            │
   │   { status: RUNNING }           │                            │  Worker 执行分析中...       │
   │◀─────────────────────────────── │                            │                            │
   │                                 │                            │                            │
   │   GET /analysis/tasks/:id       │                            │                            │
   │───────────────────────────────▶ │                            │                            │
   │   { status: SUCCEEDED, result } │                            │   分析完成，存结果           │
   │◀─────────────────────────────── │                            │◀───────────────────────────│
   │                                 │                            │                            │
```

### 📝 面试常考点

1. **为什么需要 Celery 而不是直接在 API 里执行？** 耗时任务会阻塞 API 进程，导致其他请求超时。异步任务让 API 快速响应，后台慢慢处理。
2. **Broker 和 Backend 的区别？** Broker 是消息队列，存放待执行的任务；Backend 存放任务执行结果。本项目都用 Redis。
3. **Celery Worker 里为什么不能用 Depends(get_db)？** 依赖注入依赖 HTTP 请求上下文，Worker 没有 HTTP 上下文，必须手动创建和关闭数据库会话。
4. **任务状态有哪些？** PENDING（待处理）→ RUNNING（执行中）→ SUCCEEDED（成功）/ FAILED（失败）。失败可重试回到 PENDING。
5. **前端怎么配合异步任务？** 创建任务后拿到 task_id，用 setInterval 轮询任务状态，完成或失败后停止轮询。

---

## 第8章：服务层四段式管道设计

### 8.1 分层架构思想

我们的后端遵循经典的**三层架构**，和前端的分层思路一一对应：

```
后端分层：                              前端分层：

Router（路由层）                        View（视图层）
  ├── 接收请求、参数校验                    ├── 渲染 UI、用户交互
  ├── 调用 Service                        ├── 调用 Store 方法
  └── 返回响应                             └── 展示数据

Service（服务层）                       Store（状态管理层）
  ├── 业务逻辑处理                         ├── 数据处理与状态管理
  ├── 调用 Infrastructure                  ├── 调用 API 请求
  └── 组装结果                              └── 更新状态

Infrastructure（基础设施层）            API（接口层）
  ├── 数据库操作（SQLAlchemy）              ├── HTTP 请求（axios/fetch）
  ├── 对象存储（MinIO/S3）                  ├── WebSocket 连接
  └── 外部服务（AI模型）                     └── 第三方 SDK
```

核心原则：**每一层只和相邻层交互，不跨层调用。**

### 8.2 CV 层详解：CVFeatureExtractor

CV 层负责**计算机视觉特征提取**，使用 Python 的 Pillow（PIL）库处理图像：

```python
# apps/api/app/services/cv/feature_extractor.py

from PIL import Image, ImageStat
from io import BytesIO
from typing import Any

class CVFeatureExtractor:
    version = "1.0"

    def extract(self, image_bytes: bytes, mime_type: str) -> dict[str, Any]:
        """从图片字节中提取视觉特征"""

        # 1. 加载图片并转 RGB 模式
        image = Image.open(BytesIO(image_bytes)).convert("RGB")
        width, height = image.size

        # 2. 计算亮度和对比度（转灰度图统计）
        gray = image.convert("L")            # 转为灰度图（单通道）
        stats = ImageStat.Stat(gray)        # 统计像素分布
        mean_brightness = round(float(stats.mean[0]), 2)   # 平均亮度
        contrast = round(float(stats.stddev[0]), 2)         # 标准差 = 对比度

        # 3. 估算主体区域（基于经验规则的简单检测）
        subject_w = round(width * 0.52)       # 主体宽度约占图片 52%
        subject_h = round(height * 0.62)      # 主体高度约占图片 62%
        subject_x = round((width - subject_w) * 0.28)   # 主体左偏
        subject_y = round((height - subject_h) * 0.22)  # 主体上偏

        # 4. 计算构图平衡度（主体中心 x 坐标 / 图片宽度）
        subject_center_x = subject_x + subject_w / 2
        composition_balance = round(subject_center_x / max(width, 1), 3)
        # 0.5 = 完美居中，<0.42 = 偏左，>0.58 = 偏右

        # 5. 检测高光和阴影区域
        highlight_strength = _clamp((mean_brightness - 175) / 80, 0, 1)
        shadow_strength = _clamp((85 - mean_brightness) / 80, 0, 1)

        # 高光区域（右上角偏亮）
        highlight_region = None
        if highlight_strength > 0.12:
            highlight_region = {
                "x": round(width * 0.62), "y": round(height * 0.14),
                "w": round(width * 0.22), "h": round(height * 0.18),
                "coord_space": "image_pixels",
            }

        # 阴影区域（左下角偏暗）
        shadow_region = None
        if shadow_strength > 0.12:
            shadow_region = {
                "x": round(width * 0.12), "y": round(height * 0.58),
                "w": round(width * 0.24), "h": round(height * 0.22),
                "coord_space": "image_pixels",
            }

        # 6. 参考线（地平线）
        horizon_line = {
            "x1": 0, "y1": round(height * 0.52),
            "x2": width, "y2": round(height * 0.5),
            "coord_space": "image_pixels",
        }

        return {
            "version": self.version,
            "image": { "width": width, "height": height, "mime_type": mime_type },
            "stats": {
                "mean_brightness": mean_brightness,
                "contrast": contrast,
                "composition_balance": composition_balance,
            },
            "subject": {
                "x": subject_x, "y": subject_y,
                "w": subject_w, "h": subject_h,
                "coord_space": "image_pixels",
            },
            "regions": { "highlight": highlight_region, "shadow": shadow_region },
            "guidelines": { "horizon": horizon_line },
        }
```

CV 层输出示例：

```json
{
  "version": "1.0",
  "image": { "width": 2400, "height": 1600, "mime_type": "image/jpeg" },
  "stats": { "mean_brightness": 132.5, "contrast": 58.3, "composition_balance": 0.456 },
  "subject": { "x": 290, "y": 218, "w": 1248, "h": 992, "coord_space": "image_pixels" },
  "regions": {
    "highlight": { "x": 1488, "y": 224, "w": 528, "h": 288, "coord_space": "image_pixels" },
    "shadow": null
  },
  "guidelines": { "horizon": { "x1": 0, "y1": 832, "x2": 2400, "y2": 800, "coord_space": "image_pixels" } }
}
```

### 8.3 LLM 层详解：LLMAnalyzer

LLM 层负责**分析评分和建议生成**，目前使用规则引擎模拟（未来可接入真实大模型）：

```python
# apps/api/app/services/llm/analyzer.py

class LLMAnalyzer:
    version = "1.0"

    def analyze(self, features: dict[str, Any]) -> dict[str, Any]:
        """根据 CV 特征生成评分和建议"""
        image = features["image"]
        subject = features["subject"]
        stats = features["stats"]

        # 1. 计算主体重心位置
        width = image["width"]
        subject_center_x = subject["x"] + subject["w"] / 2
        balance = subject_center_x / max(width, 1)  # 0~1，0.5 = 居中

        # 2. 生成摘要文本
        summary_parts = ["主体可读性还可以"]
        if balance < 0.42:
            summary_parts.append("但画面重心偏左")
        elif balance > 0.58:
            summary_parts.append("但画面重心偏右")
        else:
            summary_parts.append("画面重心基本稳定")

        if stats["mean_brightness"] < 96:
            summary_parts.append("整体曝光偏暗")
        elif stats["mean_brightness"] > 182:
            summary_parts.append("高光略抢眼")
        else:
            summary_parts.append("曝光处于可优化区间")

        # 3. 生成建议列表（按类型分：构图/曝光/叙事）
        suggestions: list[dict[str, Any]] = []

        # 构图建议
        if balance < 0.42:
            suggestions.append({
                "id": "s1", "type": "composition", "priority": "high",
                "problem": "主体重心偏左，右侧留白较多。",
                "action": "裁掉右侧约 10% 到 18% 的空间，让主体更靠近右侧三分线。",
                "text": "主体重心偏左，建议裁掉右侧约 10% 到 18% 的空间...",
            })
        elif balance > 0.58:
            suggestions.append({
                "id": "s1", "type": "composition", "priority": "high",
                "problem": "主体重心偏右，左侧留白承担了过多视觉重量。",
                "action": "裁掉左侧约 10% 的空白，并保留主体前方空间。",
                "text": "主体重心偏右，建议裁掉左侧约 10% 的空白...",
            })
        else:
            suggestions.append({
                "id": "s1", "type": "composition", "priority": "medium",
                "problem": "主体位置基本合理，但视觉焦点还不够集中。",
                "action": "可轻微收紧画面边缘，减少无效背景。",
                "text": "主体位置基本合理，可轻微收紧画面边缘...",
            })

        # 曝光建议（略，逻辑类似）
        # ...

        # 叙事建议（始终给出，优先级最低）
        suggestions.append({
            "id": "s3", "type": "story", "priority": "low",
            "problem": "当前叙事焦点主要依赖主体位置，背景参与度不强。",
            "action": "在保留主体周围留白的前提下，适当清理分散注意力的边缘区域。",
            "text": "当前叙事焦点主要依赖主体位置，建议清理分散注意力的边缘区域。",
        })

        # 4. 计算四维评分
        return {
            "version": self.version,
            "summary": "，".join(summary_parts) + "。",
            "suggestions": suggestions,
            "scores": self._build_scores(stats, balance),
        }

    @staticmethod
    def _build_scores(stats: dict[str, Any], balance: float) -> dict[str, int]:
        """四维评分算法：构图/曝光/色彩/叙事，各 0~100 分"""
        # 构图分：越接近 0.5（居中）分越高
        composition = max(55, min(90, round(88 - abs(0.5 - balance) * 85)))
        # 曝光分：亮度越接近 135（中间值）分越高
        exposure = max(50, min(90, round(90 - abs(135 - stats["mean_brightness"]) * 0.32)))
        # 色彩分：对比度适中的得分更高
        color = max(58, min(84, round(68 + min(stats["contrast"], 40) * 0.25)))
        # 叙事分：综合构图和曝光
        story = max(55, min(82, round((composition + exposure) / 2 - 8)))

        return {
            "composition": composition,
            "exposure": exposure,
            "color": color,
            "story": story,
        }
```

LLM 层输出示例：

```json
{
  "version": "1.0",
  "summary": "主体可读性还可以，但画面重心偏左，曝光处于可优化区间。",
  "suggestions": [
    { "id": "s1", "type": "composition", "priority": "high", "text": "...", "problem": "...", "action": "..." },
    { "id": "s2", "type": "exposure", "priority": "medium", "text": "...", "problem": "...", "action": "..." },
    { "id": "s3", "type": "story", "priority": "low", "text": "...", "problem": "...", "action": "..." }
  ],
  "scores": { "composition": 72, "exposure": 78, "color": 70, "story": 63 }
}
```

### 8.4 Rules 层详解：EditPlanner

Rules 层负责**根据建议生成具体的编辑动作参数**，把"建议"翻译成"操作"：

```python
# apps/api/app/services/rules/edit_planner.py

class EditPlanner:
    def plan(self, features: dict, suggestions: list[dict]) -> list[dict]:
        """根据特征和建议生成编辑动作列表"""
        image = features["image"]
        subject = features["subject"]
        stats = features["stats"]

        actions: list[dict] = []

        # 1. 裁剪动作：根据主体重心偏移自动裁剪
        crop = self._plan_crop(image=image, subject=subject)
        if crop is not None:
            actions.append(crop)

        # 2. 曝光动作：根据亮度调整曝光参数
        exposure_action = self._plan_exposure(stats["mean_brightness"])
        if exposure_action is not None:
            actions.append(exposure_action)

        # 3. 白平衡动作：始终给一个轻量自动白平衡选项
        if suggestions:
            actions.append({
                "id": "e3",
                "action_type": "white_balance",
                "source": "rule",
                "params": { "mode": "gray_world", "strength": 0.18 },
                "reason": "为后续调色预留一个稳定、轻量的自动白平衡选项。",
                "previewable": True,
                "apply_mode": "non_destructive",
            })

        return actions

    @staticmethod
    def _plan_crop(image: dict, subject: dict) -> dict | None:
        """计算裁剪参数：把主体重心往三分线靠拢"""
        width = image["width"]
        height = image["height"]
        subject_center_x = subject["x"] + subject["w"] / 2
        ratio = subject_center_x / max(width, 1)

        # 主体在中间区域就不裁剪
        if 0.42 <= ratio <= 0.58:
            return None

        # 裁掉约 14% 的边缘
        crop_width = round(width * 0.86)
        crop_height = round(height * 0.86)
        # 根据偏移方向，决定裁剪起点
        target_center_x = crop_width * (2/3 if ratio < 0.5 else 1/3)
        crop_x = round(max(0, min(width - crop_width, subject_center_x - target_center_x)))
        crop_y = round((height - crop_height) / 2)

        return {
            "id": "e1",
            "action_type": "crop",
            "source": "rule",
            "params": { "x": crop_x, "y": crop_y, "w": crop_width, "h": crop_height, "ratio": "free" },
            "reason": "根据主体重心偏移自动收紧边缘空间，让主体更靠近三分线。",
            "previewable": True,
            "apply_mode": "destructive",  # 裁剪是破坏性操作
        }

    @staticmethod
    def _plan_exposure(mean_brightness: float) -> dict | None:
        """计算曝光调整参数：alpha（对比度乘数）+ beta（亮度偏移）"""
        if mean_brightness < 96:
            return {
                "id": "e2", "action_type": "exposure", "source": "rule",
                "params": { "alpha": 1.08, "beta": 18 },   # 稍微提亮
                "reason": "整体亮度偏低，自动提升曝光与中低频亮度。",
                "previewable": True,
                "apply_mode": "non_destructive",
            }
        if mean_brightness > 182:
            return {
                "id": "e2", "action_type": "exposure", "source": "rule",
                "params": { "alpha": 0.94, "beta": -14 },  # 稍微压暗
                "reason": "高光较强，自动回收亮度峰值并压低整体曝光。",
                "previewable": True,
                "apply_mode": "non_destructive",
            }
        return None  # 亮度正常，不需要调整
```

Rules 层输出示例：

```json
[
  { "id": "e1", "action_type": "crop", "params": { "x": 100, "y": 112, "w": 2064, "h": 1376, "ratio": "free" }, "apply_mode": "destructive" },
  { "id": "e2", "action_type": "exposure", "params": { "alpha": 1.08, "beta": 18 }, "apply_mode": "non_destructive" },
  { "id": "e3", "action_type": "white_balance", "params": { "mode": "gray_world", "strength": 0.18 }, "apply_mode": "non_destructive" }
]
```

### 8.5 Composer 层详解：ResultComposer

Composer 层负责**组装最终结果**，把前几层的输出合并成前端需要的完整数据结构：

```python
# apps/api/app/services/composer/result_composer.py

class ResultComposer:
    version = "1.1"

    def compose(self, feature_id: str, features: dict, llm_result: dict,
                edit_actions: list[dict]) -> dict[str, Any]:
        """组装最终分析结果"""
        return {
            "version": self.version,
            "summary": llm_result["summary"],         # 摘要（来自 LLM 层）
            "suggestions": llm_result["suggestions"],   # 建议列表（来自 LLM 层）
            "scores": llm_result.get("scores"),         # 评分（来自 LLM 层）
            "features_ref": { "feature_id": feature_id }, # 引用特征数据
            "annotations": self._build_annotations(features),  # 标注数据（来自 CV 层）
            "edit_actions": edit_actions,                # 编辑动作（来自 Rules 层）
        }

    @staticmethod
    def _build_annotations(features: dict) -> list[dict]:
        """根据 CV 特征生成前端可视化标注"""
        annotations = []

        # 主体标注（bbox 矩形框）
        subject = features.get("subject")
        if subject:
            annotations.append({
                "id": "a1", "source": "cv", "category": "composition",
                "geometry_type": "bbox",   # 矩形框类型
                "coords": subject,           # 坐标数据
                "label": "subject",
                "message": "主体检测区域，可用于构图分析与自动裁剪。",
                "confidence": 0.86,
                "related_suggestion_ids": ["s1"],  # 关联的建议 ID
            })

        # 高光标注
        highlight = features.get("regions", {}).get("highlight")
        if highlight:
            annotations.append({
                "id": "a2", "source": "cv", "category": "exposure",
                "geometry_type": "bbox", "coords": highlight,
                "label": "highlight",
                "message": "高光区域较亮，后续可联动曝光调整。",
                "confidence": 0.73,
                "related_suggestion_ids": ["s2"],
            })

        # 阴影标注
        shadow = features.get("regions", {}).get("shadow")
        if shadow:
            annotations.append({
                "id": "a3", "source": "cv", "category": "exposure",
                "geometry_type": "bbox", "coords": shadow,
                "label": "shadow",
                "message": "暗部区域较重，后续可联动阴影或曝光调整。",
                "confidence": 0.72,
                "related_suggestion_ids": ["s2"],
            })

        # 地平线标注（line 类型）
        horizon = features.get("guidelines", {}).get("horizon")
        if horizon:
            annotations.append({
                "id": "a4", "source": "cv", "category": "guideline",
                "geometry_type": "line",   # 线段类型
                "coords": horizon,
                "label": "horizon",
                "message": "参考地平线，用于后续构图和校正能力。",
                "confidence": 0.64,
                "related_suggestion_ids": [],
            })

        return annotations
```

### 8.6 对象存储 MinIO/S3：S3StorageService

图片不存数据库，而是存到对象存储（MinIO 兼容 S3 协议）：

```python
# apps/api/app/services/storage/s3_storage.py

import boto3
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError
from fastapi import HTTPException
from app.core.config import settings

class S3StorageService:
    def __init__(self) -> None:
        # 创建 S3 客户端，连接 MinIO
        self.client = boto3.client(
            "s3",
            endpoint_url=settings.s3_endpoint,      # MinIO 地址
            aws_access_key_id=settings.s3_access_key,
            aws_secret_access_key=settings.s3_secret_key,
            region_name=settings.s3_region,
            config=Config(
                connect_timeout=3,      # 连接超时 3 秒
                read_timeout=8,         # 读取超时 8 秒
                retries={"max_attempts": 1},  # 最多重试 1 次
            ),
        )
        self.bucket = settings.s3_bucket

    def ensure_bucket(self) -> None:
        """确保存储桶存在，不存在就创建"""
        try:
            self.client.head_bucket(Bucket=self.bucket)  # 检查桶是否存在
        except ClientError:
            self.client.create_bucket(Bucket=self.bucket)  # 不存在则创建

    def upload_bytes(self, object_key: str, content: bytes, content_type: str) -> None:
        """上传文件到 MinIO"""
        self.client.put_object(
            Bucket=self.bucket,
            Key=object_key,         # 如 "user-uuid/20260528/abc123.jpg"
            Body=content,           # 文件二进制内容
            ContentType=content_type,
        )

    def download_bytes(self, object_key: str) -> bytes:
        """从 MinIO 下载文件"""
        response = self.client.get_object(Bucket=self.bucket, Key=object_key)
        return response["Body"].read()  # 读取全部字节
```

类比前端：
- MinIO 就像 AWS S3，是"云存储"的本地版
- `upload_bytes` 就像前端用 `axios.put()` 上传文件
- `download_bytes` 就像前端用 `axios.get()` 下载文件
- 数据库存的是文件路径（object_key），不是文件本身

### 8.7 门面模式 AnalyzerFacade

四段管道被封装在一个**门面（Facade）** 中，对外只暴露一个 `analyze()` 方法：

```python
# apps/api/app/services/ai/analyzer.py

class AnalyzerFacade:
    def analyze(self, image_bytes: bytes, mime_type: str) -> dict[str, Any]:
        """一键分析：CV → LLM → Rules → Composer"""
        # 第1段：CV 特征提取
        features = get_feature_extractor().extract(image_bytes=image_bytes, mime_type=mime_type)
        # 第2段：LLM 分析评分
        llm_result = get_llm_analyzer().analyze(features=features)
        # 第3段：规则引擎生成编辑建议
        edit_actions = get_edit_planner().plan(features=features, suggestions=llm_result["suggestions"])
        # 第4段：组装最终结果
        return get_result_composer().compose(
            feature_id="inline", features=features,
            llm_result=llm_result, edit_actions=edit_actions,
        )
```

门面模式的好处：
- **简化调用**：调用方只需一行 `analyzer.analyze(bytes, mime_type)`
- **解耦**：调用方不需要知道内部的四段管道细节
- **灵活替换**：未来换 AI 模型，只需改 Facade 内部实现

类比前端：就像一个 **Composable**（`useAnalysis()`），内部可能调了多个 API，但对外只暴露一个 `analyze()` 方法。

### 8.8 四段管道流程图

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    四段式分析管道                                        │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  图片字节流                                                              │
│      │                                                                  │
│      ▼                                                                  │
│  ┌──────────────────┐                                                  │
│  │  ① CV 特征提取    │  Pillow (PIL) 图像处理                          │
│  │  CVFeatureExtractor│  → 亮度、对比度、主体区域、高光/阴影           │
│  └────────┬─────────┘                                                  │
│           │ features dict                                               │
│           ▼                                                             │
│  ┌──────────────────┐                                                  │
│  │  ② LLM 分析评分   │  规则引擎（未来可换 GPT-4V）                     │
│  │  LLMAnalyzer     │  → 评分、建议、摘要                               │
│  └────────┬─────────┘                                                  │
│           │ llm_result dict                                             │
│           │                                                             │
│           ├──────────────────────────────────┐                         │
│           │ features + suggestions           │                         │
│           ▼                                  ▼                         │
│  ┌──────────────────┐              ┌──────────────────┐                │
│  │  ③ 规则引擎       │              │  ④ 结果组装       │                │
│  │  EditPlanner     │─────────────▶│  ResultComposer   │                │
│  │  → 裁剪/曝光/白平衡│  edit_actions │  → 标注+结果合并  │                │
│  └──────────────────┘              └────────┬─────────┘                │
│                                              │                         │
│                                              ▼                         │
│                                    最终 analysis_result JSON             │
│                                    { summary, suggestions, scores,       │
│                                      annotations, edit_actions }         │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 8.9 各层输入输出 JSON 示例

```json
// CV 层输出 → LLM 层输入
{
  "version": "1.0",
  "image": { "width": 2400, "height": 1600, "mime_type": "image/jpeg" },
  "stats": { "mean_brightness": 132.5, "contrast": 58.3, "composition_balance": 0.456 },
  "subject": { "x": 290, "y": 218, "w": 1248, "h": 992, "coord_space": "image_pixels" },
  "regions": { "highlight": null, "shadow": null },
  "guidelines": { "horizon": { "x1": 0, "y1": 832, "x2": 2400, "y2": 800, "coord_space": "image_pixels" } }
}

// LLM 层输出 → Rules 层输入（suggestions 部分）
{
  "version": "1.0",
  "summary": "主体可读性还可以，但画面重心偏左，曝光处于可优化区间。",
  "suggestions": [
    { "id": "s1", "type": "composition", "priority": "high", "problem": "...", "action": "...", "text": "..." },
    { "id": "s2", "type": "exposure", "priority": "medium", "problem": "...", "action": "...", "text": "..." },
    { "id": "s3", "type": "story", "priority": "low", "problem": "...", "action": "...", "text": "..." }
  ],
  "scores": { "composition": 72, "exposure": 78, "color": 70, "story": 63 }
}

// 最终输出（Composer 组装后）
{
  "version": "1.1",
  "summary": "主体可读性还可以，但画面重心偏左，曝光处于可优化区间。",
  "suggestions": [ ... ],
  "scores": { "composition": 72, "exposure": 78, "color": 70, "story": 63 },
  "features_ref": { "feature_id": "inline" },
  "annotations": [
    { "id": "a1", "source": "cv", "category": "composition", "geometry_type": "bbox", "coords": {...}, "label": "subject", "confidence": 0.86 },
    { "id": "a4", "source": "cv", "category": "guideline", "geometry_type": "line", "coords": {...}, "label": "horizon", "confidence": 0.64 }
  ],
  "edit_actions": [
    { "id": "e1", "action_type": "crop", "params": {"x":100,"y":112,"w":2064,"h":1376}, "apply_mode": "destructive" },
    { "id": "e3", "action_type": "white_balance", "params": {"mode":"gray_world","strength":0.18}, "apply_mode": "non_destructive" }
  ]
}
```

### 📝 面试常考点

1. **什么是门面模式？** 为复杂子系统提供统一的高层接口，简化调用方使用。AnalyzerFacade 就是典型例子。
2. **为什么图片不存数据库而存对象存储？** 数据库存二进制大文件会严重影响性能，对象存储（MinIO/S3）专为文件设计，数据库只存路径引用。
3. **四段管道的数据流向是怎样的？** 图片字节 → CV特征 → LLM评分建议 → Rules编辑动作 → Composer组装结果，单向流动，每层只依赖上一层的输出。
4. **destructive 和 non_destructive 的区别？** destructive（破坏性）操作如裁剪会改变图片尺寸，不可逆；non_destructive（非破坏性）如曝光调整可随时撤销。
5. **置信度（confidence）字段的作用？** 标注的置信度表示 CV 检测的可靠程度，前端可以据此决定是否显示该标注。

---

## 第9章：Docker 容器化与部署

### 9.1 Docker 基础概念

如果你熟悉前端工程化，理解 Docker 其实不难：

```
前端类比：

  npm install = 安装依赖          →  Docker 镜像构建（COPY + RUN pip install）
  npm start   = 启动开发服务器    →  Docker 容器运行（CMD uvicorn）
  node_modules/ = 依赖包          →  镜像里的 /app 目录
  package.json = 依赖声明         →  requirements.txt

核心区别：
  npm install 在你的电脑上装依赖   → 你电脑是 Mac，装的就是 Mac 版
  Docker 镜像在虚拟 Linux 里装依赖  → 不管宿主机是什么，环境永远一致！
```

| 概念 | 说明 | 前端类比 |
|------|------|----------|
| 镜像 (Image) | 只读模板，包含代码+依赖+环境 | `node_modules/` + 编译后的 `dist/` |
| 容器 (Container) | 镜像的运行实例 | `npm start` 运行中的应用 |
| Dockerfile | 构建镜像的脚本 | `package.json` + 构建脚本 |
| docker-compose | 编排多个容器 | 前端 monorepo 的 turbo.json |
| 数据卷 (Volume) | 持久化存储 | localStorage（容器删了数据还在） |

### 9.2 Dockerfile 三要素

每个 Dockerfile 都包含三个核心部分：

```
1. 基础镜像（FROM）   → "从哪个操作系统开始"
2. 构建步骤（RUN/COPY）→ "安装依赖、复制代码"
3. 启动命令（CMD）    → "容器启动后执行什么"
```

### 9.3 API Dockerfile 逐行解析

```dockerfile
# apps/api/Dockerfile

# 1. 基础镜像：Python 3.12 精简版
# ARG 允许在构建时传参，如 --build-arg PYTHON_IMAGE=python:3.11-slim
ARG PYTHON_IMAGE=python:3.12-slim
FROM ${PYTHON_IMAGE}

# 2. 工作目录
WORKDIR /app

# 3. Python 环境优化
ENV PYTHONDONTWRITEBYTECODE=1  # 不生成 .pyc 缓存文件，减小镜像体积
ENV PYTHONUNBUFFERED=1          # 不缓冲输出，日志实时打印

# 4. 安全：创建非 root 用户
# ⚠️ 容器默认以 root 运行，被攻破后可以访问宿主机！
# 用非 root 用户运行是安全最佳实践
RUN addgroup --system app && adduser --system --ingroup app app

# 5. 安装 Python 依赖（利用 Docker 缓存层）
# 先只复制 requirements.txt，安装依赖
# 这样代码变了不用重装依赖，构建速度快很多！
COPY apps/api/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir --default-timeout=120 --retries 10 \
    -i https://mirrors.cloud.tencent.com/pypi/simple/ \
    --trusted-host mirrors.cloud.tencent.com \
    -r /tmp/requirements.txt
#  👆 使用腾讯云镜像加速，因为默认的 PyPI 在国内很慢

# 6. 复制应用代码
COPY apps/api /app

# 7. 将文件所有权交给 app 用户
RUN chown -R app:app /app

# 8. 切换到非 root 用户
USER app

# 9. 声明端口
EXPOSE 8000

# 10. 启动命令
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Docker 缓存层优化：

```
❌ 不好（每次改代码都重装依赖）：
  COPY apps/api /app
  RUN pip install -r requirements.txt
  # 改了一行代码 → 全部重新构建 → pip install 又跑 5 分钟

✅ 好的（先装依赖，再复制代码）：
  COPY apps/api/requirements.txt /tmp/requirements.txt  # 依赖声明单独复制
  RUN pip install -r /tmp/requirements.txt               # 安装依赖（缓存层）
  COPY apps/api /app                                      # 最后复制代码
  # 改代码 → 只重新执行 COPY 和之后的步骤，依赖安装用缓存！

类比前端：
  就像 CI 里先 cache node_modules，再 npm install，最后 npm run build
  如果 lock 文件没变，直接用缓存的 node_modules
```

### 9.4 Web Dockerfile 多阶段构建

前端项目的 Dockerfile 有个特点：**构建阶段需要 Node.js，但运行只需要 Nginx**。

```dockerfile
# apps/web/Dockerfile

# ===== 第一阶段：构建（需要 Node.js）=====
FROM node:22-alpine AS build
#                    👆 AS build 给阶段命名

WORKDIR /app

# 先复制 package.json，利用缓存层
COPY apps/web/package.json ./
RUN npm install

# 复制源代码
COPY apps/web ./

# 构建参数：Vite 构建时注入的 API 地址
ARG VITE_API_BASE_URL=/api/v1
ENV VITE_API_BASE_URL=${VITE_API_BASE_URL}
# Vite 在 npm run build 时读取这个环境变量
# 类比前端：import.meta.env.VITE_API_BASE_URL

# 执行构建，生成 dist/ 目录
RUN npm run build

# ===== 第二阶段：运行（只需要 Nginx）=====
FROM nginx:1.27-alpine
# 👆 全新的基础镜像，不含 Node.js！镜像从 ~800MB → ~30MB

# 复制 Nginx 配置
COPY infra/nginx/default.conf /etc/nginx/conf.d/default.conf

# 从第一阶段复制构建产物
COPY --from=build /app/dist /usr/share/nginx/html
#           👆 引用第一阶段的名字

EXPOSE 80

# 健康检查：每 30 秒访问一次首页，3 次失败标记为不健康
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
  CMD wget -qO- http://localhost/ >/dev/null || exit 1
```

多阶段构建的好处：

```
没有多阶段构建：
  最终镜像包含 Node.js + npm + 源码 + dist → 约 1.2GB！
  里面有你不需要的 node_modules、TypeScript 源码...

有多阶段构建：
  第一阶段（build）：Node.js + npm install + npm run build → 生成 dist/
  第二阶段（运行）：只包含 Nginx + dist/ → 约 30MB！

类比前端：
  就像 npm run build 后只部署 dist/，不部署 node_modules/ 和 src/
```

### 9.5 Worker Dockerfile

Worker 复用了 API 的代码和依赖，只是启动命令不同：

```dockerfile
# apps/worker/Dockerfile

ARG PYTHON_IMAGE=python:3.12-slim
FROM ${PYTHON_IMAGE}

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN addgroup --system app && adduser --system --ingroup app app

# ⚠️ 注意：复制的是 API 的 requirements.txt！
COPY apps/api/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# ⚠️ 复制的也是 API 的代码！Worker 和 API 共用同一套代码
COPY apps/api /app
RUN chown -R app:app /app

USER app

# 唯一区别：启动命令不同
# API 用 uvicorn 启动 Web 服务
# Worker 用 celery 启动异步任务消费者
CMD ["celery", "-A", "app.core.celery_app.celery_app", "worker", "--loglevel=info", "-Q", "analysis"]
#           👆 Celery 应用路径                    👆 只监听 analysis 队列
```

### 9.6 docker-compose.yml 开发环境编排

Docker Compose 的作用是**一键启动多个容器**，并管理它们之间的关系：

```yaml
# infra/docker-compose.yml

services:
  # ── 数据库：PostgreSQL ──
  postgres:
    image: postgres:16               # 直接用官方镜像
    container_name: photo-coach-postgres
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres    # 开发环境用简单密码
      POSTGRES_DB: photo_coach
    ports:
      - "5432:5432"                 # 暴露端口，本地可用 psql 连接
    volumes:
      - pg_data:/var/lib/postgresql/data  # 数据持久化
    healthcheck:                     # 健康检查
      test: ["CMD-SHELL", "pg_isready -U postgres -d photo_coach"]
      interval: 10s
      timeout: 5s
      retries: 5

  # ── 缓存/消息队列：Redis ──
  redis:
    image: redis:7
    container_name: photo-coach-redis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]  # Redis 的健康检查就是 ping

  # ── 对象存储：MinIO ──
  minio:
    image: minio/minio:latest
    container_name: photo-coach-minio
    command: server /data --console-address ":9001"  # 启动命令
    environment:
      MINIO_ROOT_USER: minioadmin
      MINIO_ROOT_PASSWORD: minioadmin
    ports:
      - "9000:9000"   # API 端口
      - "9001:9001"   # 管理控制台端口
    volumes:
      - minio_data:/data
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:9000/minio/health/live"]

  # ── API 服务 ──
  api:
    build:
      context: ..                        # 构建上下文：项目根目录
      dockerfile: apps/api/Dockerfile    # Dockerfile 路径
      args:
        PYTHON_IMAGE: python:3.12-slim   # 构建参数
    container_name: photo-coach-api
    environment:
      DB_URL: postgresql+psycopg://postgres:postgres@postgres:5432/photo_coach
      #                                                       👆 用服务名 postgres 而非 localhost！
      REDIS_URL: redis://redis:6379/0
      #                       👆 同样用服务名
      S3_ENDPOINT: http://minio:9000
      #                      👆 同样用服务名
    ports:
      - "8000:8000"
    depends_on:                       # 依赖关系
      postgres:
        condition: service_healthy    # 等 postgres 健康检查通过才启动
      redis:
        condition: service_healthy
      minio:
        condition: service_healthy

  # ── Worker 服务 ──
  worker:
    build:
      context: ..
      dockerfile: apps/worker/Dockerfile
    container_name: photo-coach-worker
    environment:
      # 和 API 一样的环境变量（同一个数据库、同一个 Redis）
      DB_URL: postgresql+psycopg://postgres:postgres@postgres:5432/photo_coach
      REDIS_URL: redis://redis:6379/0
      S3_ENDPOINT: http://minio:9000
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
      minio:
        condition: service_healthy

# 数据卷：容器删除后数据仍然保留
volumes:
  pg_data:
  redis_data:
  minio_data:
```

关键概念：

- **服务名即主机名**：`postgres:5432` 而不是 `localhost:5432`，Docker 内部 DNS 自动解析
- **depends_on + condition**：确保依赖服务先启动且健康
- **volumes**：数据持久化，容器删除重建不丢数据
- **ports**：开发环境暴露端口方便调试，生产环境不暴露

### 9.7 docker-compose.prod.yml 生产环境差异

```yaml
# infra/docker-compose.prod.yml（只列差异部分）

services:
  # ✅ 生产多了 Web 服务（Nginx + 前端）
  web:
    build:
      context: ..
      dockerfile: apps/web/Dockerfile
      args:
        VITE_API_BASE_URL: /api/v1  # 前端 API 地址用相对路径
    container_name: photo-coach-web
    ports:
      - "80:80"                     # 生产只暴露 80 端口
    depends_on:
      api:
        condition: service_healthy
    restart: unless-stopped          # ✅ 生产环境：挂了自动重启

  # ✅ 密码用环境变量，不硬编码
  postgres:
    environment:
      POSTGRES_USER: ${POSTGRES_USER}           # 从 .env.prod 读取
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}     # 不再是硬编码的 "postgres"
      POSTGRES_DB: ${POSTGRES_DB}
    restart: unless-stopped
    # ❌ 没有 ports！数据库不对外暴露，只有内部网络可访问

  redis:
    restart: unless-stopped
    # ❌ 没有 ports！Redis 也不对外暴露

  minio:
    environment:
      MINIO_ROOT_USER: ${S3_ACCESS_KEY}         # 密码从环境变量读取
      MINIO_ROOT_PASSWORD: ${S3_SECRET_KEY}
    restart: unless-stopped
    # ❌ 没有 ports！MinIO 也不对外暴露

  api:
    environment:
      # 数据库连接串用环境变量拼接
      DB_URL: postgresql+psycopg://${POSTGRES_USER}:${POSTGRES_PASSWORD}@postgres:5432/${POSTGRES_DB}
      S3_ACCESS_KEY: ${S3_ACCESS_KEY}
      S3_SECRET_KEY: ${S3_SECRET_KEY}
      CORS_ORIGINS: http://${SERVER_IP}          # ✅ 只允许生产域名
    healthcheck:                     # ✅ API 自己也有健康检查了
      test: ["CMD", "python", "-c",
        "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/healthz')"]
      interval: 15s
      timeout: 5s
      retries: 5
    restart: unless-stopped

  worker:
    restart: unless-stopped
```

### 9.8 Nginx 反向代理配置详解

```nginx
# infra/nginx/default.conf

server {
    listen 80;                # 监听 80 端口
    server_name _;            # 接受任何域名

    root /usr/share/nginx/html;  # 前端静态文件目录
    index index.html;

    # API 请求转发到后端
    location /api/ {
        proxy_pass http://api:8000/api/;  # 转发到 API 容器
        #             👆 api 是 Docker 服务名，自动解析为 API 容器的 IP
        proxy_http_version 1.1;

        # 透传真实客户端信息（否则后端只能看到 Nginx 的 IP）
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # 健康检查也转发
    location = /healthz {
        proxy_pass http://api:8000/healthz;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # 前端 SPA 路由：所有未匹配的请求返回 index.html
    location / {
        try_files $uri $uri/ /index.html;
        # 👆 关键！没有这行，Vue Router 的 history 模式刷新会 404
        #
        # 原理：
        #   用户访问 /history → Nginx 先找 /history 文件 → 没有
        #                    → 再找 /history/ 目录 → 没有
        #                    → 返回 /index.html → Vue Router 接管路由
    }
}
```

类比前端：
- Nginx 就像 Vite 的开发服务器 + proxy 配置
- `proxy_pass` 就像 `vite.config.ts` 里的 `proxy: { '/api': 'http://localhost:8000' }`
- `try_files` 解决了 Vue Router history 模式的刷新 404 问题

### 9.9 deploy.sh 部署脚本流程

```bash
# infra/deploy.sh

#!/usr/bin/env bash
set -eu   # -e: 任何命令失败立即退出  -u: 使用未定义变量报错

# 1. 定位项目路径
SCRIPT_DIR="$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd)"
REPO_ROOT="$(CDPATH='' cd -- "${SCRIPT_DIR}/.." && pwd)"
ENV_FILE="${REPO_ROOT}/infra/.env.prod"           # 生产环境变量文件
COMPOSE_FILE="${REPO_ROOT}/infra/docker-compose.prod.yml"

# 2. 检查环境变量文件是否存在
if [ ! -f "$ENV_FILE" ]; then
    echo "Missing env file: $ENV_FILE" >&2
    echo "Create it from infra/.env.prod.example before deploying." >&2
    exit 1
fi

# 3. 检查 docker compose 是否可用
require_command docker
if ! docker compose version >/dev/null 2>&1; then
    echo "docker compose is not available" >&2
    exit 1
fi

# 4. 检查必需的环境变量是否都已配置
required_vars='SERVER_IP POSTGRES_USER POSTGRES_PASSWORD POSTGRES_DB S3_ACCESS_KEY S3_SECRET_KEY S3_BUCKET'
for key in $required_vars; do
    if ! grep -Eq "^${key}=.+" "$ENV_FILE"; then
        echo "Missing required setting: $key" >&2
        exit 1
    fi
done

# 5. 构建并启动所有服务
cd "$REPO_ROOT"
docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" up --build -d
#                                                                    👆 -d 后台运行

# 6. 打印服务状态和常用命令
docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" ps
echo "Expected URLs:"
echo "  http://${server_ip}"
echo "  http://${server_ip}/healthz"
```

部署前需要准备 `.env.prod` 文件：

```bash
# infra/.env.prod.example

SERVER_IP=YOUR_SERVER_IP            # 服务器公网 IP

POSTGRES_USER=postgres
POSTGRES_PASSWORD=change-this-db-password   # ⚠️ 必须改！
POSTGRES_DB=photo_coach

S3_ACCESS_KEY=minioadmin
S3_SECRET_KEY=change-this-minio-password    # ⚠️ 必须改！
S3_BUCKET=photo-images
S3_REGION=us-east-1

MODEL_NAME=mock-vision-v1
PROMPT_VERSION=v1
```

### 9.10 开发 vs 生产环境对比表

| 对比项 | 开发环境 | 生产环境 |
|--------|----------|----------|
| 前端 | `npm run dev` (localhost:5151) | Nginx 容器 (端口 80) |
| 后端 | API 容器 (端口 8000 暴露) | API 容器 (端口 8000 不暴露) |
| 数据库 | 端口 5432 暴露 | 端口不暴露 |
| Redis | 端口 6379 暴露 | 端口不暴露 |
| MinIO | 端口 9000/9001 暴露 | 端口不暴露 |
| 密码 | 硬编码（postgres/minioadmin） | 环境变量（${POSTGRES_PASSWORD}） |
| 重启策略 | 无（挂了就挂了） | unless-stopped（自动重启） |
| 健康检查 | 基础设施有，API 无 | API 也有健康检查 |
| API 地址 | 前端直连 localhost:8000 | 通过 Nginx 代理 /api/ |
| Docker Compose 文件 | docker-compose.yml | docker-compose.prod.yml |

### 9.11 生产架构图

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          生产环境架构                                    │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│                     互联网用户                                          │
│                         │                                               │
│                         ▼                                               │
│              ┌─────────────────────┐                                    │
│              │   Nginx (Web 容器)   │ ← 唯一对外暴露的端口 :80          │
│              │   ┌───────────────┐ │                                    │
│              │   │ /api/* → API  │ │ ← 反向代理                        │
│              │   │ /healthz→API  │ │                                    │
│              │   │ /* → Vue SPA  │ │ ← 前端静态文件                     │
│              │   └───────────────┘ │                                    │
│              └─────────┬───────────┘                                    │
│                        │                                                │
│              ┌─────────┴───────────┐                                    │
│              │    API 容器 :8000    │ ← 只在 Docker 内网可访问          │
│              │   FastAPI + Uvicorn  │                                    │
│              └──┬──────┬──────┬────┘                                    │
│                 │      │      │                                         │
│     ┌───────────┘      │      └───────────┐                             │
│     ▼                  ▼                  ▼                             │
│ ┌────────┐      ┌──────────┐      ┌──────────┐                        │
│ │Postgres│      │  Redis   │      │  MinIO   │                        │
│ │ :5432  │      │  :6379   │      │  :9000   │                        │
│ │(不暴露) │      │ (不暴露)  │      │ (不暴露)  │                        │
│ └────────┘      └────┬─────┘      └──────────┘                        │
│                       │                                                │
│              ┌────────┴──────────┐                                     │
│              │  Worker 容器       │ ← Celery 消费者                    │
│              │  监听 analysis 队列│                                     │
│              └───────────────────┘                                     │
│                                                                         │
│  ┌──────────────────────────────────────────┐                          │
│  │ Docker 内部网络                            │                          │
│  │ 服务名即主机名：api、postgres、redis、minio  │                          │
│  │ 容器间用服务名通信，外部只能访问 Nginx :80   │                          │
│  └──────────────────────────────────────────┘                          │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 📝 面试常考点

1. **Docker 镜像和容器的区别？** 镜像是只读模板（类似 class），容器是运行实例（类似 object）。一个镜像可以启动多个容器。
2. **为什么 Dockerfile 先 COPY requirements.txt 再 COPY 代码？** 利用 Docker 缓存层机制，依赖不变时不用重装，大幅加速构建。
3. **多阶段构建的好处？** 最终镜像不包含构建工具（Node.js），体积从 GB 级降到 MB 级，更安全更快速。
4. **docker-compose 的 depends_on 能保证服务就绪吗？** 不能，depends_on 只保证启动顺序。要加 `condition: service_healthy` 才等健康检查通过。
5. **Nginx 的 try_files 解决什么问题？** 解决 SPA 前端路由 history 模式刷新 404 的问题，把未匹配的请求回退到 index.html。
6. **生产环境为什么不暴露数据库/Redis 端口？** 减少攻击面，只有 Nginx 对外暴露，内部服务通过 Docker 网络通信。

---

## 第10章：数据契约（JSON Schema）

### 10.1 前后端数据契约的意义

你是否遇到过这种场景：后端改了一个字段名，前端没同步更新，结果线上白屏了？

**数据契约**就是解决这个问题的。它是一份前后端共同遵守的"合同"，定义了数据的结构和约束。

```
没有数据契约：
  后端返回 { composition: 72 }  → 前端用 data.compostion  → undefined！
  （拼错了一个字母，但 TypeScript 编译时不报错，运行时才崩）

有数据契约：
  后端按 schema 返回 → CI 用 schema 验证返回值 → 拼写错误在 CI 阶段就被发现
  前端按 schema 生成 TypeScript 类型 → 拼写错误在编译阶段就被发现

前端类比：
  数据契约 ≈ TypeScript interface
  但比 interface 更强大：
  - interface 只在编译时检查
  - JSON Schema 还能在运行时验证数据
  - JSON Schema 是语言无关的，Python/JS/Java 都能用
```

| 对比项 | TypeScript interface | JSON Schema |
|--------|---------------------|-------------|
| 语言 | TypeScript only | 语言无关 |
| 检查时机 | 编译时 | 编译时 + 运行时 |
| 验证能力 | 类型检查 | 类型 + 范围 + 格式 + 必填 |
| 前后端共享 | ❌ 后端用不了 | ✅ 两边都能用 |
| 自动生成代码 | ❌ | ✅ 可自动生成 TS interface |

### 10.2 analysis-result.schema.json 完整结构解析

这是最重要的契约，定义了 AI 分析结果的完整数据结构：

```json
// packages/contracts/analysis-result.schema.json

{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://ai-photo-coach/contracts/analysis-result.schema.json",
  "title": "AnalysisResult",
  "type": "object",

  // 必填字段：少了任何一个，验证失败
  "required": ["version", "summary", "suggestions", "scores", "annotations", "edit_actions"],

  "properties": {
    // 版本号
    "version": { "type": "string" },

    // 摘要文本（不能为空字符串）
    "summary": { "type": "string", "minLength": 1 },

    // 建议列表
    "suggestions": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["id", "type", "text", "priority"],
        "properties": {
          "id": { "type": "string" },
          "type": {
            "type": "string",
            "enum": ["composition", "exposure", "color", "story", "other"]
            // 👆 枚举约束：只能是这5种之一
          },
          "text": { "type": "string" },
          "problem": { "type": "string" },
          "action": { "type": "string" },
          "priority": {
            "type": "string",
            "enum": ["high", "medium", "low"]
          }
        },
        "additionalProperties": false  // 不允许额外字段，防止拼写错误
      }
    },

    // 四维评分
    "scores": {
      "type": ["object", "null"],  // 允许为 null（某些情况可能没评分）
      "properties": {
        "composition": { "type": "number", "minimum": 0, "maximum": 100 },
        "exposure":    { "type": "number", "minimum": 0, "maximum": 100 },
        "color":       { "type": "number", "minimum": 0, "maximum": 100 },
        "story":       { "type": "number", "minimum": 0, "maximum": 100 }
        // 👆 每个分数必须是 0~100 的数字
      },
      "additionalProperties": true  // 允许扩展新维度
    },

    // 特征数据引用
    "features_ref": {
      "type": ["object", "null"],
      "properties": {
        "feature_id": { "type": "string" }
      },
      "additionalProperties": false
    },

    // 标注列表（引用另一个 schema）
    "annotations": {
      "type": "array",
      "items": {
        "$ref": "annotation.schema.json"  // 👆 引用标注 schema
      }
    },

    // 编辑动作列表（引用另一个 schema）
    "edit_actions": {
      "type": "array",
      "items": {
        "$ref": "edit-action.schema.json"  // 👆 引用编辑动作 schema
      }
    }
  },
  "additionalProperties": false  // 整体也不允许额外字段
}
```

关键设计要点：

1. **`$ref` 引用**：annotations 和 edit_actions 引用了独立的 schema，实现契约的模块化
2. **`enum` 枚举约束**：type 和 priority 只能取预定义的值，防止前端写了 `if (type === 'compos')` 这种拼错
3. **`minimum/maximum`**：评分范围 0~100，超出范围验证失败
4. **`additionalProperties: false`**：不允许未定义的字段，确保前后端结构一致
5. **`type: ["object", "null"]`**：scores 允许为 null，兼容未来可能无法评分的场景

### 10.3 annotation.schema.json 标注数据格式解析

标注（Annotation）是前端可视化层最关心的数据结构：

```json
// packages/contracts/annotation.schema.json

{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://ai-photo-coach/contracts/annotation.schema.json",
  "title": "Annotation",
  "type": "object",

  "required": ["id", "source", "category", "geometry_type", "coords", "label", "message", "confidence"],

  "properties": {
    "id": { "type": "string" },

    // 标注来源
    "source": {
      "type": "string",
      "enum": ["cv", "llm", "rule"]
      // CV 层检测的 / LLM 分析的 / 规则引擎生成的
    },

    // 标注类别
    "category": {
      "type": "string",
      "enum": ["composition", "exposure", "color", "story", "guideline", "detail", "crop"]
    },

    // 几何类型（决定前端怎么画）
    "geometry_type": {
      "type": "string",
      "enum": ["bbox", "point", "line", "polygon"]
      // bbox = 矩形框，point = 点，line = 线段，polygon = 多边形
    },

    // 坐标数据
    "coords": {
      "type": "object",
      "required": ["coord_space"],  // 坐标系必须声明
      "properties": {
        // bbox 类型的坐标
        "x": { "type": "number" },
        "y": { "type": "number" },
        "w": { "type": "number" },
        "h": { "type": "number" },
        // line 类型的坐标
        "x1": { "type": "number" },
        "y1": { "type": "number" },
        "x2": { "type": "number" },
        "y2": { "type": "number" },
        // 坐标系（目前只支持像素坐标）
        "coord_space": {
          "type": "string",
          "enum": ["image_pixels"]
        }
      },
      "additionalProperties": true  // 允许扩展坐标字段
    },

    "label": { "type": "string" },      // 标注标签，如 "subject"、"highlight"
    "message": { "type": "string" },    // 给用户的说明文本
    "confidence": {                     // 置信度
      "type": "number",
      "minimum": 0,
      "maximum": 1                     // 0~1 之间，0.86 = 86% 置信度
    },
    "related_suggestion_ids": {         // 关联的建议 ID
      "type": "array",
      "items": { "type": "string" }
    }
  },
  "additionalProperties": false
}
```

前端根据 `geometry_type` 决定怎么绘制标注：

```
geometry_type = "bbox"   → Canvas 画矩形框 (x, y, w, h)
geometry_type = "line"   → Canvas 画线段 (x1, y1) → (x2, y2)
geometry_type = "point"  → Canvas 画圆点 (x, y)
geometry_type = "polygon"→ Canvas 画多边形 (points[])

类比前端：
  就像地图 SDK 的标注系统
  bbox = 矩形区域标注
  line = 路线标注
  point = 兴趣点标注
```

### 10.4 edit-action.schema.json 编辑动作格式解析

编辑动作（EditAction）定义了前端可以预览和应用的操作：

```json
// packages/contracts/edit-action.schema.json

{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://ai-photo-coach/contracts/edit-action.schema.json",
  "title": "EditAction",
  "type": "object",

  "required": ["id", "action_type", "source", "params", "reason", "previewable", "apply_mode"],

  "properties": {
    "id": { "type": "string" },

    // 动作类型
    "action_type": {
      "type": "string",
      "enum": ["crop", "exposure", "white_balance", "contrast", "saturation"]
      // 裁剪 / 曝光 / 白平衡 / 对比度 / 饱和度
    },

    // 动作来源
    "source": {
      "type": "string",
      "enum": ["cv", "llm", "rule"]
    },

    // 动作参数（不同 action_type 参数不同）
    "params": { "type": "object" },
    // crop:       { "x": 100, "y": 112, "w": 2064, "h": 1376, "ratio": "free" }
    // exposure:   { "alpha": 1.08, "beta": 18 }
    // white_balance: { "mode": "gray_world", "strength": 0.18 }

    "reason": { "type": "string" },  // 为什么建议这个操作

    "previewable": { "type": "boolean" },  // 是否支持预览
    // true = 前端可以先预览效果，用户确认后再应用
    // false = 只能直接应用，无法预览

    "apply_mode": {
      "type": "string",
      "enum": ["destructive", "non_destructive"]
      // destructive = 破坏性操作（如裁剪改变尺寸）
      // non_destructive = 非破坏性操作（如曝光调整，可撤销）
    }
  },
  "additionalProperties": false
}
```

前端根据 `action_type` 和 `apply_mode` 决定交互方式：

```
action_type = "crop" (destructive)
  → 显示裁剪框预览
  → 用户拖动调整裁剪区域
  → 点击"应用"才真正裁剪
  → 裁剪后不可撤销

action_type = "exposure" (non_destructive)
  → 实时预览曝光调整效果
  → 用滑块微调 alpha/beta 参数
  → 随时可以撤销

action_type = "white_balance" (non_destructive)
  → 显示白平衡前后对比
  → 可以调整 strength 强度
  → 随时可以撤销
```

### 10.5 数据契约如何保证前后端一致性

```
┌─────────────────────────────────────────────────────────────────────┐
│              数据契约驱动的前后端协作流程                              │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  1. 定义契约（packages/contracts/*.schema.json）                    │
│     └── 前后端共同review，确认字段和约束                             │
│                                                                     │
│  2. 后端实现                                                         │
│     └── ResultComposer 按 schema 组装结果                            │
│     └── CI 测试用 schema 验证实际输出                                │
│                                                                     │
│  3. 前端实现                                                         │
│     └── 用 json-schema-to-typescript 生成 TS 类型                    │
│     └── 按 TypeScript interface 开发组件                              │
│                                                                     │
│  4. 持续验证                                                         │
│     └── 后端 CI：pytest 用 jsonschema 库验证 API 返回值              │
│     └── 前端 CI：ajv 或 zod 验证 API 响应数据                       │
│     └── 任何一端改了字段 → 契约测试失败 → 双方同步                    │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘

示例：后端 CI 验证
```python
# Python 后端测试伪代码
import jsonschema

result = api_client.get("/api/v1/analysis/tasks/xxx").json()["result"]
schema = json.load(open("packages/contracts/analysis-result.schema.json"))
jsonschema.validate(result, schema)  # 不符合 schema 就抛异常！
```

示例：前端生成 TypeScript 类型
```bash
# 用工具从 JSON Schema 自动生成 TypeScript interface
npx json-schema-to-typescript \
  packages/contracts/analysis-result.schema.json \
  --output src/types/analysis-result.ts
```

生成的 TypeScript 类型（示例）：
```typescript
// 自动生成，手写容易出错，自动生成保证一致
export interface AnalysisResult {
  version: string;
  summary: string;
  suggestions: {
    id: string;
    type: "composition" | "exposure" | "color" | "story" | "other";
    text: string;
    problem?: string;
    action?: string;
    priority: "high" | "medium" | "low";
  }[];
  scores: { composition?: number; exposure?: number; color?: number; story?: number } | null;
  features_ref: { feature_id: string } | null;
  annotations: Annotation[];
  edit_actions: EditAction[];
}
```

### 10.6 契约驱动开发流程

```
┌─────────────────────────────────────────────────────────────────────┐
│                    契约驱动开发流程                                    │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  传统流程（❌ 容易出问题）：                                         │
│  后端写代码 → 前端写代码 → 联调发现数据不一致 → 改来改去 → 延期     │
│                                                                     │
│  契约驱动流程（✅ 高效）：                                           │
│  1. 先定契约 → 前后端对齐数据结构                                    │
│  2. 后端按契约实现 → 前端按契约开发（并行！）                        │
│  3. 联调时只需验证：实际数据是否符合契约                             │
│                                                                     │
│  类比前端：                                                          │
│  传统 = 后端先写完，前端照着抄 → 后端改了没通知 → bug               │
│  契约 = 先画设计图（Wireframe），前后端都按设计图开发                │
│       = 就像 API First 设计理念                                      │
│       = 类似 OpenAPI/Swagger 的 "设计先行" 模式                     │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 📝 面试常考点

1. **什么是数据契约？** 前后端共同遵守的数据格式约定，通常用 JSON Schema 定义，保证双方对数据结构的理解一致。
2. **JSON Schema 和 TypeScript interface 的区别？** Schema 是语言无关的，可以在运行时验证；interface 只在编译时检查。两者互补，不冲突。
3. **`additionalProperties: false` 有什么作用？** 禁止出现未定义的字段，防止前后端字段拼写不一致导致的 bug。
4. **`$ref` 引用机制的好处？** 大 schema 拆成小模块，复用公共定义，维护更方便。就像前端的组件化思想。
5. **数据契约怎么保证前后端一致性？** 后端 CI 用 schema 验证 API 返回值，前端 CI 用生成的 TS 类型检查代码，任何一方改了字段都会导致另一方的测试失败，强制同步。

---

> 第 1-10 章完。本笔记覆盖了从应用结构、配置管理、数据库 ORM、认证安全、依赖注入、路由与 Schema、异步任务、服务层管道、容器化部署到数据契约的完整后端知识体系。

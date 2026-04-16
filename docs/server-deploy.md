# 服务器部署说明

这套项目现在可以直接通过 Docker Compose 部署到一台 Linux 服务器。

## 适用方式

- 前端 `Vue + Vite` 会构建成静态文件，并由 `nginx` 提供服务
- `nginx` 同时反向代理 `/api/*` 到 FastAPI
- 后端、Worker、PostgreSQL、Redis、MinIO 都运行在同一个 Compose 网络内
- 服务器对外只暴露一个 Web 端口，默认是 `80`

## 服务器准备

建议使用 Ubuntu 22.04/24.04，并提前安装：

```bash
sudo apt update
sudo apt install -y docker.io docker-compose-plugin
sudo systemctl enable --now docker
```

如果当前用户没有 Docker 权限，可以执行：

```bash
sudo usermod -aG docker $USER
newgrp docker
```

## 部署步骤

1. 把仓库传到服务器

```bash
git clone <your-repo-url> ai-photo-coach
cd ai-photo-coach
```

2. 准备生产环境变量

```bash
cp infra/.env.prod.example infra/.env.prod
```

至少修改这些值：

- `POSTGRES_PASSWORD`
- `MINIO_ROOT_PASSWORD`
- `S3_SECRET_KEY`
- `CORS_ORIGINS`

如果你是直接用服务器 IP 访问前端：

```env
CORS_ORIGINS=http://你的服务器IP
WEB_PORT=80
```

如果你后面会绑定域名，则把 `CORS_ORIGINS` 改成你的域名，例如：

```env
CORS_ORIGINS=https://photo.example.com
```

3. 启动服务

```bash
docker compose --env-file infra/.env.prod -f infra/docker-compose.prod.yml up -d --build
```

4. 检查状态

```bash
docker compose --env-file infra/.env.prod -f infra/docker-compose.prod.yml ps
docker compose --env-file infra/.env.prod -f infra/docker-compose.prod.yml logs -f api
docker compose --env-file infra/.env.prod -f infra/docker-compose.prod.yml logs -f worker
```

## 访问地址

部署成功后：

- 前端首页：`http://你的服务器IP/`
- API 健康检查：`http://你的服务器IP/healthz`
- API 前缀：`http://你的服务器IP/api/v1`

## 常用维护命令

重启：

```bash
docker compose --env-file infra/.env.prod -f infra/docker-compose.prod.yml restart
```

停止：

```bash
docker compose --env-file infra/.env.prod -f infra/docker-compose.prod.yml down
```

更新代码后重新发布：

```bash
git pull
docker compose --env-file infra/.env.prod -f infra/docker-compose.prod.yml up -d --build
```

## 说明

- 目前默认使用项目里的 `mock-vision-v1`
- 数据库存储在 `pg_data` 卷
- Redis 数据存储在 `redis_data` 卷
- 图片对象存储在 `minio_data` 卷
- 当前方案先解决单机上线；如果你后面要加 HTTPS、域名和 CI/CD，可以在这套 Compose 外面再接一层 Caddy 或 Nginx

# 腾讯云服务器部署指南

本文档指导你将 **安全生产业务管理系统** 部署到腾讯云服务器（CVM 或轻量应用服务器）。

---

## 📋 前置准备

### 1. 服务器要求

| 配置项 | 最低要求 | 推荐配置 |
|--------|----------|----------|
| CPU | 2 核 | 2 核 |
| 内存 | 4 GB | 4 GB |
| 磁盘 | 50 GB SSD | 100 GB SSD |
| 带宽 | 3 Mbps | 5 Mbps+ |
| 操作系统 | Ubuntu 22.04 LTS | Ubuntu 22.04 LTS |

> 💡 **轻量应用服务器** 即可满足需求，2核4G6M 套餐约 200 元/年。

### 2. 安全组配置

在腾讯云控制台 > 安全组中，开放以下端口：

| 端口 | 协议 | 来源 | 用途 |
|------|------|------|------|
| 22 | TCP | 你的本地 IP | SSH 远程登录 |
| 80 | TCP | 0.0.0.0/0 | HTTP 访问 |
| 443 | TCP | 0.0.0.0/0 | HTTPS 访问（后续配置）|

> ⚠️ **重要**：不要将 PostgreSQL (5432)、Redis (6379)、MinIO (9000/9001) 暴露到公网！这些服务只在 Docker 内部网络通信。

### 3. 域名（可选但强烈建议）

如果有域名，建议先完成 ICP 备案（国内服务器必需），并添加 A 记录指向服务器公网 IP。

---

## 🚀 快速部署（推荐方式）

### 步骤一：连接服务器

```bash
# 使用你的实际 IP 替换 1.2.3.4
ssh ubuntu@1.2.3.4
```

### 步骤二：上传代码

**方式 A：Git 克隆（推荐）**

确保代码已推送到 GitHub/GitLab：

```bash
# 在服务器上执行
git clone https://github.com/your-org/safety-bms.git
cd safety-bms
```

**方式 B：本地打包上传**

```bash
# 在本地项目根目录执行
# 排除 node_modules 和 .venv 等大文件
tar czvf safety-bms.tar.gz \
  --exclude='frontend/node_modules' \
  --exclude='backend/.venv' \
  --exclude='.git' \
  .

# 上传到服务器
scp safety-bms.tar.gz ubuntu@1.2.3.4:/home/ubuntu/

# 在服务器上解压
ssh ubuntu@1.2.3.4 "tar xzvf /home/ubuntu/safety-bms.tar.gz -C /home/ubuntu/safety-bms && rm /home/ubuntu/safety-bms.tar.gz"
```

### 步骤三：运行部署脚本

```bash
cd safety-bms

# 1. 初始化服务器环境（首次执行，安装 Docker）
sudo bash scripts/setup-server.sh

# 2. 重新登录以应用 docker 用户组（或执行 newgrp docker）
newgrp docker

# 3. 一键部署
sudo bash scripts/deploy.sh
```

脚本会自动完成：
- ✅ 生成强密码和 JWT 密钥
- ✅ 创建 `.env` 生产环境配置
- ✅ 构建并启动所有容器
- ✅ 自动执行数据库迁移和初始化

### 步骤四：访问系统

部署完成后，在浏览器中访问：`http://你的服务器IP`

| 账号 | 密码 | 角色 |
|------|------|------|
| admin | admin123 | 超级管理员 |

---

## 🔒 配置 HTTPS（强烈建议）

### 方式 A：使用腾讯云 SSL 证书（推荐）

1. 在 [腾讯云 SSL 证书控制台](https://console.cloud.tencent.com/ssl) 申请免费证书
2. 下载 Nginx 格式的证书文件（`.crt` 和 `.key`）
3. 上传到服务器的 `~/safety-bms/ssl/` 目录：

```bash
# 重命名为标准文件名
mv your_domain.crt ssl/cert.pem
mv your_domain.key ssl/key.pem
```

4. 使用生产扩展配置启动：

```bash
cd ~/safety-bms
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

### 方式 B：使用 Let's Encrypt + Certbot（自动续期）

```bash
# 安装 certbot
docker run -it --rm \
  -v "$(pwd)/ssl:/etc/letsencrypt" \
  -v "$(pwd)/ssl:/var/lib/letsencrypt" \
  certbot/certbot certonly \
  --standalone -d your-domain.com --agree-tos -m your-email@example.com

# 创建符号链接
cd ssl
ln -s /etc/letsencrypt/live/your-domain.com/fullchain.pem cert.pem
ln -s /etc/letsencrypt/live/your-domain.com/privkey.pem key.pem

# 启动服务
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

配置自动续期（crontab）：

```bash
sudo crontab -e
# 添加以下行（每月 1 日凌晨 3 点自动续期）
0 3 1 * * docker run --rm -v /home/ubuntu/safety-bms/ssl:/etc/letsencrypt certbot/certbot renew --quiet && cd /home/ubuntu/safety-bms && docker compose restart frontend
```

---

## 🔄 后续维护

### 更新部署

```bash
cd ~/safety-bms

# 拉取最新代码
git pull origin main

# 重新构建并启动
docker compose pull
docker compose up -d --build

# 执行数据库迁移（如有 schema 变更）
docker compose exec backend alembic upgrade head
```

### 查看日志

```bash
# 所有服务日志
docker compose logs -f

# 仅后端日志
docker compose logs -f backend

# 仅前端日志
docker compose logs -f frontend

# 最近 100 行日志
docker compose logs --tail=100 backend
```

### 数据备份

备份文件已自动保存在 `~/safety-bms/backups/` 目录，默认策略：
- 每日备份（保留 7 天）
- 每周备份（保留 4 周）
- 每月备份（保留 6 个月）

手动备份：
```bash
docker compose exec postgres-backup /backup.sh
```

恢复备份：
```bash
# 停止后端服务
docker compose stop backend

# 从备份文件恢复（替换为实际的备份文件名）
docker compose exec -T postgres psql -U postgres safety_bms < backups/weekly/safety_bms-XXXX.sql

# 重启服务
docker compose start backend
```

### 修改配置后重启

```bash
# 修改 .env 后，需要重启服务使配置生效
docker compose restart
```

---

## 🛠️ 常见问题

### Q1: 部署后无法访问？

1. 检查安全组是否开放 80/443 端口
2. 检查服务状态：`docker compose ps`
3. 检查后端日志：`docker compose logs backend`
4. 检查前端是否能访问后端：`curl http://localhost/api/v1/health`

### Q2: 如何修改 admin 密码？

登录系统后，在「系统管理 > 用户管理」中编辑 admin 用户修改密码。

### Q3: 如何绑定自定义域名？

1. 域名 DNS 添加 A 记录指向服务器 IP
2. 修改 `.env` 中的 `ALLOWED_ORIGINS`：
   ```
   ALLOWED_ORIGINS=["https://your-domain.com"]
   ```
3. 重启服务：`docker compose restart`

### Q4: 内存不足导致服务崩溃？

脚本已自动配置 2GB Swap。如仍不足，建议升级服务器配置或：

```bash
# 减少 gunicorn workers 数量
# 编辑 backend/gunicorn.conf.py，将 workers 改为 2
```

### Q5: 数据库连接失败？

确保 `.env` 中的 `DB_HOST=postgres`（Docker 内部服务名），不要写成 `localhost`。

---

## 📞 技术支持

如有问题，请检查：
1. 服务状态：`docker compose ps`
2. 日志输出：`docker compose logs`
3. 系统资源：`docker stats`、`free -h`、`df -h`

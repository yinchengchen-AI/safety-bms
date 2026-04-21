# 安全生产业务管理系统 (Safety Production BMS)

安全生产第三方服务咨询公司业务管理系统，覆盖客户管理、合同管理、服务管理、开票管理、收款管理、统计分析全业务链路。

## 技术栈

**后端**
- Python 3.12 + FastAPI
- SQLAlchemy 2.0 + Alembic（数据库迁移）
- PostgreSQL 16（主数据库）
- Redis 7（JWT Token 黑名单 + Refresh Token 缓存）
- MinIO（文件存储：合同、服务报告、发票、收款凭证）

**前端**
- React 18 + TypeScript + Vite
- Ant Design 5.x（UI 组件库）
- Redux Toolkit 2.x + RTK Query（状态管理 + API 缓存）
- @ant-design/charts（仪表盘与统计分析图表）
- React Router v7

**部署**
- Docker Compose（一键启动全套服务）

## 快速启动

项目现在明确分为两种本地运行模式，请二选一使用：

### 模式 A：完整容器模式（推荐用于联调）

前端、后端、PostgreSQL、Redis、MinIO 全部运行在 Docker 中。

1. 准备根目录 Compose 配置：

```bash
cp .env.example .env
```

2. 启动完整栈：

```bash
docker compose up -d --build
```

3. 初始化默认角色、管理员账号并同步权限定义：

```bash
docker compose exec backend python app/db/init_db.py
docker compose exec backend python app/cli/sync_permissions.py
```

说明：

- 根目录 `.env` 用于 **完整容器模式**，其中数据库、Redis、MinIO 地址应保持为容器服务名（如 `postgres`、`redis`、`minio:9000`）
- 该模式下只暴露前端入口 `http://localhost`
- 后端文档通过前端反向代理访问：`http://localhost/api/docs`

### 模式 B：本机开发模式（仅 Docker 基础设施）

Docker 只启动 PostgreSQL / Redis / MinIO，前后端在宿主机本地热重载运行。

1. 准备后端本地配置：

```bash
cp backend/.env.example backend/.env
```

2. 启动基础设施：

```bash
docker compose -f docker-compose.dev.yml up -d
```

3. 启动本机后端：

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

4. 初始化默认角色、管理员账号并同步权限定义：

```bash
cd backend
PYTHONPATH=. python app/db/init_db.py
PYTHONPATH=. python app/cli/sync_permissions.py
```

5. 启动本机前端：

```bash
cd frontend
npm install
npm run dev
```

说明：

- `backend/.env` 用于 **本机开发模式**，其中数据库、Redis、MinIO 地址应保持为 `localhost`
- Vite 会将 `/api` 代理到 `http://localhost:8000`
- 该模式下前端入口为 `http://localhost:5173`，后端文档为 `http://localhost:8000/api/docs`
- `docker-compose.dev.yml` 不会启动 backend/frontend 容器

### 模式边界说明

- 不要再把根目录 `.env` 和 `backend/.env` 混用，它们分别服务于不同模式
- `docker-compose.yml` 是 **完整容器模式**
- `docker-compose.dev.yml` 是 **本机开发模式的基础设施**
- 完整容器模式不再暴露 Postgres / Redis 到宿主机，避免和本机开发模式形成错误耦合

## 访问地址

### 完整容器模式

| 服务 | 地址 |
|------|------|
| 前端 | http://localhost |
| API 文档 (Swagger) | http://localhost/api/docs |

### 本机开发模式

| 服务 | 地址 |
|------|------|
| 前端 | http://localhost:5173 |
| 后端 API | http://localhost:8000 |
| API 文档 (Swagger) | http://localhost:8000/api/docs |
| MinIO 控制台 | http://localhost:9001 |

## 初始账号

| 用户名 | 密码 | 角色 |
|--------|------|------|
| admin | admin123 | 超级管理员 |

## 系统模块

| 模块 | 功能 |
|------|------|
| 仪表盘 | 月度开票/收款趋势、合同状态分布、逾期预警 |
| 统计分析 | 经营/财务/客户/服务多维图表分析、明细下钻、Excel 导出 |
| 客户管理 | 客户信息、联系人、跟进记录 |
| 合同管理 | 合同全生命周期管理（草稿→审核→生效→完成）|
| 服务管理 | 服务工单（5种服务类型）管理与进度跟踪 |
| 开票管理 | 开票申请 / 审核 / 驳回 / 已寄出 / 删除，自动校验可开票余额 |
| 收款管理 | 收款记录（新增/编辑/删除）+ 逾期应收预警，编辑时校验可收款余额 |
| 用户管理 | 用户 CRUD + RBAC 角色管理（仅管理员）|

## 业务角色

| 角色 | 权限 |
|------|------|
| admin | 全部权限 + 用户管理 |
| sales | 客户、合同、服务读写 + 仪表盘/统计分析查看 |
| service | 服务工单读写 + 客户/合同只读 + 仪表盘/统计分析查看 |
| finance | 开票、收款读写 + 合同只读 + 仪表盘/统计分析查看 |
| viewer | 全部只读 + 仪表盘/统计分析查看 |

## 统计分析模块

- 前端入口：`/analytics`
- 路由/菜单权限：`analytics:read`
- 默认授予角色：`admin`、`sales`、`service`、`finance`、`viewer`
- 分析内容：
  - 经营分析：签约额 / 开票额 / 收款额趋势、签约排行
  - 财务分析：回款率、应收余额、应收账龄、高风险合同
  - 客户与服务分析：客户增长、行业分布、客户状态分布、服务效率、服务类型分布
- 交互能力：日期范围筛选、图表点击下钻明细、Excel 导出

更多说明见：`docs/analytics-invoice-operations.md`

## 开票审核流程

- 发票状态：`applying`（申请中）→ `issued`（已开票）→ `sent`（已寄出）
- 驳回状态：`rejected`（已拒绝）
- 审核通过时必须填写：开票日期、实际发票号
- 审核驳回时必须填写：驳回原因
- 开票申请与审核通过前都会校验合同可开票余额，避免累计开票金额超过合同总额

## 生产部署

### 一键部署

```bash
cp .env.example .env
# 编辑 .env，设置强密码和 SECRET_KEY
docker compose up -d --build
```

### 生产环境关键配置

1. **`.env` 必改项**：
   - `SECRET_KEY`：至少 32 位随机字符串
   - `DB_PASSWORD`：强密码
   - `ALLOWED_ORIGINS`：精确设置为你的域名，如 `["https://bms.yourcompany.com"]`
   - `DEBUG=false`

2. **HTTPS / TLS**：
   - 准备 SSL 证书放到 `./ssl/` 目录（`cert.pem` 和 `key.pem`）
   - 使用生产扩展配置启动：
     ```bash
     docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
     ```

3. **数据库自动备份**：
   - `docker-compose.yml` 已包含 `postgres-backup` 服务
   - 备份文件保存在 `./backups/` 目录
   - 默认保留策略：7 天每日备份 + 4 周每周备份 + 6 月每月备份

4. **运行时环境变量（前端）**：
   - 前端支持通过 `API_BASE_URL` 运行时切换 API 地址
   - 默认通过 nginx 反向代理同域访问 `/api/v1`
   - 如需跨域部署：
     ```bash
     docker run -e API_BASE_URL=https://api.example.com ...
     ```

### 生产架构特点

| 特性 | 说明 |
|------|------|
| WSGI 服务器 | gunicorn + 4 uvicorn workers |
| 自动初始化 | `backend-init` 服务自动执行 `alembic upgrade head` 和 `init_db.py` |
| 分布式锁 | 调度器通过 Redis 分布式锁防止多实例重复触发定时任务 |
| 日志格式 | DEBUG=false 时输出 JSON 结构化日志 |
| 文档隐藏 | 生产环境自动关闭 `/api/docs`、`/api/redoc`、`/api/openapi.json` |
| 连接池 | SQLAlchemy pool_size=10, max_overflow=20, pool_recycle=3600s |

## 业务逻辑约束

- **开票校验**: 累计开票金额不得超过合同总额；创建、编辑、审核通过前均会校验
- **收款校验**: 累计收款金额不得超过合同总额；若关联发票，不得超过发票金额；创建和编辑均会校验
- **开票删除保护**: `issued` / `sent` 状态的发票若已有关联收款，禁止删除
- **统计口径统一**:
  - 签约额：仅统计 `signed` / `executing` / `completed` 状态且 `sign_date` 不为空的合同
  - 开票额：仅统计 `issued` / `sent` 状态的发票
  - 收款额：仅统计未删除且关联合同满足签约口径的收款记录
- **权限口径**: 菜单、路由守卫和后端接口统一按入口权限控制，例如 `/analytics` 需要 `analytics:read`
- **标签展示**: 仪表盘和统计分析中的状态/类型图表优先展示中文标签映射
- **逾期判断**: 合同到期且应收余额 > 0 → 标记逾期
- **软删除**: 客户、合同、发票、收款均使用软删除（`is_deleted` 标记），删除后数据保留可审计
- **合同状态机**: 每次状态变更自动记录变更历史；终止合同仅要求无未完成工单，不再要求无开票/收款记录
- **JWT 安全**: 退出登录后 Token 加入 Redis 黑名单即时失效
# safety-bms

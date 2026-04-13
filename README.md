# 安全生产业务管理系统 (Safety Production BMS)

安全生产第三方服务咨询公司业务管理系统，覆盖客户管理、合同管理、服务管理、开票管理、收款管理全业务链路。

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
- @ant-design/charts（仪表盘图表）
- React Router v7

**部署**
- Docker Compose（一键启动全套服务）

## 快速启动

### 1. 克隆配置文件

```bash
cp .env.example .env
```

编辑 `.env`，设置各服务密码。

### 2. Docker Compose 启动（生产模式）

```bash
docker-compose up -d
```

### 3. 开发模式（仅启动基础设施）

```bash
docker-compose -f docker-compose.dev.yml up -d
```

后端：
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

前端：
```bash
cd frontend
npm install
npm run dev
```

## 访问地址

| 服务 | 地址 |
|------|------|
| 前端 | http://localhost |
| 后端 API | http://localhost:8000 |
| API 文档 (Swagger) | http://localhost:8000/api/docs |
| MinIO 控制台 | http://localhost:9001 |

## 初始账号

| 用户名 | 密码 | 角色 |
|--------|------|------|
| admin | Admin@123456 | 超级管理员 |

## 系统模块

| 模块 | 功能 |
|------|------|
| 仪表盘 | 月度开票/收款趋势、合同状态分布、逾期预警 |
| 客户管理 | 客户信息、联系人、跟进记录 |
| 合同管理 | 合同全生命周期管理（草稿→审核→生效→完成）|
| 服务管理 | 服务工单（5种服务类型）管理与进度跟踪 |
| 开票管理 | 开票申请（自动校验可开票余额）|
| 收款管理 | 收款记录 + 逾期应收预警 |
| 用户管理 | 用户 CRUD + RBAC 角色管理（仅管理员）|

## 业务角色

| 角色 | 权限 |
|------|------|
| admin | 全部权限 + 用户管理 |
| sales | 客户、合同、服务读写 |
| service | 服务工单读写 |
| finance | 开票、收款读写 |
| viewer | 全部只读 |

## 业务逻辑约束

- **开票校验**: 累计开票金额不得超过合同总额
- **逾期判断**: 合同到期且应收余额 > 0 → 标记逾期
- **软删除**: 客户和合同使用软删除（`is_deleted` 标记）
- **合同状态机**: 每次状态变更自动记录变更历史
- **JWT 安全**: 退出登录后 Token 加入 Redis 黑名单即时失效

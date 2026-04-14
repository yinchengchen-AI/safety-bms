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

初始化默认角色、管理员账号并同步权限定义：

```bash
cd backend
PYTHONPATH=. python app/db/init_db.py
PYTHONPATH=. python app/cli/sync_permissions.py
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
| 统计分析 | 经营/财务/客户/服务多维图表分析、明细下钻、Excel 导出 |
| 客户管理 | 客户信息、联系人、跟进记录 |
| 合同管理 | 合同全生命周期管理（草稿→审核→生效→完成）|
| 服务管理 | 服务工单（5种服务类型）管理与进度跟踪 |
| 开票管理 | 开票申请 / 审核 / 驳回 / 已寄出，自动校验可开票余额 |
| 收款管理 | 收款记录 + 逾期应收预警 |
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

## 业务逻辑约束

- **开票校验**: 累计开票金额不得超过合同总额
- **开票统计口径**: 仪表盘与统计分析中的开票额仅统计 `issued` / `sent` 状态发票，并优先按 `invoice_date` 归档；缺失时回退到 `created_at`
- **合同统计口径**: 统计分析中的签约额统一按 `sign_date` 统计
- **权限口径**: 菜单、路由守卫和后端接口统一按入口权限控制，例如 `/analytics` 需要 `analytics:read`
- **标签展示**: 仪表盘和统计分析中的状态/类型图表优先展示中文标签映射
- **逾期判断**: 合同到期且应收余额 > 0 → 标记逾期
- **软删除**: 客户和合同使用软删除（`is_deleted` 标记）
- **合同状态机**: 每次状态变更自动记录变更历史
- **JWT 安全**: 退出登录后 Token 加入 Redis 黑名单即时失效
# safety-bms

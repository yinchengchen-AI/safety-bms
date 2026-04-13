# Plan: 安全生产第三方服务咨询公司业务管理系统

## TL;DR
全栈项目：React + Ant Design 前端，FastAPI + PostgreSQL + Redis + MinIO 后端，Docker Compose 部署。
包含用户权限、客户管理、合同管理、服务管理、开票管理、收款管理六大模块，模块间有明确的业务流程链路。

---

## 确认的技术决策
- 认证：JWT Token (Bearer)
- 部署：Docker Compose
- 客服管理：实为【客户管理】（客户资料、联系人、跟进记录）
- 服务类型：安全评价、安全培训、安全检测检验、安全咨询顾问、应急预案编制

---

## 业务流程链路（核心逻辑）

```
客户管理 → 合同管理 → 服务管理 → 开票管理 → 收款管理
    ↑           ↑          ↑
  用户权限管理贯穿所有模块
```

详细流程：
1. 销售员创建客户 → 跟进记录
2. 客户确认后签订合同（关联客户）
3. 合同生效后创建服务工单（关联合同，指定服务类型、服务人员）
4. 服务完成后生成发票（关联合同、可部分开票）
5. 收款登记（关联发票或合同，支持分期收款）

---

## 模块设计

### 1. 用户角色权限模块
**角色**：系统管理员、销售、服务人员、财务、只读查看
**权限粒度**：菜单权限 + 操作权限（CRUD级别）
**技术**：RBAC模型，JWT + Redis缓存Token黑名单

### 2. 客户管理模块
- 客户基本信息（公司名、行业、规模、地址、统一社会信用代码）
- 联系人管理（多联系人、主联系人标记）
- 客户跟进记录（时间线）
- 客户状态：意向/成交/流失
- 附件上传（MinIO存储）

### 3. 合同管理模块
- 合同关联客户（必选）
- 合同类型：对应服务类型（安全评价/培训/检测/顾问/预案）
- 合同金额、合同期限、付款方式（一次性/分期）
- 合同状态：草稿/审核中/生效/完成/终止
- 合同附件（MinIO）
- 合同变更记录

### 4. 服务管理模块
- 服务工单关联合同
- 服务项目明细（多个服务项可在一个合同下）
- 分配服务人员
- 服务进度跟踪（待开始/进行中/已完成/已验收）
- 服务报告上传（MinIO）
- 服务时间记录

### 5. 开票管理模块
- 发票关联合同（一个合同可开多次票，累计不超合同金额）
- 发票类型：增值税专用发票/增值税普通发票
- 开票金额、税率、税额
- 开票申请 → 已开票 → 已寄出
- 发票扫描件上传（MinIO）
- 开票金额校验（不可超合同未开票金额）

### 6. 收款管理模块
- 收款关联合同（支持关联发票）
- 收款方式：银行转账/现金/支票
- 应收账款追踪（合同金额 - 已收款 = 应收余额）
- 收款状态：待收/部分收款/已收齐
- 收款凭证上传（MinIO）
- 逾期预警（基于合同付款条款）

---

## 项目目录结构

```
safety-bms/                          # 项目根目录
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── core/
│   │   │   ├── security.py          # JWT, 密码哈希
│   │   │   ├── exceptions.py        # 自定义异常
│   │   │   └── constants.py
│   │   ├── db/
│   │   │   ├── session.py           # SQLAlchemy Session
│   │   │   ├── base.py              # Base Model
│   │   │   └── init_db.py           # 初始化数据
│   │   ├── models/
│   │   │   ├── user.py              # User, Role, Permission, UserRole
│   │   │   ├── customer.py          # Customer, Contact, FollowUp
│   │   │   ├── contract.py          # Contract, ContractItem, ContractChange
│   │   │   ├── service.py           # ServiceOrder, ServiceItem, ServiceReport
│   │   │   ├── invoice.py           # Invoice, InvoiceItem
│   │   │   └── payment.py           # Payment, PaymentRecord
│   │   ├── schemas/
│   │   │   ├── common.py            # Pagination, Response, Token
│   │   │   ├── user.py
│   │   │   ├── customer.py
│   │   │   ├── contract.py
│   │   │   ├── service.py
│   │   │   ├── invoice.py
│   │   │   └── payment.py
│   │   ├── crud/
│   │   │   ├── base.py              # 泛型CRUD基类
│   │   │   └── [各模块crud]
│   │   ├── api/
│   │   │   └── v1/
│   │   │       ├── router.py        # 汇总所有路由
│   │   │       └── endpoints/
│   │   │           ├── auth.py      # 登录/刷新token
│   │   │           ├── users.py
│   │   │           ├── customers.py
│   │   │           ├── contracts.py
│   │   │           ├── services.py
│   │   │           ├── invoices.py
│   │   │           └── payments.py
│   │   ├── services/                # 业务逻辑层
│   │   │   ├── auth_service.py
│   │   │   ├── contract_service.py  # 合同金额校验逻辑
│   │   │   ├── invoice_service.py   # 开票金额校验
│   │   │   ├── payment_service.py   # 收款追踪逻辑
│   │   │   └── minio_service.py     # 文件上传
│   │   └── utils/
│   │       ├── redis_client.py
│   │       └── pagination.py
│   ├── migrations/                   # Alembic
│   ├── tests/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── api/                     # Axios实例 + 各模块API
│   │   ├── components/              # 公共组件
│   │   ├── pages/
│   │   │   ├── Dashboard/
│   │   │   ├── Users/               # 用户管理（管理员）
│   │   │   ├── Roles/               # 角色权限管理
│   │   │   ├── Customers/           # 客户管理
│   │   │   ├── Contracts/           # 合同管理
│   │   │   ├── Services/            # 服务管理
│   │   │   ├── Invoices/            # 开票管理
│   │   │   └── Payments/            # 收款管理
│   │   ├── store/                   # Redux Toolkit (authSlice/uiSlice + RTK Query)
│   │   ├── hooks/
│   │   ├── types/
│   │   ├── utils/
│   │   └── config/
│   ├── Dockerfile
│   ├── nginx.conf
│   └── package.json
├── docker-compose.yml
├── docker-compose.dev.yml
├── .env.example
└── README.md
```

---

## 关键数据库关系

```
users ──< user_roles >── roles ──< role_permissions >── permissions
customers ──< contacts
customers ──< follow_ups
customers ──< contracts (customer_id FK)
contracts ──< contract_items
contracts ──< service_orders (contract_id FK)
service_orders ──< service_items
service_orders ──< service_reports
contracts ──< invoices (contract_id FK)  [校验：sum(invoice.amount) <= contract.amount]
invoices ──< payments (invoice_id FK)    [也可 payment.contract_id 直接关联合同]
```

---

## 实施步骤（分阶段）

### Phase 1: 项目脚手架 (独立，可并行)
1. 创建 backend/ 目录结构 + FastAPI 基础配置
2. 创建 frontend/ 目录结构 + React + Ant Design 基础配置
3. 创建 docker-compose.yml（postgres + redis + minio + backend + frontend）

### Phase 2: 后端基础层 (按序)
4. 配置 SQLAlchemy + Alembic + 数据库连接
5. 创建所有数据库模型（models/）
6. 运行 Alembic 生成初始迁移
7. 实现 JWT 认证 + Redis Token 黑名单

### Phase 3: 后端业务逻辑 (可并行 per 模块)
8. 实现各模块 CRUD + schemas
9. 实现各模块 service 层（含业务校验逻辑）
10. 实现各模块 API endpoints
11. 配置 MinIO 文件上传 service

### Phase 4: 前端实现 (依赖 Phase 3)
12. 配置 Axios 实例 + 路由 + 权限守卫
13. 实现各模块页面（列表/详情/增删改）
14. 实现仪表盘（统计数据）

### Phase 5: 集成验证
15. 联调测试
16. 编写 README

---

## 验证步骤
1. docker compose up 能正常启动所有服务
2. 登录 → JWT Token 正常颁发 → 受保护接口需要认证
3. 业务流程测试：创建客户→签订合同→创建服务工单→开票（不超合同金额）→登记收款
4. 开票金额校验：尝试开超合同金额的票，应返回错误
5. RBAC 验证：非管理员无法访问用户管理接口

---

## 范围边界
- 包含：上述6大模块的完整CRUD + 核心业务逻辑校验 + 文件上传
- 不包含：短信通知、邮件发送、报表导出、移动端适配（可后续扩展）
- 不包含：工作流审批引擎（合同审批用简单状态机实现）

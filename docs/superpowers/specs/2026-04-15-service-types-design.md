# 服务类型独立功能模块设计文档

## 需求概述

将当前硬编码的「服务类型」枚举改造成可动态配置的功能模块，支持后台管理（增删改查）及扩展属性配置，并在合同、服务工单、合同模板等业务场景中动态引用。

## 现状分析

当前系统中，服务类型以 Python `Enum` 硬编码在 `backend/app/core/constants.py` 中，共 5 个固定值：

| 枚举值 (code) | 中文名称 |
|---------------|----------|
| `evaluation` | 安全评价 |
| `training` | 安全培训 |
| `inspection` | 安全检测检验 |
| `consulting` | 安全咨询顾问 |
| `emergency_plan` | 应急预案编制 |

这些类型被以下 3 个数据库表直接使用（PostgreSQL ENUM 类型）：
- `contracts.service_type`
- `service_orders.service_type`
- `contract_templates.service_type`

前端在 `frontend/src/types/index.ts` 和 `frontend/src/utils/constants.ts` 中做了镜像硬编码。

## 目标

1. 新增独立的数据库表 `service_types`，支持动态维护服务类型。
2. 每个服务类型支持扩展属性：默认单价、标准工期、资质要求、默认合同模板。
3. 将现有业务表中的 ENUM 字段替换为对 `service_types` 的外键引用。
4. 新增后台管理页面，admin 可管理服务类型。
5. 前端所有下拉框和展示逻辑改为动态获取，不再依赖硬编码枚举。
6. 自动迁移现有 5 个类型到新表，保留历史数据关联。

## 数据模型设计

### 新表：`service_types`

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | Integer, PK, auto | 主键 |
| `code` | VARCHAR, unique, not null | 机器标识（如 `evaluation`），兼容旧枚举值 |
| `name` | VARCHAR, not null | 展示名称（如 `安全评价`） |
| `default_price` | DECIMAL(18,2), nullable | 默认单价（元） |
| `standard_duration_days` | Integer, nullable | 标准工期（天） |
| `qualification_requirements` | TEXT, nullable | 资质要求 |
| `default_contract_template_id` | Integer, FK → `contract_templates.id`, nullable | 默认合同模板 |
| `is_active` | Boolean, default true | 是否启用 |
| `created_at` | DateTime | 创建时间 |
| `updated_at` | DateTime | 更新时间 |

### 改造现有表

将以下字段从 PostgreSQL ENUM 改为 `Integer(FK → service_types.id)`：
- `contracts.service_type`
- `service_orders.service_type`
- `contract_templates.service_type`

外键约束统一设置 `ON DELETE RESTRICT`，当类型被引用时禁止删除，后端返回友好错误提示。

## 后端 API 设计

### 新增接口：`/api/v1/service-types`

| 方法 | 路径 | 权限 | 说明 |
|------|------|------|------|
| GET | `/service-types` | 任意登录用户 | 列表，支持分页、按 `is_active` 筛选 |
| GET | `/service-types/{id}` | 任意登录用户 | 详情 |
| POST | `/service-types` | admin | 创建 |
| PUT | `/service-types/{id}` | admin | 更新 |
| DELETE | `/service-types/{id}` | admin | 删除（受外键引用限制） |
| GET | `/service-types/{id}/usage` | admin | 返回引用统计（合同数、工单数、模板数） |

### 现有 API 兼容性调整

为最小化前端改动，`ContractOut`、`ServiceOrderOut`、`ContractTemplateOut` 等 Schema 做如下调整：
- 保留 `service_type: string`（返回 `service_types.code`）
- 新增 `service_type_id: int`
- 新增 `service_type_name: string`

这样前端原有 `record.service_type` 的代码可继续工作，展示名称可直接使用 `service_type_name`。

文档生成服务 (`contract_doc_service.py`) 和导出逻辑不再使用本地映射，统一从 `service_types` 表查询名称。

## 前端设计

### 新增页面：服务类型管理

- **菜单位置**：顶部主菜单新增「服务类型管理」，仅 admin 可见。
- **页面结构**：
  - 表格列：名称、默认单价、标准工期、启用状态、操作（编辑/删除）
  - 新增/编辑弹窗表单：包含 `service_types` 表全部字段
  - 删除时先调用 `GET /service-types/{id}/usage` 检查引用，如有引用则禁止删除并提示

### 改造现有页面

以下页面中的「服务类型」下拉框从静态 `ServiceTypeLabels` 改为动态调用 `GET /service-types?is_active=true`：
- `Contracts/index.tsx`（合同创建/编辑）
- `Services/index.tsx`（服务工单创建/编辑）
- `ContractTemplates/index.tsx`（合同模板创建/筛选）
- `Analytics/index.tsx`（分析报表筛选）
- `Dashboard/index.tsx`（如需按类型过滤）

移除前端的 `ServiceType` union type 和 `ServiceTypeLabels`，将相关类型改为 `string`。

## 数据迁移策略

通过 Alembic 迁移脚本一次性完成：

1. 创建 `service_types` 表。
2. 插入 5 条初始数据（`code` 和 `name` 对应现有枚举值）。
3. 在 `contracts`、`service_orders`、`contract_templates` 中新增临时列 `service_type_id`。
4. 根据旧 ENUM 值将对应记录更新为 `service_types.id`。
5. 删除旧 `service_type` 列，重命名 `service_type_id` → `service_type`。
6. 删除 PostgreSQL ENUM 类型 `service_type` 和 `service_type_order`。
7. 添加新的外键约束（`ON DELETE RESTRICT`）。

## 风险与处理

| 风险 | 处理方案 |
|------|----------|
| 前端大量硬编码引用 | 将 `ServiceType` 改为 `string`，`ServiceTypeLabels` 移除，所有展示改用后端返回的 `service_type_name` |
| 报表/文档生成依赖本地映射 | `contract_doc_service.py` 改为查询 `service_types` 表获取名称 |
| 列表查询 JOIN 增加性能开销 | 使用 SQLAlchemy `selectinload` / `joinedload` 优化；服务类型列表可缓存到 Redis（数据量小） |
| 迁移脚本失败导致数据不一致 | 在测试环境先行验证迁移脚本；所有更新操作放在同一个事务中执行 |

## 验收标准

- [ ] 数据库中存在 `service_types` 表，包含设计中的所有字段。
- [ ] `contracts`、`service_orders`、`contract_templates` 的 `service_type` 为外键关联。
- [ ] 管理页面可见且 admin 可进行 CRUD 操作；删除被引用类型时给出明确提示。
- [ ] 前端合同/工单/模板页中的服务类型下拉框为动态获取，新增类型后可立即选择。
- [ ] 现有 5 个服务类型的历史数据完整迁移，业务页面展示无异常。
- [ ] 合同文档生成和 Excel 导出中的服务类型名称正确。

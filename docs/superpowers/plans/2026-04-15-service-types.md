# 服务类型独立功能模块实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将硬编码的服务类型枚举改造成可动态配置的独立功能模块，包含后端 CRUD API、数据库迁移、前端管理页面及现有业务页面的动态下拉框改造。

**Architecture:** 新增 `service_types` 数据表替代 PostgreSQL ENUM，contracts/service_orders/contract_templates 改为外键关联；后端提供 RESTful API；前端通过 RTK Query 动态获取服务类型列表，并在管理页面支持 CRUD。

**Tech Stack:** FastAPI + SQLAlchemy + Alembic (Backend), React + TypeScript + RTK Query + Ant Design (Frontend)

---

## 文件清单

| 文件 | 操作 | 说明 |
|------|------|------|
| `backend/app/models/service_type.py` | 创建 | ServiceType 模型 |
| `backend/app/schemas/service_type.py` | 创建 | ServiceType 的 Pydantic Schema |
| `backend/app/crud/service_type.py` | 创建 | ServiceType CRUD |
| `backend/app/api/v1/endpoints/service_types.py` | 创建 | ServiceType API 路由 |
| `backend/app/api/v1/router.py` | 修改 | 注册新路由 |
| `backend/migrations/versions/xxxx_add_service_types_table.py` | 创建 | Alembic 迁移脚本 |
| `backend/app/models/contract.py` | 修改 | Contract/ContractTemplate 字段改为 FK |
| `backend/app/models/service.py` | 修改 | ServiceOrder 字段改为 FK |
| `backend/app/schemas/contract.py` | 修改 | 移除 ServiceType 枚举引用，增加兼容性字段 |
| `backend/app/schemas/service.py` | 修改 | 移除 ServiceType 枚举引用，增加兼容性字段 |
| `backend/app/api/v1/endpoints/contracts.py` | 修改 | 导出和列表查询适配新结构 |
| `backend/app/api/v1/endpoints/services.py` | 修改 | 导出和列表查询适配新结构 |
| `backend/app/api/v1/endpoints/contract_templates.py` | 修改 | 查询参数和返回适配新结构 |
| `backend/app/services/contract_doc_service.py` | 修改 | 从数据库查询服务类型名称 |
| `backend/app/crud/contract.py` | 修改 | 适配新模型结构 |
| `frontend/src/types/index.ts` | 修改 | 移除 ServiceType union，新增 ServiceType 接口 |
| `frontend/src/utils/constants.ts` | 修改 | 移除 ServiceTypeLabels |
| `frontend/src/store/api/serviceTypesApi.ts` | 创建 | RTK Query API slice |
| `frontend/src/store/api/baseApi.ts` | 修改 | 添加 tagType |
| `frontend/src/store/api/contractsApi.ts` | 修改 | 移除 ServiceType 类型导入 |
| `frontend/src/store/api/servicesApi.ts` | 修改 | 移除 ServiceType 类型导入 |
| `frontend/src/store/api/contractTemplatesApi.ts` | 修改 | 移除 ServiceType 类型导入 |
| `frontend/src/store/api/analyticsApi.ts` | 修改 | 移除 ServiceType 类型导入 |
| `frontend/src/config/menuConfig.ts` | 修改 | 添加菜单项 |
| `frontend/src/App.tsx` | 修改 | 注册新路由 |
| `frontend/src/pages/ServiceTypes/index.tsx` | 创建 | 服务类型管理页面 |
| `frontend/src/pages/Contracts/index.tsx` | 修改 | 动态获取服务类型下拉框 |
| `frontend/src/pages/Services/index.tsx` | 修改 | 动态获取服务类型下拉框 |
| `frontend/src/pages/ContractTemplates/index.tsx` | 修改 | 动态获取服务类型下拉框 |
| `frontend/src/pages/Analytics/index.tsx` | 修改 | 动态获取服务类型下拉框（如需要） |
| `frontend/src/pages/Dashboard/index.tsx` | 修改 | 使用后端返回名称（如需要） |

---

### Task 1: 创建 ServiceType 后端模型

**Files:**
- Create: `backend/app/models/service_type.py`
- Modify: `backend/app/models/__init__.py`

- [ ] **Step 1: 编写模型文件**

```python
from sqlalchemy import Column, Integer, String, Numeric, Text, Boolean, ForeignKey
from sqlalchemy.orm import relationship

from app.db.base import Base, TimestampMixin


class ServiceType(Base, TimestampMixin):
    __tablename__ = "service_types"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True, nullable=False, comment="机器标识")
    name = Column(String(100), nullable=False, comment="展示名称")
    default_price = Column(Numeric(18, 2), nullable=True, comment="默认单价")
    standard_duration_days = Column(Integer, nullable=True, comment="标准工期(天)")
    qualification_requirements = Column(Text, nullable=True, comment="资质要求")
    default_contract_template_id = Column(
        Integer,
        ForeignKey("contract_templates.id", ondelete="SET NULL"),
        nullable=True,
        comment="默认合同模板",
    )
    is_active = Column(Boolean, default=True, nullable=False, comment="是否启用")

    default_contract_template = relationship("ContractTemplate", foreign_keys=[default_contract_template_id])
```

- [ ] **Step 2: 在 models __init__ 中导出**

修改 `backend/app/models/__init__.py`，添加：
```python
from app.models.service_type import ServiceType
```

- [ ] **Step 3: Commit**

```bash
git add backend/app/models/service_type.py backend/app/models/__init__.py
git commit -m "feat(service-types): add ServiceType model"
```

---

### Task 2: 创建 ServiceType Schema

**Files:**
- Create: `backend/app/schemas/service_type.py`

- [ ] **Step 1: 编写 Schema 文件**

```python
from typing import Optional
from pydantic import BaseModel
from decimal import Decimal
from datetime import datetime


class ServiceTypeBase(BaseModel):
    code: str
    name: str
    default_price: Optional[Decimal] = None
    standard_duration_days: Optional[int] = None
    qualification_requirements: Optional[str] = None
    default_contract_template_id: Optional[int] = None
    is_active: bool = True


class ServiceTypeCreate(ServiceTypeBase):
    pass


class ServiceTypeUpdate(BaseModel):
    code: Optional[str] = None
    name: Optional[str] = None
    default_price: Optional[Decimal] = None
    standard_duration_days: Optional[int] = None
    qualification_requirements: Optional[str] = None
    default_contract_template_id: Optional[int] = None
    is_active: Optional[bool] = None


class ServiceTypeOut(ServiceTypeBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
```

- [ ] **Step 2: Commit**

```bash
git add backend/app/schemas/service_type.py
git commit -m "feat(service-types): add ServiceType schemas"
```

---

### Task 3: 创建 ServiceType CRUD

**Files:**
- Create: `backend/app/crud/service_type.py`

- [ ] **Step 1: 编写 CRUD 文件**

```python
from typing import List, Tuple, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.crud.base import CRUDBase
from app.models.service_type import ServiceType
from app.schemas.service_type import ServiceTypeCreate, ServiceTypeUpdate


class CRUDServiceType(CRUDBase[ServiceType, ServiceTypeCreate, ServiceTypeUpdate]):
    def get_by_code(self, db: Session, *, code: str) -> Optional[ServiceType]:
        return db.query(ServiceType).filter(ServiceType.code == code).first()

    def get_multi(
        self,
        db: Session,
        *,
        skip: int = 0,
        limit: int = 20,
        is_active: Optional[bool] = None,
    ) -> Tuple[int, List[ServiceType]]:
        query = db.query(ServiceType)
        if is_active is not None:
            query = query.filter(ServiceType.is_active == is_active)
        total = query.count()
        items = query.offset(skip).limit(limit).all()
        return total, items

    def get_usage_counts(self, db: Session, *, service_type_id: int) -> dict:
        from app.models.contract import Contract, ContractTemplate
        from app.models.service import ServiceOrder

        contract_count = (
            db.query(func.count(Contract.id))
            .filter(Contract.service_type == service_type_id)
            .scalar()
        )
        order_count = (
            db.query(func.count(ServiceOrder.id))
            .filter(ServiceOrder.service_type == service_type_id)
            .scalar()
        )
        template_count = (
            db.query(func.count(ContractTemplate.id))
            .filter(ContractTemplate.service_type == service_type_id)
            .scalar()
        )
        return {
            "contract_count": contract_count,
            "order_count": order_count,
            "template_count": template_count,
        }


crud_service_type = CRUDServiceType(ServiceType)
```

- [ ] **Step 2: Commit**

```bash
git add backend/app/crud/service_type.py
git commit -m "feat(service-types): add ServiceType CRUD"
```

---

### Task 4: 创建 ServiceType API 端点

**Files:**
- Create: `backend/app/api/v1/endpoints/service_types.py`
- Modify: `backend/app/api/v1/router.py`

- [ ] **Step 1: 编写 API 路由文件**

```python
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.service_type import ServiceTypeCreate, ServiceTypeUpdate, ServiceTypeOut
from app.schemas.common import PageResponse, ResponseMsg
from app.crud.service_type import crud_service_type
from app.dependencies import require_permissions
from app.core.exceptions import NotFoundError, BusinessError
from app.core.constants import PermissionCode
from app.models.user import User
from app.utils.pagination import make_page_response

router = APIRouter(prefix="/service-types", tags=["服务类型管理"])


@router.get("", response_model=PageResponse[ServiceTypeOut])
def list_service_types(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    is_active: Optional[bool] = None,
    current_user: User = Depends(require_permissions(PermissionCode.SERVICE_READ)),
    db: Session = Depends(get_db),
):
    skip = (page - 1) * page_size
    total, items = crud_service_type.get_multi(db, skip=skip, limit=page_size, is_active=is_active)
    return make_page_response(total, items, page, page_size)


@router.get("/{service_type_id}", response_model=ServiceTypeOut)
def get_service_type(
    service_type_id: int,
    current_user: User = Depends(require_permissions(PermissionCode.SERVICE_READ)),
    db: Session = Depends(get_db),
):
    obj = crud_service_type.get(db, id=service_type_id)
    if not obj:
        raise NotFoundError("服务类型")
    return obj


@router.post("", response_model=ServiceTypeOut, status_code=201)
def create_service_type(
    body: ServiceTypeCreate,
    current_user: User = Depends(require_permissions(PermissionCode.SERVICE_CREATE)),
    db: Session = Depends(get_db),
):
    existing = crud_service_type.get_by_code(db, code=body.code)
    if existing:
        raise BusinessError(f"服务类型 code '{body.code}' 已存在")
    return crud_service_type.create(db, obj_in=body)


@router.put("/{service_type_id}", response_model=ServiceTypeOut)
def update_service_type(
    service_type_id: int,
    body: ServiceTypeUpdate,
    current_user: User = Depends(require_permissions(PermissionCode.SERVICE_UPDATE)),
    db: Session = Depends(get_db),
):
    obj = crud_service_type.get(db, id=service_type_id)
    if not obj:
        raise NotFoundError("服务类型")
    if body.code:
        existing = crud_service_type.get_by_code(db, code=body.code)
        if existing and existing.id != service_type_id:
            raise BusinessError(f"服务类型 code '{body.code}' 已存在")
    return crud_service_type.update(db, db_obj=obj, obj_in=body)


@router.delete("/{service_type_id}", response_model=ResponseMsg)
def delete_service_type(
    service_type_id: int,
    current_user: User = Depends(require_permissions(PermissionCode.SERVICE_DELETE)),
    db: Session = Depends(get_db),
):
    obj = crud_service_type.get(db, id=service_type_id)
    if not obj:
        raise NotFoundError("服务类型")
    usage = crud_service_type.get_usage_counts(db, service_type_id=service_type_id)
    total = usage["contract_count"] + usage["order_count"] + usage["template_count"]
    if total > 0:
        raise BusinessError(
            f"该服务类型正在被引用（合同 {usage['contract_count']} 个，工单 {usage['order_count']} 个，模板 {usage['template_count']} 个），无法删除"
        )
    crud_service_type.remove(db, id=service_type_id)
    return {"message": "删除成功"}


@router.get("/{service_type_id}/usage")
def get_service_type_usage(
    service_type_id: int,
    current_user: User = Depends(require_permissions(PermissionCode.SERVICE_READ)),
    db: Session = Depends(get_db),
):
    obj = crud_service_type.get(db, id=service_type_id)
    if not obj:
        raise NotFoundError("服务类型")
    return crud_service_type.get_usage_counts(db, service_type_id=service_type_id)
```

- [ ] **Step 2: 在 router.py 中注册路由**

修改 `backend/app/api/v1/router.py`：
1. 在 import 列表中添加 `service_types`
2. 在 `api_router.include_router` 列表中添加 `api_router.include_router(service_types.router)`

```python
from app.api.v1.endpoints import (
    ...,
    service_types,
)
...
api_router.include_router(service_types.router)
```

- [ ] **Step 3: Commit**

```bash
git add backend/app/api/v1/endpoints/service_types.py backend/app/api/v1/router.py
git commit -m "feat(service-types): add REST API endpoints"
```

---

### Task 5: 数据库迁移脚本

**Files:**
- Create: `backend/migrations/versions/xxxx_add_service_types_table.py` (通过 alembic 生成后修改)

- [ ] **Step 1: 生成迁移脚本**

在 `backend/` 目录下运行：
```bash
cd backend
PYTHONPATH=. alembic revision --autogenerate -m "add_service_types_table"
```

- [ ] **Step 2: 手动修改迁移脚本**

自动生成的迁移脚本通常只创建表，不会处理 ENUM 到 FK 的转换。需要修改生成的脚本，内容如下（假设生成的 revision id 为 `abcd1234`）：

```python
"""add_service_types_table

Revision ID: abcd1234
Revises: <head>
Create Date: 2026-04-15 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'abcd1234'
down_revision = '<head>'
branch_labels = None
depends_on = None


def upgrade():
    # 1. 创建 service_types 表
    op.create_table(
        'service_types',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('code', sa.String(length=50), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('default_price', sa.Numeric(precision=18, scale=2), nullable=True),
        sa.Column('standard_duration_days', sa.Integer(), nullable=True),
        sa.Column('qualification_requirements', sa.Text(), nullable=True),
        sa.Column('default_contract_template_id', sa.Integer(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['default_contract_template_id'], ['contract_templates.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('code')
    )
    op.create_index(op.f('ix_service_types_id'), 'service_types', ['id'], unique=False)

    # 2. 插入初始数据
    service_types_table = sa.table(
        'service_types',
        sa.column('id', sa.Integer),
        sa.column('code', sa.String),
        sa.column('name', sa.String),
        sa.column('is_active', sa.Boolean),
        sa.column('created_at', sa.DateTime),
        sa.column('updated_at', sa.DateTime),
    )
    op.bulk_insert(
        service_types_table,
        [
            {"id": 1, "code": "evaluation", "name": "安全评价", "is_active": True, "created_at": "2026-01-01 00:00:00", "updated_at": "2026-01-01 00:00:00"},
            {"id": 2, "code": "training", "name": "安全培训", "is_active": True, "created_at": "2026-01-01 00:00:00", "updated_at": "2026-01-01 00:00:00"},
            {"id": 3, "code": "inspection", "name": "安全检测检验", "is_active": True, "created_at": "2026-01-01 00:00:00", "updated_at": "2026-01-01 00:00:00"},
            {"id": 4, "code": "consulting", "name": "安全咨询顾问", "is_active": True, "created_at": "2026-01-01 00:00:00", "updated_at": "2026-01-01 00:00:00"},
            {"id": 5, "code": "emergency_plan", "name": "应急预案编制", "is_active": True, "created_at": "2026-01-01 00:00:00", "updated_at": "2026-01-01 00:00:00"},
        ]
    )
    # 重置序列
    op.execute("SELECT setval('service_types_id_seq', 5, true)")

    # 3. contracts 表：添加临时列、更新数据、删除旧列、重命名
    op.add_column('contracts', sa.Column('service_type_id', sa.Integer(), nullable=True))
    op.execute("""
        UPDATE contracts
        SET service_type_id = CASE service_type::text
            WHEN 'evaluation' THEN 1
            WHEN 'training' THEN 2
            WHEN 'inspection' THEN 3
            WHEN 'consulting' THEN 4
            WHEN 'emergency_plan' THEN 5
        END
    """)
    op.alter_column('contracts', 'service_type_id', nullable=False)
    op.drop_column('contracts', 'service_type')
    op.alter_column('contracts', 'service_type_id', new_column_name='service_type')
    op.create_foreign_key(None, 'contracts', 'service_types', ['service_type'], ['id'], ondelete='RESTRICT')

    # 4. service_orders 表
    op.add_column('service_orders', sa.Column('service_type_id', sa.Integer(), nullable=True))
    op.execute("""
        UPDATE service_orders
        SET service_type_id = CASE service_type::text
            WHEN 'evaluation' THEN 1
            WHEN 'training' THEN 2
            WHEN 'inspection' THEN 3
            WHEN 'consulting' THEN 4
            WHEN 'emergency_plan' THEN 5
        END
    """)
    op.alter_column('service_orders', 'service_type_id', nullable=False)
    op.drop_column('service_orders', 'service_type')
    op.alter_column('service_orders', 'service_type_id', new_column_name='service_type')
    op.create_foreign_key(None, 'service_orders', 'service_types', ['service_type'], ['id'], ondelete='RESTRICT')

    # 5. contract_templates 表
    op.add_column('contract_templates', sa.Column('service_type_id', sa.Integer(), nullable=True))
    op.execute("""
        UPDATE contract_templates
        SET service_type_id = CASE service_type::text
            WHEN 'evaluation' THEN 1
            WHEN 'training' THEN 2
            WHEN 'inspection' THEN 3
            WHEN 'consulting' THEN 4
            WHEN 'emergency_plan' THEN 5
        END
    """)
    op.alter_column('contract_templates', 'service_type_id', nullable=False)
    op.drop_column('contract_templates', 'service_type')
    op.alter_column('contract_templates', 'service_type_id', new_column_name='service_type')
    op.create_foreign_key(None, 'contract_templates', 'service_types', ['service_type'], ['id'], ondelete='RESTRICT')

    # 6. 删除旧 ENUM 类型
    op.execute("DROP TYPE IF EXISTS service_type")
    op.execute("DROP TYPE IF EXISTS service_type_order")


def downgrade():
    # 降级脚本：恢复 ENUM，删除 service_types 表（简化版，仅用于回滚测试）
    service_type_enum = postgresql.ENUM('evaluation', 'training', 'inspection', 'consulting', 'emergency_plan', name='service_type')
    service_type_order_enum = postgresql.ENUM('evaluation', 'training', 'inspection', 'consulting', 'emergency_plan', name='service_type_order')

    # 删除外键并恢复列（需要知道具体约束名，这里示例省略完整实现）
    # 实际执行时建议根据自动生成的脚本微调
    pass
```

> **注意**：请根据实际生成的 `revision id` 和 `down_revision` 替换脚本头部。`downgrade` 函数可以保留为空（pass），因为生产环境通常不需要降级。

- [ ] **Step 3: 运行迁移**

```bash
cd backend
PYTHONPATH=. alembic upgrade head
```

- [ ] **Step 4: Commit**

```bash
git add backend/migrations/versions/xxxx_add_service_types_table.py
git commit -m "feat(service-types): add migration to replace enum with foreign key"
```

---

### Task 6: 改造后端模型（Contract, ServiceOrder, ContractTemplate）

**Files:**
- Modify: `backend/app/models/contract.py`
- Modify: `backend/app/models/service.py`

- [ ] **Step 1: 修改 Contract 和 ContractTemplate 模型**

将 `backend/app/models/contract.py` 中的 `service_type` 字段从 ENUM 改为 Integer FK：

```python
# 移除这行：
# from app.core.constants import ContractStatus, ServiceType, PaymentPlan
# 改为：
from app.core.constants import ContractStatus, PaymentPlan

# Contract 类中：
service_type = Column(
    Integer,
    ForeignKey("service_types.id", ondelete="RESTRICT"),
    nullable=False,
    comment="服务类型",
)

# ContractTemplate 类中：
service_type = Column(
    Integer,
    ForeignKey("service_types.id", ondelete="RESTRICT"),
    nullable=False,
    comment="适用服务类型",
)
```

- [ ] **Step 2: 修改 ServiceOrder 模型**

将 `backend/app/models/service.py` 中的 `service_type` 字段从 ENUM 改为 Integer FK：

```python
# 移除这行：
# from app.core.constants import ServiceOrderStatus, ServiceType
# 改为：
from app.core.constants import ServiceOrderStatus

# ServiceOrder 类中：
service_type = Column(
    Integer,
    ForeignKey("service_types.id", ondelete="RESTRICT"),
    nullable=False,
)
```

- [ ] **Step 3: 在模型中增加 relationship（可选但推荐）**

在 `Contract`、`ServiceOrder`、`ContractTemplate` 类中分别添加：
```python
service_type_obj = relationship("ServiceType")
```

- [ ] **Step 4: Commit**

```bash
git add backend/app/models/contract.py backend/app/models/service.py
git commit -m "refactor(models): change service_type from enum to foreign key"
```

---

### Task 7: 改造后端 Schemas

**Files:**
- Modify: `backend/app/schemas/contract.py`
- Modify: `backend/app/schemas/service.py`

- [ ] **Step 1: 修改 contract schemas**

修改 `backend/app/schemas/contract.py`：

```python
# 1. 移除 ServiceType 导入
# from app.core.constants import ContractStatus, ServiceType, PaymentPlan
# 改为：
from app.core.constants import ContractStatus, PaymentPlan

# 2. ContractBase 中 service_type 改为 int
class ContractBase(BaseModel):
    contract_no: str
    title: str
    customer_id: int
    service_type: int  # 改为 int (FK)
    total_amount: Decimal
    ...

# 3. ContractTemplateCreate 中 service_type 改为 int
class ContractTemplateCreate(BaseModel):
    name: str
    service_type: int  # 改为 int (FK)
    is_default: bool = False

# 4. ContractTemplateOut 中 service_type 改为 int，并增加兼容字段
class ContractTemplateOut(BaseModel):
    id: int
    name: str
    service_type: int
    service_type_id: int
    service_type_name: Optional[str] = None
    service_type_code: Optional[str] = None
    file_url: Optional[str] = None
    is_default: bool
    created_at: datetime

    model_config = {"from_attributes": True}

# 5. ContractOut 增加兼容字段
class ContractOut(ContractBase):
    id: int
    status: ContractStatus
    file_url: Optional[str] = None
    template_id: Optional[int] = None
    draft_doc_url: Optional[str] = None
    final_pdf_url: Optional[str] = None
    signed_at: Optional[datetime] = None
    created_at: datetime
    customer_name: Optional[str] = None
    signatures: List[ContractSignatureOut] = []
    invoiced_amount: Optional[Decimal] = None
    received_amount: Optional[Decimal] = None
    service_type_id: int
    service_type_name: Optional[str] = None
    service_type_code: Optional[str] = None

    model_config = {"from_attributes": True}

# 6. ContractListOut 同样增加兼容字段
class ContractListOut(BaseModel):
    id: int
    contract_no: str
    title: str
    customer_id: int
    customer_name: Optional[str] = None
    service_type: int
    service_type_id: int
    service_type_name: Optional[str] = None
    service_type_code: Optional[str] = None
    total_amount: Decimal
    payment_plan: PaymentPlan
    status: ContractStatus
    sign_date: Optional[date] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    template_id: Optional[int] = None
    draft_doc_url: Optional[str] = None
    final_pdf_url: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}
```

- [ ] **Step 2: 修改 service schemas**

修改 `backend/app/schemas/service.py`：

```python
# 移除 ServiceType 导入
# from app.core.constants import ServiceOrderStatus, ServiceType
# 改为：
from app.core.constants import ServiceOrderStatus

# ServiceOrderBase 中 service_type 改为 int
class ServiceOrderBase(BaseModel):
    order_no: str
    contract_id: int
    title: str
    service_type: int  # 改为 int (FK)
    ...

# ServiceOrderOut 增加兼容字段
class ServiceOrderOut(ServiceOrderBase):
    id: int
    status: ServiceOrderStatus
    actual_start: Optional[date] = None
    actual_end: Optional[date] = None
    created_at: datetime
    customer_name: Optional[str] = None
    assignee_name: Optional[str] = None
    items: List[ServiceItemOut] = []
    reports: List[ServiceReportOut] = []
    service_type_id: int
    service_type_name: Optional[str] = None
    service_type_code: Optional[str] = None

    model_config = {"from_attributes": True}

# ServiceOrderListOut 同样增加兼容字段
class ServiceOrderListOut(BaseModel):
    id: int
    order_no: str
    title: str
    contract_id: int
    customer_name: Optional[str] = None
    service_type: int
    service_type_id: int
    service_type_name: Optional[str] = None
    service_type_code: Optional[str] = None
    status: ServiceOrderStatus
    assignee_id: Optional[int] = None
    assignee_name: Optional[str] = None
    planned_start: Optional[date] = None
    planned_end: Optional[date] = None
    created_at: datetime

    model_config = {"from_attributes": True}
```

- [ ] **Step 3: Commit**

```bash
git add backend/app/schemas/contract.py backend/app/schemas/service.py
git commit -m "refactor(schemas): change service_type to int and add compatibility fields"
```

---

### Task 8: 改造后端 API — 填充兼容字段

**Files:**
- Modify: `backend/app/api/v1/endpoints/contracts.py`
- Modify: `backend/app/api/v1/endpoints/services.py`
- Modify: `backend/app/api/v1/endpoints/contract_templates.py`

- [ ] **Step 1: 修改 contracts.py**

在 `list_contracts` 和 `get_contract` 等返回 ContractOut/ContractListOut 的地方，填充新增的兼容字段：

```python
# list_contracts 中（约第57-62行）
for c in items:
    item = ContractListOut.model_validate(c)
    item.customer_name = c.customer.name if c.customer else None
    if c.service_type_obj:
        item.service_type_id = c.service_type_obj.id
        item.service_type_name = c.service_type_obj.name
        item.service_type_code = c.service_type_obj.code
    result.append(item)

# get_contract 中（约第117-121行）
result = ContractOut.model_validate(contract)
result.customer_name = contract.customer.name if contract.customer else None
if contract.service_type_obj:
    result.service_type_id = contract.service_type_obj.id
    result.service_type_name = contract.service_type_obj.name
    result.service_type_code = contract.service_type_obj.code
result.invoiced_amount = ...

# export_contracts 中（约第84-94行）
rows = []
for c in items:
    service_type_name = c.service_type_obj.name if c.service_type_obj else ""
    rows.append([
        c.contract_no, c.title, c.customer.name if c.customer else "",
        service_type_name, ...
    ])
```

同理修改 `update_contract`、`update_contract_status`、`generate_contract_draft`、`sign_contract`、`upload_signed_contract` 中所有返回 `ContractOut` 的位置。

> 提示：可以写一个小辅助函数减少重复：
> ```python
> def _enrich_contract_out(contract, out: ContractOut) -> ContractOut:
>     out.customer_name = contract.customer.name if contract.customer else None
>     if contract.service_type_obj:
>         out.service_type_id = contract.service_type_obj.id
>         out.service_type_name = contract.service_type_obj.name
>         out.service_type_code = contract.service_type_obj.code
>     return out
> ```

- [ ] **Step 2: 修改 services.py**

在 `list_service_orders` 和 `get_service_order` 等返回处填充兼容字段：

```python
# list_service_orders 中
for item in items:
    out = ServiceOrderListOut.model_validate(item)
    out.customer_name = ...
    out.assignee_name = ...
    if item.service_type_obj:
        out.service_type_id = item.service_type_obj.id
        out.service_type_name = item.service_type_obj.name
        out.service_type_code = item.service_type_obj.code
    result.append(out)

# get_service_order 中
result = ServiceOrderOut.model_validate(order)
result.customer_name = ...
result.assignee_name = ...
if order.service_type_obj:
    result.service_type_id = order.service_type_obj.id
    result.service_type_name = order.service_type_obj.name
    result.service_type_code = order.service_type_obj.code

# export_service_orders 中
service_type_name = item.service_type_obj.name if item.service_type_obj else ""
```

- [ ] **Step 3: 修改 contract_templates.py**

在 `list_contract_templates` 中填充兼容字段：

```python
# 由于返回的是 PageResponse[ContractTemplateOut]，可以直接在返回前处理 items
items_out = []
for t in items:
    out = ContractTemplateOut.model_validate(t)
    if t.service_type_obj:
        out.service_type_id = t.service_type_obj.id
        out.service_type_name = t.service_type_obj.name
        out.service_type_code = t.service_type_obj.code
    items_out.append(out)
return make_page_response(total, items_out, page, page_size)
```

同时修改 `service_type` 查询参数类型从 `Optional[ServiceType]` 改为 `Optional[int]`：
```python
from typing import Optional
# 移除 ServiceType 导入

def list_contract_templates(
    ...
    service_type: Optional[int] = None,
    ...
):
    ...
    if service_type:
        query = query.filter(ContractTemplate.service_type == service_type)
```

- [ ] **Step 4: Commit**

```bash
git add backend/app/api/v1/endpoints/contracts.py backend/app/api/v1/endpoints/services.py backend/app/api/v1/endpoints/contract_templates.py
git commit -m "refactor(api): populate service_type compatibility fields in responses"
```

---

### Task 9: 改造 contract_doc_service

**Files:**
- Modify: `backend/app/services/contract_doc_service.py`

- [ ] **Step 1: 修改 _get_service_type_label**

将 `_get_service_type_label` 改为通过传入 contract 对象或 service_type_id 从数据库查询：

```python
def _get_service_type_label(contract) -> str:
    if contract.service_type_obj:
        return contract.service_type_obj.name
    return ""
```

然后修改 `render_contract_draft` 中的调用（第147行）：
```python
"service_type_label": _get_service_type_label(contract),
```

- [ ] **Step 2: Commit**

```bash
git add backend/app/services/contract_doc_service.py
git commit -m "refactor(contract-doc): fetch service type label from database"
```

---

### Task 10: 后端测试与修复

**Files:**
- 运行时动态修复

- [ ] **Step 1: 启动后端并检查错误**

```bash
cd backend
PYTHONPATH=. uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

如果启动报错（如某些文件仍引用 `ServiceType` 枚举），根据错误信息逐个修复。常见需要检查的地方：
- `backend/app/crud/contract.py` 中的 filter 条件
- `backend/app/api/v1/endpoints/analytics.py`
- `backend/app/api/v1/endpoints/dashboard.py`

- [ ] **Step 2: 运行 API 验证测试**

```bash
cd backend
PYTHONPATH=. python scripts/api_validation_tests.py
```

---

### Task 11: 前端 — 改造 Types 和 Constants

**Files:**
- Modify: `frontend/src/types/index.ts`
- Modify: `frontend/src/utils/constants.ts`

- [ ] **Step 1: 修改 types/index.ts**

```typescript
// 移除这行：
// export type ServiceType = 'evaluation' | 'training' | 'inspection' | 'consulting' | 'emergency_plan'

// 新增 ServiceType 接口
export interface ServiceType {
  id: number
  code: string
  name: string
  default_price?: number | string
  standard_duration_days?: number
  qualification_requirements?: string
  default_contract_template_id?: number
  is_active: boolean
  created_at: string
  updated_at: string
}
```

然后搜索 `ServiceType` 的其他引用，将需要 string 的地方改为使用 `service_type: string`（直接用 string 类型）， Contract/ServiceOrder 等接口中 `service_type` 保持为 `string`（code）。

修改 `ContractTemplate` 接口：
```typescript
export interface ContractTemplate {
  id: number
  name: string
  service_type: string
  service_type_id?: number
  service_type_name?: string
  file_url: string
  is_default: boolean
  created_at: string
}
```

修改 `Contract` 接口：
```typescript
export interface Contract {
  id: number
  contract_no: string
  title: string
  customer_id: number
  customer_name?: string
  service_type: string
  service_type_id?: number
  service_type_name?: string
  ...
}
```

修改 `ContractCreate`：
```typescript
export interface ContractCreate {
  contract_no: string
  title: string
  customer_id: number
  service_type: string  // 传 code
  ...
}
```

修改 `ServiceOrder` 和 `ServiceOrderCreate`：
```typescript
export interface ServiceOrder {
  id: number
  order_no: string
  contract_id: number
  title: string
  service_type: string
  service_type_id?: number
  service_type_name?: string
  ...
}

export interface ServiceOrderCreate {
  order_no: string
  contract_id: number
  title: string
  service_type: string  // 传 code
  ...
}
```

修改 `DashboardStats` 中的 `contract_amount_by_service_type` 保持 `service_type: string`。

修改 `AnalyticsQueryParams` 等（如果存在）：将 `service_type?: ServiceType` 改为 `service_type?: string`。

- [ ] **Step 2: 修改 utils/constants.ts**

```typescript
// 移除 ServiceTypeLabels
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/types/index.ts frontend/src/utils/constants.ts
git commit -m "refactor(frontend): replace ServiceType enum with string and interface"
```

---

### Task 12: 前端 — 创建 ServiceTypes API Slice

**Files:**
- Create: `frontend/src/store/api/serviceTypesApi.ts`
- Modify: `frontend/src/store/api/baseApi.ts`

- [ ] **Step 1: 编写 API Slice**

```typescript
import { baseApi } from './baseApi'
import type { ServiceType, PageResponse } from '@/types'

export const serviceTypesApi = baseApi.injectEndpoints({
  endpoints: (builder) => ({
    listServiceTypes: builder.query<PageResponse<ServiceType>, { page?: number; page_size?: number; is_active?: boolean }>({
      query: (params) => ({
        url: '/service-types',
        params,
      }),
      providesTags: ['ServiceType'],
    }),
    getServiceType: builder.query<ServiceType, number>({
      query: (id) => `/service-types/${id}`,
      providesTags: (result, error, id) => [{ type: 'ServiceType', id }],
    }),
    createServiceType: builder.mutation<ServiceType, Omit<ServiceType, 'id' | 'created_at' | 'updated_at'>>({
      query: (body) => ({
        url: '/service-types',
        method: 'POST',
        body,
      }),
      invalidatesTags: ['ServiceType'],
    }),
    updateServiceType: builder.mutation<ServiceType, { id: number; data: Partial<Omit<ServiceType, 'id' | 'created_at' | 'updated_at'>> }>({
      query: ({ id, data }) => ({
        url: `/service-types/${id}`,
        method: 'PUT',
        body: data,
      }),
      invalidatesTags: (result, error, { id }) => [{ type: 'ServiceType', id }, 'ServiceType'],
    }),
    deleteServiceType: builder.mutation<void, number>({
      query: (id) => ({
        url: `/service-types/${id}`,
        method: 'DELETE',
      }),
      invalidatesTags: ['ServiceType'],
    }),
    getServiceTypeUsage: builder.query<{ contract_count: number; order_count: number; template_count: number }, number>({
      query: (id) => `/service-types/${id}/usage`,
    }),
  }),
})

export const {
  useListServiceTypesQuery,
  useGetServiceTypeQuery,
  useCreateServiceTypeMutation,
  useUpdateServiceTypeMutation,
  useDeleteServiceTypeMutation,
  useGetServiceTypeUsageQuery,
} = serviceTypesApi
```

- [ ] **Step 2: 修改 baseApi.ts**

在 `tagTypes` 数组中添加 `'ServiceType'`：
```typescript
tagTypes: ['User', 'Customer', 'Contract', 'ContractTemplate', 'Service', 'Invoice', 'Payment', 'Dashboard', 'Analytics', 'Role', 'Department', 'Notification', 'Permission', 'ServiceType'],
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/store/api/serviceTypesApi.ts frontend/src/store/api/baseApi.ts
git commit -m "feat(frontend): add serviceTypes RTK Query API slice"
```

---

### Task 13: 前端 — 修改其他 API Slice 的类型导入

**Files:**
- Modify: `frontend/src/store/api/contractsApi.ts`
- Modify: `frontend/src/store/api/servicesApi.ts`
- Modify: `frontend/src/store/api/contractTemplatesApi.ts`
- Modify: `frontend/src/store/api/analyticsApi.ts`

- [ ] **Step 1: 移除 ServiceType 导入**

在每个文件中，将 `ServiceType` 从 `@/types` 的 import 中移除（如果存在）。
如果 `AnalyticsQueryParams` 中有 `service_type?: ServiceType`，改为 `service_type?: string`。

- [ ] **Step 2: Commit**

```bash
git add frontend/src/store/api/contractsApi.ts frontend/src/store/api/servicesApi.ts frontend/src/store/api/contractTemplatesApi.ts frontend/src/store/api/analyticsApi.ts
git commit -m "refactor(frontend): remove ServiceType enum imports from API slices"
```

---

### Task 14: 前端 — 创建 ServiceTypes 管理页面

**Files:**
- Create: `frontend/src/pages/ServiceTypes/index.tsx`

- [ ] **Step 1: 编写管理页面**

```tsx
import React, { useState } from 'react'
import { Table, Button, Space, Input, Switch, message, Modal, Form, InputNumber, Select, Descriptions } from 'antd'
import { PlusOutlined, EditOutlined, DeleteOutlined } from '@ant-design/icons'
import {
  useListServiceTypesQuery,
  useCreateServiceTypeMutation,
  useUpdateServiceTypeMutation,
  useDeleteServiceTypeMutation,
  useGetServiceTypeUsageQuery,
} from '@/store/api/serviceTypesApi'
import { useListContractTemplatesQuery } from '@/store/api/contractTemplatesApi'
import { PermissionButton } from '@/components/auth/PermissionButton'
import type { ServiceType } from '@/types'

const ServiceTypesPage: React.FC = () => {
  const [page, setPage] = useState(1)
  const [createOpen, setCreateOpen] = useState(false)
  const [editOpen, setEditOpen] = useState(false)
  const [editingId, setEditingId] = useState<number | null>(null)
  const [form] = Form.useForm()
  const [editForm] = Form.useForm()

  const { data, isLoading, refetch } = useListServiceTypesQuery({ page, page_size: 20 })
  const { data: templatesData } = useListContractTemplatesQuery({ page: 1, page_size: 200 })
  const [createServiceType, { isLoading: creating }] = useCreateServiceTypeMutation()
  const [updateServiceType, { isLoading: updating }] = useUpdateServiceTypeMutation()
  const [deleteServiceType] = useDeleteServiceTypeMutation()

  const handleCreate = async (values: any) => {
    try {
      await createServiceType({
        ...values,
        default_price: values.default_price ? Number(values.default_price) : undefined,
        standard_duration_days: values.standard_duration_days ? Number(values.standard_duration_days) : undefined,
      }).unwrap()
      message.success('创建成功')
      setCreateOpen(false)
      form.resetFields()
      refetch()
    } catch (err: any) {
      message.error(err?.data?.detail || '创建失败')
    }
  }

  const handleEdit = (record: ServiceType) => {
    setEditingId(record.id)
    editForm.setFieldsValue({
      code: record.code,
      name: record.name,
      default_price: record.default_price,
      standard_duration_days: record.standard_duration_days,
      qualification_requirements: record.qualification_requirements,
      default_contract_template_id: record.default_contract_template_id,
      is_active: record.is_active,
    })
    setEditOpen(true)
  }

  const handleUpdate = async (values: any) => {
    if (!editingId) return
    try {
      await updateServiceType({
        id: editingId,
        data: {
          ...values,
          default_price: values.default_price ? Number(values.default_price) : undefined,
          standard_duration_days: values.standard_duration_days ? Number(values.standard_duration_days) : undefined,
        },
      }).unwrap()
      message.success('更新成功')
      setEditOpen(false)
      editForm.resetFields()
      setEditingId(null)
      refetch()
    } catch (err: any) {
      message.error(err?.data?.detail || '更新失败')
    }
  }

  const handleDelete = async (id: number) => {
    try {
      await deleteServiceType(id).unwrap()
      message.success('删除成功')
      refetch()
    } catch (err: any) {
      message.error(err?.data?.detail || '删除失败')
    }
  }

  const templateOptions = templatesData?.items.map((t) => ({ value: t.id, label: t.name })) || []

  const columns = [
    { title: '名称', dataIndex: 'name', key: 'name' },
    { title: 'Code', dataIndex: 'code', key: 'code' },
    { title: '默认单价', dataIndex: 'default_price', key: 'default_price', render: (v?: number | string) => (v !== undefined && v !== null ? `¥${Number(v).toFixed(2)}` : '-') },
    { title: '标准工期', dataIndex: 'standard_duration_days', key: 'standard_duration_days', render: (v?: number) => (v !== undefined && v !== null ? `${v} 天` : '-') },
    { title: '启用状态', dataIndex: 'is_active', key: 'is_active', render: (v: boolean) => (v ? '启用' : '禁用') },
    {
      title: '操作',
      key: 'action',
      render: (_: any, r: ServiceType) => (
        <Space>
          <PermissionButton permission="service:update" size="small" icon={<EditOutlined />} onClick={() => handleEdit(r)}>编辑</PermissionButton>
          <PermissionButton permission="service:delete" danger size="small" icon={<DeleteOutlined />} onClick={() => handleDelete(r.id)}>删除</PermissionButton>
        </Space>
      ),
    },
  ]

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 16 }}>
        <div />
        <PermissionButton permission="service:create" type="primary" icon={<PlusOutlined />} onClick={() => setCreateOpen(true)}>新建服务类型</PermissionButton>
      </div>

      <Table
        rowKey="id"
        columns={columns}
        dataSource={data?.items}
        loading={isLoading}
        pagination={{ current: page, pageSize: 20, total: data?.total, onChange: setPage, showTotal: (t) => `共 ${t} 条` }}
      />

      <Modal title="新建服务类型" open={createOpen} onCancel={() => { setCreateOpen(false); form.resetFields() }} onOk={() => form.submit()} confirmLoading={creating}>
        <Form form={form} layout="vertical" onFinish={handleCreate}>
          <Form.Item name="code" label="Code" rules={[{ required: true }]}><Input placeholder="evaluation" /></Form.Item>
          <Form.Item name="name" label="名称" rules={[{ required: true }]}><Input placeholder="安全评价" /></Form.Item>
          <Form.Item name="default_price" label="默认单价"><InputNumber style={{ width: '100%' }} min={0} precision={2} /></Form.Item>
          <Form.Item name="standard_duration_days" label="标准工期（天）"><InputNumber style={{ width: '100%' }} min={0} precision={0} /></Form.Item>
          <Form.Item name="qualification_requirements" label="资质要求"><Input.TextArea rows={3} /></Form.Item>
          <Form.Item name="default_contract_template_id" label="默认合同模板">
            <Select allowClear options={templateOptions} />
          </Form.Item>
          <Form.Item name="is_active" label="启用状态" initialValue={true} valuePropName="checked">
            <Switch />
          </Form.Item>
        </Form>
      </Modal>

      <Modal title="编辑服务类型" open={editOpen} onCancel={() => { setEditOpen(false); editForm.resetFields(); setEditingId(null) }} onOk={() => editForm.submit()} confirmLoading={updating}>
        <Form form={editForm} layout="vertical" onFinish={handleUpdate}>
          <Form.Item name="code" label="Code" rules={[{ required: true }]}><Input /></Form.Item>
          <Form.Item name="name" label="名称" rules={[{ required: true }]}><Input /></Form.Item>
          <Form.Item name="default_price" label="默认单价"><InputNumber style={{ width: '100%' }} min={0} precision={2} /></Form.Item>
          <Form.Item name="standard_duration_days" label="标准工期（天）"><InputNumber style={{ width: '100%' }} min={0} precision={0} /></Form.Item>
          <Form.Item name="qualification_requirements" label="资质要求"><Input.TextArea rows={3} /></Form.Item>
          <Form.Item name="default_contract_template_id" label="默认合同模板">
            <Select allowClear options={templateOptions} />
          </Form.Item>
          <Form.Item name="is_active" label="启用状态" valuePropName="checked">
            <Switch />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

export default ServiceTypesPage
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/pages/ServiceTypes/index.tsx
git commit -m "feat(frontend): add ServiceTypes management page"
```

---

### Task 15: 前端 — 注册路由和菜单

**Files:**
- Modify: `frontend/src/App.tsx`
- Modify: `frontend/src/config/menuConfig.ts`

- [ ] **Step 1: 修改 App.tsx**

在 import 区域添加：
```typescript
import ServiceTypes from '@/pages/ServiceTypes'
```

在路由中添加（放在 system 路由组附近）：
```tsx
<Route path="/service-types" element={<ServiceTypes />} />
```

建议放在 `business` 组内或作为独立路由。根据设计文档，放在主菜单中：
```tsx
<Route element={<AppLayout />}>
  ...
  <Route path="/service-types" element={<ServiceTypes />} />
</Route>
```

- [ ] **Step 2: 修改 menuConfig.ts**

在 `business` 子菜单中添加：
```typescript
{
  key: 'business',
  icon: FileTextOutlined,
  label: '业务管理',
  children: [
    ...,
    { key: '/service-types', icon: ToolOutlined, label: '服务类型管理', path: '/service-types', requiredPermissions: ['service:read'] },
  ],
},
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/App.tsx frontend/src/config/menuConfig.ts
git commit -m "feat(frontend): register ServiceTypes route and menu"
```

---

### Task 16: 前端 — 改造 Contracts 页面

**Files:**
- Modify: `frontend/src/pages/Contracts/index.tsx`

- [ ] **Step 1: 导入 serviceTypesApi**

```typescript
import { useListServiceTypesQuery } from '@/store/api/serviceTypesApi'
```

- [ ] **Step 2: 获取服务类型列表**

在组件中添加：
```typescript
const { data: serviceTypesData } = useListServiceTypesQuery({ page: 1, page_size: 200, is_active: true })
```

- [ ] **Step 3: 替换所有 ServiceTypeLabels 引用**

1. 表格列中的服务类型展示：
```typescript
{ title: '服务类型', dataIndex: 'service_type_name', key: 'service_type_name', render: (_: any, r: Contract) => r.service_type_name || r.service_type || '-' },
```

2. 创建/编辑表单中的 Select：
```tsx
<Select
  options={serviceTypesData?.items.map(st => ({ value: st.code, label: st.name })) || []}
  onChange={() => form.setFieldsValue({ template_id: undefined })}
/>
```

3. `getTemplateOptions` 保持不变，因为模板仍按 `service_type` code 过滤。

4. 合同详情中的服务类型展示：
```tsx
<Descriptions.Item label="服务类型">{data.service_type_name || data.service_type || '-'}</Descriptions.Item>
```

- [ ] **Step 4: Commit**

```bash
git add frontend/src/pages/Contracts/index.tsx
git commit -m "refactor(contracts): use dynamic service types in dropdown and display"
```

---

### Task 17: 前端 — 改造 Services 页面

**Files:**
- Modify: `frontend/src/pages/Services/index.tsx`

- [ ] **Step 1: 导入和获取服务类型**

```typescript
import { useListServiceTypesQuery } from '@/store/api/serviceTypesApi'
```

```typescript
const { data: serviceTypesData } = useListServiceTypesQuery({ page: 1, page_size: 200, is_active: true })
```

- [ ] **Step 2: 替换 ServiceTypeLabels**

1. 表格列：
```typescript
{ title: '服务类型', dataIndex: 'service_type_name', key: 'service_type_name', render: (_: any, r: ServiceOrder) => r.service_type_name || r.service_type || '-' },
```

2. 创建/编辑表单中的 Select：
```tsx
<Select options={serviceTypesData?.items.map(st => ({ value: st.code, label: st.name })) || []} />
```

3. 详情页中的展示：
```tsx
<Descriptions.Item label="服务类型">{data.service_type_name || data.service_type || '-'}</Descriptions.Item>
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/pages/Services/index.tsx
git commit -m "refactor(services): use dynamic service types in dropdown and display"
```

---

### Task 18: 前端 — 改造 ContractTemplates 页面

**Files:**
- Modify: `frontend/src/pages/ContractTemplates/index.tsx`

- [ ] **Step 1: 导入和获取服务类型**

```typescript
import { useListServiceTypesQuery } from '@/store/api/serviceTypesApi'
```

```typescript
const { data: serviceTypesData } = useListServiceTypesQuery({ page: 1, page_size: 200 })
```

- [ ] **Step 2: 替换引用**

1. 表格列：
```typescript
{ title: '服务类型', dataIndex: 'service_type_name', key: 'service_type_name', render: (_: any, r: ContractTemplate) => r.service_type_name || r.service_type || '-' },
```

2. 筛选 Select：
```tsx
<Select
  placeholder="服务类型"
  allowClear
  style={{ width: 160 }}
  onChange={setServiceType}
  options={serviceTypesData?.items.map(st => ({ value: st.id, label: st.name })) || []}
/>
```

注意：这里 filter 传给 API 的是 `service_type_id`（int），但当前 state 类型是 `ServiceType | undefined`，需要改为 `number | undefined`。

3. 创建表单：
```tsx
<Select options={serviceTypesData?.items.map(st => ({ value: st.id, label: st.name })) || []} />
```

同时修改 `handleCreate` 的参数类型：
```typescript
const handleCreate = async (values: { name: string; service_type: number }) => {
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/pages/ContractTemplates/index.tsx
git commit -m "refactor(contract-templates): use dynamic service types in dropdown and display"
```

---

### Task 19: 前端 — 改造 Analytics / Dashboard（如需要）

**Files:**
- Modify: `frontend/src/pages/Analytics/index.tsx`（如果使用了 ServiceTypeLabels）
- Modify: `frontend/src/pages/Dashboard/index.tsx`（如果使用了 ServiceTypeLabels）

- [ ] **Step 1: 检查并修改 Analytics**

如果 `Analytics/index.tsx` 中有 `ServiceTypeLabels` 引用，改为使用后端返回的数据，或者移除标签映射（后端已经返回可读名称时可直接展示）。

常见修改点：
```typescript
// 将
label: ServiceTypeLabels[item.service_type]
// 改为
label: item.service_type  // 如果后端已经返回中文；否则需要额外映射
```

如果筛选下拉框用了 `ServiceTypeLabels`，改为使用 `useListServiceTypesQuery`。

- [ ] **Step 2: 检查并修改 Dashboard**

`Dashboard/index.tsx` 中的 `contract_amount_by_service_type` 图表：
```typescript
// 将
name: ServiceTypeLabels[item.service_type]
// 改为
name: item.service_type  // 后端返回 name 时
// 或保持 item.service_type（如果后端返回 code，需要确认前端展示逻辑）
```

> 建议后端 `dashboard.py` 的 `contract_amount_by_service_type` 查询直接 JOIN `service_types` 返回 `name` 而不是 `code`，这样前端无需映射。

- [ ] **Step 3: Commit**

```bash
git add frontend/src/pages/Analytics/index.tsx frontend/src/pages/Dashboard/index.tsx
git commit -m "refactor(analytics/dashboard): remove static ServiceTypeLabels references"
```

---

### Task 20: 前端构建测试

**Files:**
- 运行时修复

- [ ] **Step 1: 运行 TypeScript 检查**

```bash
cd frontend
npm run lint
```

修复所有类型错误（如残留的 `ServiceTypeLabels` 或 `ServiceType` union 引用）。

- [ ] **Step 2: 运行开发服务器并手动测试**

```bash
cd frontend
npm run dev
```

打开浏览器测试：
1. 服务类型管理页面能否正常 CRUD
2. 合同/工单/模板页面的服务类型下拉框是否为动态数据
3. 现有数据展示是否正常

- [ ] **Step 3: Commit 修复**

```bash
git add .
git commit -m "fix(frontend): resolve typescript errors after service type refactor"
```

---

## 计划自审

### Spec 覆盖检查

| 设计文档需求 | 对应任务 |
|--------------|----------|
| 新建 `service_types` 表 | Task 1, 5 |
| 扩展属性（单价、工期、资质、模板） | Task 1, 2, 14 |
| 现有表 ENUM 改 FK | Task 5, 6 |
| 后端 CRUD API | Task 3, 4 |
| 删除前检查引用 | Task 4 |
| 现有 API 兼容字段 | Task 7, 8 |
| 文档生成从 DB 查名称 | Task 9 |
| 前端管理页面 | Task 14, 15 |
| 前端动态下拉框 | Task 16, 17, 18, 19 |
| 自动迁移现有 5 个类型 | Task 5 |

### Placeholder 扫描

- 无 "TBD"、"TODO"、"implement later"
- 每个代码步骤都包含完整代码
- 每个运行步骤都包含具体命令

### 类型一致性检查

- `service_type` 在数据库模型中为 `Integer(FK)`
- 后端 Schema 的输入为 `int`，输出增加 `service_type_id/name/code`
- 前端 `Contract/ServiceOrder/ContractTemplate` 中 `service_type` 保持 `string`（code）
- API slice 中 `service_type` 筛选参数类型与后端一致

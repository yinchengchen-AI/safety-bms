# 固定标准合同模板功能实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在合同提交审核时，自动根据默认 Word 模板生成标准合同草稿并存储到 MinIO，前端详情页提供下载入口。

**Architecture:** 后端复用 `contract_doc_service.py`，新增 `number_to_chinese_upper` 和 `render_standard_contract_draft`；在 `update_contract_status` 中当 `template_id is None` 时自动触发渲染；前端在 `ContractDetail` 中新增下载区域。

**Tech Stack:** FastAPI, SQLAlchemy, Alembic, docxtpl, MinIO, React + TypeScript + RTK Query, Ant Design

---

## 文件映射

| 文件 | 职责 |
|------|------|
| `backend/requirements.txt` | 添加 `docxtpl` 和 `python-docx` 依赖 |
| `backend/app/models/contract.py` | 为 `Contract` 模型新增 `standard_doc_url` 字段 |
| `backend/migrations/versions/` | Alembic 迁移文件，添加 `standard_doc_url` 列 |
| `backend/app/schemas/contract.py` | 在 `ContractOut` / `ContractListOut` 中暴露 `standard_doc_url` |
| `backend/app/services/contract_doc_service.py` | 实现金额大写转换、上下文构建、标准合同渲染 |
| `backend/app/api/v1/endpoints/contracts.py` | 在提交审核时 Hook 自动渲染，并在 GET 详情时生成预签名 URL |
| `backend/scripts/seed_default_contract_template.py` | 将预置模板上传到 MinIO 并创建默认 `ContractTemplate` 记录 |
| `frontend/src/types/index.ts` | `Contract` 类型新增 `standard_doc_url` |
| `frontend/src/pages/Contracts/index.tsx` | 详情页新增下载入口，提交审核按钮添加成功提示 |
| `backend/tests/test_contract_doc_service.py` | `number_to_chinese_upper` 单元测试 |
| `backend/tests/test_contract_standard_template.py` | `render_standard_contract_draft` 集成测试 |

---

### Task 1: 添加 Python 依赖

**Files:**
- Modify: `backend/requirements.txt`

- [ ] **Step 1: 在 requirements.txt 末尾追加两行**

```text
docxtpl==0.16.8
python-docx==1.1.2
```

- [ ] **Step 2: 安装依赖**

Run: `cd backend && pip install -r requirements.txt`
Expected: Successfully installed docxtpl-0.16.8 python-docx-1.1.2

- [ ] **Step 3: Commit**

```bash
git add backend/requirements.txt
git commit -m "deps: add docxtpl and python-docx for contract template rendering"
```

### Task 2: 更新 Contract 模型

**Files:**
- Modify: `backend/app/models/contract.py`

- [ ] **Step 1: 在 Contract 模型 `final_pdf_url` 下方添加 `standard_doc_url` 字段**

修改前（`backend/app/models/contract.py:39-42`）：
```python
    draft_doc_url = Column(String(500), comment="待签文档 MinIO 路径")
    final_pdf_url = Column(String(500), comment="最终PDF MinIO 路径")
    signed_at = Column(DateTime(timezone=True), comment="签订时间")
```

修改后：
```python
    draft_doc_url = Column(String(500), comment="待签文档 MinIO 路径")
    final_pdf_url = Column(String(500), comment="最终PDF MinIO 路径")
    standard_doc_url = Column(String(500), comment="标准合同草稿 MinIO 路径")
    signed_at = Column(DateTime(timezone=True), comment="签订时间")
```

- [ ] **Step 2: Commit**

```bash
git add backend/app/models/contract.py
git commit -m "feat(contract): add standard_doc_url column"
```

### Task 3: 创建 Alembic 迁移

**Files:**
- Create: `backend/migrations/versions/` (auto-generated file)

- [ ] **Step 1: 生成迁移文件**

Run: `cd backend && alembic revision --autogenerate -m "add contract standard_doc_url"`
Expected: 在 `backend/migrations/versions/` 下生成新文件，如 `20260415_xxxx_add_contract_standard_doc_url.py`

- [ ] **Step 2: 检查迁移文件内容**

Read the generated file. Expected `upgrade()` to contain:
```python
op.add_column('contracts', sa.Column('standard_doc_url', sa.String(length=500), nullable=True))
```
And `downgrade()` to contain:
```python
op.drop_column('contracts', 'standard_doc_url')
```

- [ ] **Step 3: 运行迁移**

Run: `cd backend && alembic upgrade head`
Expected:
```
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO  [alembic.runtime.migration] Will assume transactional DDL.
```

- [ ] **Step 4: Commit**

```bash
git add backend/migrations/versions/
git commit -m "feat(contract): migration for standard_doc_url"
```

### Task 4: 更新 Pydantic Schemas

**Files:**
- Modify: `backend/app/schemas/contract.py`

- [ ] **Step 1: 在 `ContractOut` 中添加 `standard_doc_url`**

修改前（`backend/app/schemas/contract.py:124-128`）：
```python
    template_id: Optional[int] = None
    draft_doc_url: Optional[str] = None
    final_pdf_url: Optional[str] = None
    signed_at: Optional[datetime] = None
```

修改后：
```python
    template_id: Optional[int] = None
    draft_doc_url: Optional[str] = None
    final_pdf_url: Optional[str] = None
    standard_doc_url: Optional[str] = None
    signed_at: Optional[datetime] = None
```

- [ ] **Step 2: 在 `ContractListOut` 中添加 `standard_doc_url`**

修改前（`backend/app/schemas/contract.py:157-160`）：
```python
    template_id: Optional[int] = None
    draft_doc_url: Optional[str] = None
    final_pdf_url: Optional[str] = None
    created_at: datetime
```

修改后：
```python
    template_id: Optional[int] = None
    draft_doc_url: Optional[str] = None
    final_pdf_url: Optional[str] = None
    standard_doc_url: Optional[str] = None
    created_at: datetime
```

- [ ] **Step 3: Commit**

```bash
git add backend/app/schemas/contract.py
git commit -m "feat(contract): add standard_doc_url to schemas"
```

### Task 5: 实现金额大写与标准合同渲染

**Files:**
- Modify: `backend/app/services/contract_doc_service.py`

- [ ] **Step 1: 在文件顶部导入 `ContractTemplate` 和 `logging`**

在现有导入之后添加：
```python
import logging
from app.models.contract import ContractTemplate
```

- [ ] **Step 2: 在文件末尾追加 `number_to_chinese_upper` 函数**

```python
def number_to_chinese_upper(amount) -> str:
    from decimal import Decimal, ROUND_HALF_UP

    amount = Decimal(str(amount)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    integer_part = int(amount)
    decimal_part = int((amount - integer_part) * 100)

    nums = "零壹贰叁肆伍陆柒捌玖"
    units = ["", "拾", "佰", "仟"]

    def _four_digit_to_chinese(n: int) -> str:
        if n == 0:
            return "零"
        s = str(n)
        result = []
        for i, ch in enumerate(s):
            digit = int(ch)
            pos = len(s) - i - 1
            if digit == 0:
                if result and result[-1] != "零":
                    result.append("零")
            else:
                result.append(nums[digit] + units[pos % 4])
        return "".join(result).rstrip("零")

    def _int_to_chinese(n: int) -> str:
        if n == 0:
            return "零"
        if n < 10000:
            return _four_digit_to_chinese(n)

        low = n % 10000
        mid = (n // 10000) % 10000
        high = n // 100000000

        parts = []
        if high > 0:
            parts.append(_four_digit_to_chinese(high) + "亿")
        if mid > 0:
            parts.append(_four_digit_to_chinese(mid) + "万")
        elif high > 0 and low > 0:
            parts.append("零")

        if low > 0:
            low_str = _four_digit_to_chinese(low)
            need_pad = False
            if mid > 0 and len(str(low)) < 4:
                need_pad = True
            elif high > 0 and mid == 0 and len(str(low)) < 4:
                need_pad = True
            if need_pad:
                low_str = "零" + low_str
            parts.append(low_str)

        return "".join(parts).rstrip("零")

    jiao = decimal_part // 10
    fen = decimal_part % 10

    if integer_part == 0:
        if jiao == 0 and fen == 0:
            return "零元整"
        result = ""
    else:
        result = _int_to_chinese(integer_part) + "元"

    if jiao == 0 and fen == 0:
        result += "整"
    else:
        if jiao > 0:
            result += nums[jiao] + "角"
        if fen > 0:
            if integer_part > 0 and jiao == 0:
                result += "零"
            result += nums[fen] + "分"

    return result
```

- [ ] **Step 3: 在 `number_to_chinese_upper` 下方追加 `_build_standard_contract_context`**

```python
def _build_standard_contract_context(contract) -> dict:
    customer = contract.customer
    sign_date = contract.sign_date
    start_date = contract.start_date
    end_date = contract.end_date

    sign_location = ""
    if customer:
        sign_location = f"{customer.city or ''}{customer.district or ''}"

    total_amount = contract.total_amount or 0

    return {
        "contract_reg_no": contract.contract_no or "",
        "party_a_name": customer.name if customer else "",
        "sign_location": sign_location,
        "sign_year": sign_date.year if sign_date else "",
        "sign_month": sign_date.month if sign_date else "",
        "sign_day": sign_date.day if sign_date else "",
        "valid_start_year": start_date.year if start_date else "",
        "valid_start_month": start_date.month if start_date else "",
        "valid_start_day": start_date.day if start_date else "",
        "valid_end_year": end_date.year if end_date else "",
        "valid_end_month": end_date.month if end_date else "",
        "valid_end_day": end_date.day if end_date else "",
        "service_start_year": start_date.year if start_date else "",
        "service_start_month": start_date.month if start_date else "",
        "service_start_day": start_date.day if start_date else "",
        "service_end_year": end_date.year if end_date else "",
        "service_end_month": end_date.month if end_date else "",
        "service_end_day": end_date.day if end_date else "",
        "total_amount": str(total_amount),
        "total_amount_upper": number_to_chinese_upper(total_amount),
        "payment_amount": str(total_amount),
        "service_address": customer.address if customer else "",
    }
```

- [ ] **Step 4: 在 `_build_standard_contract_context` 下方追加 `render_standard_contract_draft`**

```python
def render_standard_contract_draft(contract, db) -> str | None:
    logger = logging.getLogger(__name__)

    template = db.query(ContractTemplate).filter(ContractTemplate.is_default == True).first()
    if not template or not template.file_url:
        logger.warning("未找到默认合同模板，跳过标准合同草稿生成")
        return None

    try:
        template_bytes = _download_minio_file(template.file_url)

        with tempfile.TemporaryDirectory() as tmpdir:
            template_path = Path(tmpdir) / "template.docx"
            template_path.write_bytes(template_bytes)

            doc = DocxTemplate(str(template_path))
            context = _build_standard_contract_context(contract)
            doc.render(context)

            output_path = Path(tmpdir) / "standard_draft.docx"
            doc.save(str(output_path))

            draft_bytes = output_path.read_bytes()

        draft_object_name = f"contracts/{contract.id}/standard_drafts/{uuid.uuid4().hex}.docx"
        _upload_bytes_to_minio(
            draft_bytes,
            draft_object_name,
            content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )
        return draft_object_name
    except Exception:
        logger.exception("标准合同草稿生成失败")
        return None
```

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/contract_doc_service.py
git commit -m "feat(contract): add number_to_chinese_upper and standard contract rendering"
```

### Task 6: Hook 自动渲染到合同状态流转

**Files:**
- Modify: `backend/app/api/v1/endpoints/contracts.py`

- [ ] **Step 1: 修改导入，添加 `render_standard_contract_draft` 和 `logging`**

将第 19 行：
```python
from app.services.contract_doc_service import render_contract_draft, insert_signatures_and_to_pdf, save_base64_signature_to_minio
```
替换为：
```python
import logging
from app.services.contract_doc_service import render_contract_draft, render_standard_contract_draft, insert_signatures_and_to_pdf, save_base64_signature_to_minio
```

- [ ] **Step 2: 修改 `update_contract_status` 中的提交审核逻辑**

将 `backend/app/api/v1/endpoints/contracts.py:177-184`：
```python
    if body.status == ContractStatus.REVIEW and old_status == ContractStatus.DRAFT:
        if not contract.template_id:
            raise BusinessError("该合同未选择模板，无法提交审核")
        template = db.query(ContractTemplate).filter(ContractTemplate.id == contract.template_id).first()
        if not template or not template.file_url:
            raise BusinessError("模板文件不存在")
        draft_object_name = render_contract_draft(contract, template.file_url)
        contract.draft_doc_url = draft_object_name
```

替换为：
```python
    if body.status == ContractStatus.REVIEW and old_status == ContractStatus.DRAFT:
        if contract.template_id:
            template = db.query(ContractTemplate).filter(ContractTemplate.id == contract.template_id).first()
            if not template or not template.file_url:
                raise BusinessError("模板文件不存在")
            draft_object_name = render_contract_draft(contract, template.file_url)
            contract.draft_doc_url = draft_object_name
        else:
            try:
                standard_object_name = render_standard_contract_draft(contract, db)
                if standard_object_name:
                    contract.standard_doc_url = standard_object_name
            except Exception:
                logging.getLogger(__name__).exception("标准合同草稿生成失败，不影响审核提交")
```

- [ ] **Step 3: 在 `_enrich_contract_out` 中为 `standard_doc_url` 生成预签名 URL**

将 `backend/app/api/v1/endpoints/contracts.py:28-34` 的函数：
```python
def _enrich_contract_out(contract, out: ContractOut) -> ContractOut:
    out.customer_name = contract.customer.name if contract.customer else None
    if contract.service_type_obj:
        out.service_type_id = contract.service_type_obj.id
        out.service_type_name = contract.service_type_obj.name
        out.service_type_code = contract.service_type_obj.code
    return out
```

替换为：
```python
def _enrich_contract_out(contract, out: ContractOut) -> ContractOut:
    out.customer_name = contract.customer.name if contract.customer else None
    if contract.service_type_obj:
        out.service_type_id = contract.service_type_obj.id
        out.service_type_name = contract.service_type_obj.name
        out.service_type_code = contract.service_type_obj.code
    if contract.standard_doc_url:
        try:
            out.standard_doc_url = minio_service.get_presigned_url(contract.standard_doc_url)
        except Exception:
            out.standard_doc_url = None
    return out
```

- [ ] **Step 4: Commit**

```bash
git add backend/app/api/v1/endpoints/contracts.py
git commit -m "feat(contract): auto-render standard contract draft on review submission"
```

### Task 7: 创建默认模板种子脚本

**Files:**
- Create: `backend/scripts/seed_default_contract_template.py`

- [ ] **Step 1: 编写种子脚本**

```python
#!/usr/bin/env python3
"""
初始化默认合同模板：上传模板文件到 MinIO 并在数据库中创建默认记录。
"""
import sys
from pathlib import Path
from io import BytesIO

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models.contract import ContractTemplate
from app.models.service_type import ServiceType
from app.services.minio_service import minio_service


TEMPLATE_PATH = Path(__file__).parent.parent / "templates" / "contracts" / "安全生产社会化服务_template.docx"
MINIO_OBJECT_NAME = "contract-templates/default-安全生产社会化服务_template.docx"


def seed(db: Session) -> None:
    existing = db.query(ContractTemplate).filter(ContractTemplate.is_default == True).first()
    if existing:
        print(f"默认模板已存在: {existing.name} (id={existing.id})")
        return

    if not TEMPLATE_PATH.exists():
        print(f"模板文件不存在: {TEMPLATE_PATH}")
        sys.exit(1)

    service_type = db.query(ServiceType).filter(ServiceType.is_active == True).first()
    if not service_type:
        print("错误：数据库中不存在可用的服务类型，请先创建服务类型")
        sys.exit(1)

    file_bytes = TEMPLATE_PATH.read_bytes()
    minio_service.client.put_object(
        minio_service.bucket,
        MINIO_OBJECT_NAME,
        BytesIO(file_bytes),
        length=len(file_bytes),
        content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )

    template = ContractTemplate(
        name="安全生产社会化服务标准模板",
        service_type=service_type.id,
        file_url=MINIO_OBJECT_NAME,
        is_default=True,
    )
    db.add(template)
    db.commit()
    db.refresh(template)
    print(f"✅ 默认模板已创建: {template.name} (id={template.id}, service_type={service_type.name})")


def main():
    db = SessionLocal()
    try:
        seed(db)
    finally:
        db.close()


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: 运行种子脚本**

Run: `cd backend && PYTHONPATH=. python scripts/seed_default_contract_template.py`
Expected: `✅ 默认模板已创建: 安全生产社会化服务标准模板 (id=X, service_type=...)`

- [ ] **Step 3: Commit**

```bash
git add backend/scripts/seed_default_contract_template.py
git commit -m "feat(contract): add seed script for default contract template"
```

### Task 8: 更新前端类型

**Files:**
- Modify: `frontend/src/types/index.ts`

- [ ] **Step 1: 在 `Contract` 接口中添加 `standard_doc_url`**

在 `frontend/src/types/index.ts:183-186`：
```typescript
  template_id?: number
  draft_doc_url?: string
  final_pdf_url?: string
  signed_at?: string
```

修改为：
```typescript
  template_id?: number
  draft_doc_url?: string
  final_pdf_url?: string
  standard_doc_url?: string
  signed_at?: string
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/types/index.ts
git commit -m "feat(contract): add standard_doc_url to Contract type"
```

### Task 9: 前端详情页添加下载入口

**Files:**
- Modify: `frontend/src/pages/Contracts/index.tsx`

- [ ] **Step 1: 修改提交审核按钮，添加成功提示**

在表格操作列中，将提交审核按钮（约第 211 行）：
```tsx
        {r.status === 'draft' && (
          <PermissionButton permission="contract:update" size="small" onClick={() => updateStatus({ id: r.id, status: 'review' })}>提交审核</PermissionButton>
        )}
```

替换为：
```tsx
        {r.status === 'draft' && (
          <PermissionButton permission="contract:update" size="small" onClick={() => {
            updateStatus({ id: r.id, status: 'review' }).unwrap()
              .then(() => message.success('已提交审核，标准合同草稿已生成'))
              .catch((err: any) => message.error(err?.data?.detail || '提交审核失败'))
          }}>提交审核</PermissionButton>
        )}
```

- [ ] **Step 2: 在 `ContractDetail` 的 `Descriptions` 中追加标准合同草稿项**

在 `frontend/src/pages/Contracts/index.tsx:433` 的备注项之后：
```tsx
        <Descriptions.Item label="备注" span={2}>{data.remark}</Descriptions.Item>
```

追加：
```tsx
        {data.standard_doc_url ? (
          <Descriptions.Item label="标准合同草稿" span={2}>
            <Button type="link" onClick={() => window.open(data.standard_doc_url, '_blank')}>下载标准合同草稿</Button>
          </Descriptions.Item>
        ) : (
          <Descriptions.Item label="标准合同草稿" span={2}>
            <span style={{ color: '#999' }}>尚未生成标准合同草稿（提交审核后自动生成）</span>
          </Descriptions.Item>
        )}
```

- [ ] **Step 3: 运行前端 Lint**

Run: `cd frontend && npm run lint`
Expected: No errors

- [ ] **Step 4: Commit**

```bash
git add frontend/src/pages/Contracts/index.tsx frontend/src/types/index.ts
git commit -m "feat(contract): add standard contract draft download in detail view"
```

### Task 10: 单元测试 number_to_chinese_upper

**Files:**
- Create: `backend/tests/test_contract_doc_service.py`

- [ ] **Step 1: 创建测试文件**

```python
import pytest
from decimal import Decimal
from app.services.contract_doc_service import number_to_chinese_upper


@pytest.mark.parametrize("amount,expected", [
    (Decimal("0"), "零元整"),
    (Decimal("10"), "壹拾元整"),
    (Decimal("100000"), "壹拾万元整"),
    (Decimal("1004"), "壹仟零肆元整"),
    (Decimal("1010"), "壹仟零壹拾元整"),
    (Decimal("1234.56"), "壹仟贰佰叁拾肆元伍角陆分"),
    (Decimal("0.07"), "柒分"),
    (Decimal("0.50"), "伍角"),
    (Decimal("10.05"), "壹拾元零伍分"),
    (Decimal("100.05"), "壹佰元零伍分"),
    (Decimal("100000001"), "壹亿零壹元整"),
])
def test_number_to_chinese_upper(amount, expected):
    assert number_to_chinese_upper(amount) == expected
```

- [ ] **Step 2: 运行测试**

Run: `cd backend && pytest tests/test_contract_doc_service.py -v`
Expected: `11 passed`

- [ ] **Step 3: Commit**

```bash
git add backend/tests/test_contract_doc_service.py
git commit -m "test(contract): add unit tests for number_to_chinese_upper"
```

### Task 11: 集成测试标准合同渲染

**Files:**
- Modify: `backend/tests/conftest.py`
- Create: `backend/tests/test_contract_standard_template.py`

- [ ] **Step 1: 在 `conftest.py` 末尾追加 `db_session` fixture**

```python
@pytest.fixture
def db_session():
    from app.db.session import SessionLocal
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

- [ ] **Step 2: 创建集成测试文件**

```python
import tempfile
from pathlib import Path
from unittest.mock import patch
from decimal import Decimal
from datetime import date

from docx import Document

from app.services.contract_doc_service import render_standard_contract_draft
from app.models.contract import Contract, ContractTemplate
from app.models.customer import Customer
from app.models.service_type import ServiceType


def test_render_standard_contract_draft(db_session):
    # Seed service type
    st = ServiceType(code="eval", name="安全评价", is_active=True)
    db_session.add(st)
    db_session.flush()

    # Seed customer
    customer = Customer(name="测试甲方", city="北京市", district="朝阳区", address="测试路1号")
    db_session.add(customer)
    db_session.flush()

    # Seed contract
    contract = Contract(
        contract_no="HT2024001",
        title="测试合同",
        customer_id=customer.id,
        service_type=st.id,
        total_amount=Decimal("8888.88"),
        sign_date=date(2024, 6, 1),
        start_date=date(2024, 6, 1),
        end_date=date(2025, 5, 31),
    )
    db_session.add(contract)
    db_session.flush()

    # Seed default template
    template = ContractTemplate(
        name="默认模板",
        service_type=st.id,
        file_url="contract-templates/default_template.docx",
        is_default=True,
    )
    db_session.add(template)
    db_session.commit()

    # Build a minimal .docx with placeholders
    with tempfile.TemporaryDirectory() as tmpdir:
        tpl_path = Path(tmpdir) / "tpl.docx"
        doc = Document()
        doc.add_paragraph("甲方: {{party_a_name}}")
        doc.add_paragraph("金额大写: {{total_amount_upper}}")
        doc.save(str(tpl_path))
        template_bytes = tpl_path.read_bytes()

    with patch("app.services.contract_doc_service._download_minio_file", return_value=template_bytes):
        with patch("app.services.contract_doc_service._upload_bytes_to_minio", return_value="contracts/standard_drafts/test.docx") as mock_upload:
            result = render_standard_contract_draft(contract, db_session)
            assert result == "contracts/standard_drafts/test.docx"
            assert mock_upload.called
            uploaded_bytes = mock_upload.call_args[0][0]
            assert isinstance(uploaded_bytes, bytes)
            assert len(uploaded_bytes) > 0
```

- [ ] **Step 3: 运行测试**

Run: `cd backend && pytest tests/test_contract_standard_template.py -v`
Expected: `1 passed`

- [ ] **Step 4: Commit**

```bash
git add backend/tests/conftest.py backend/tests/test_contract_standard_template.py
git commit -m "test(contract): add integration test for standard contract rendering"
```

### Task 12: 最终验证

- [ ] **Step 1: 运行全部后端测试**

Run: `cd backend && pytest tests/ -v`
Expected: All existing tests + 12 new tests pass

- [ ] **Step 2: 运行后端 API 验证脚本（可选，需要服务器运行）**

Run: `cd backend && PYTHONPATH=. python scripts/api_validation_tests.py`
Expected: All checks pass

- [ ] **Step 3: 运行前端 Lint**

Run: `cd frontend && npm run lint`
Expected: No errors

- [ ] **Step 4: 手工验证清单**

- [ ] 运行种子脚本，确认默认模板 `安全生产社会化服务标准模板` 已创建
- [ ] 创建一条新合同，填写客户（城市/区县/地址）、金额 `12345.67`、日期
- [ ] 点击「提交审核」，提示「已提交审核，标准合同草稿已生成」
- [ ] 进入合同详情，基本信息中出现「下载标准合同草稿」按钮
- [ ] 下载并打开 Word 文档，检查合同编号、甲方名称、签订地点（城市+区县）、日期、金额大写 `壹万贰仟叁佰肆拾伍元陆角柒分`、服务地址等已正确替换

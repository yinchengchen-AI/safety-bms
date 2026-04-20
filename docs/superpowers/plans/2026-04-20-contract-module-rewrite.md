# Contract Module Rewrite Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rebuild the contract module around offline signing and file archiving while removing review and online-sign workflows.

**Architecture:** Keep the existing `contracts` table and downstream relations, but collapse the status machine, add a `contract_attachments` table for draft/signed files, and rewrite the contract API and React page around a draft -> signed -> executing -> completed lifecycle. Preserve legacy behavior on a separate git branch before changing `main`, then migrate historical files and downstream status checks onto the new model.

**Tech Stack:** FastAPI, SQLAlchemy 2.0, Alembic, Pydantic, React, TypeScript, Redux Toolkit Query, Ant Design 5, Vite

---

## File Structure Map

### Backend core flow

- Modify: `backend/app/core/constants.py`
  Purpose: remove `review` / `active` from `ContractStatus` and keep the new five-state lifecycle as the single source of truth.
- Modify: `backend/app/models/contract.py`
  Purpose: add `ContractAttachment`, keep `draft_doc_url`/`signed_at`, and retain legacy fields only for migration compatibility.
- Modify: `backend/app/schemas/contract.py`
  Purpose: reshape contract request/response payloads around offline signing, attachment lists, and simplified status transitions.
- Modify: `backend/app/crud/contract.py`
  Purpose: update allowed transitions, attachment-aware status checks, and change-record logging.
- Modify: `backend/app/api/v1/endpoints/contracts.py`
  Purpose: remove review/online-sign endpoints and implement attachment upload, list, delete, and simplified status flow.
- Modify: `backend/app/services/contract_doc_service.py`
  Purpose: keep unified draft generation and return attachment-friendly metadata.

### Backend migrations and tests

- Create: `backend/migrations/versions/20260420_01_rewrite_contract_flow.py`
  Purpose: create `contract_attachments`, migrate old files, and remap old statuses.
- Create: `backend/tests/test_contract_rewrite_flow.py`
  Purpose: cover simplified status transitions, signed-attachment rules, and attachment lifecycle.
- Modify: `backend/scripts/api_validation_tests.py`
  Purpose: validate the rewritten contract flow against a running dev server.

### Downstream backend integrations

- Modify: `backend/app/api/v1/endpoints/invoices.py`
  Purpose: allow invoice creation only from `signed` and above.
- Modify: `backend/app/api/v1/endpoints/payments.py`
  Purpose: align payment rules with the new contract states.
- Modify: `backend/app/api/v1/endpoints/services.py`
  Purpose: align service-order creation/completion checks with the new contract states.

### Frontend contract module

- Modify: `frontend/src/types/index.ts`
  Purpose: remove old contract statuses and online-sign types, add attachment types.
- Modify: `frontend/src/utils/constants.ts`
  Purpose: update contract status labels for the new lifecycle.
- Modify: `frontend/src/store/api/contractsApi.ts`
  Purpose: replace sign/upload-final endpoints with attachment APIs and simplified status updates.
- Modify: `frontend/src/pages/Contracts/index.tsx`
  Purpose: rewrite list, form drawers, detail drawer, and status-based actions for offline signing.
- Delete: `frontend/src/components/ContractSignModal.tsx`
  Purpose: remove unused online-sign UI.

### Frontend downstream consumers

- Modify: `frontend/src/pages/Invoices/index.tsx`
  Purpose: consume contracts in `signed` and above without depending on `active`.
- Modify: `frontend/src/pages/Payments/index.tsx`
  Purpose: consume contracts in `signed` and above without depending on `active`.
- Modify: `frontend/src/pages/Services/index.tsx`
  Purpose: align any contract-status-dependent UI copy or filters with the new lifecycle.

## Task 1: Preserve Legacy Flow And Reshape Contract Data Model

**Files:**
- Create: `backend/tests/test_contract_rewrite_flow.py`
- Create: `backend/migrations/versions/20260420_01_rewrite_contract_flow.py`
- Modify: `backend/app/core/constants.py`
- Modify: `backend/app/models/contract.py`
- Modify: `backend/app/schemas/contract.py`
- Modify: `backend/app/crud/contract.py`

- [ ] **Step 1: Create the legacy backup branch before changing `main`**

```bash
git checkout -b backup/contract-module-before-rewrite
git push -u origin backup/contract-module-before-rewrite
git checkout main
```

Expected result: `backup/contract-module-before-rewrite` exists locally and on origin, and `git branch --show-current` prints `main`.

- [ ] **Step 2: Write the failing backend tests for the new contract state machine and attachment requirements**

```python
from app.core.constants import ContractStatus
from app.models.contract import Contract, ContractAttachment


def test_allowed_contract_transitions_collapsed():
    from app.crud.contract import ALLOWED_TRANSITIONS

    assert ALLOWED_TRANSITIONS[ContractStatus.DRAFT] == {
        ContractStatus.SIGNED,
        ContractStatus.TERMINATED,
    }
    assert ALLOWED_TRANSITIONS[ContractStatus.SIGNED] == {
        ContractStatus.EXECUTING,
        ContractStatus.TERMINATED,
    }


def test_cannot_mark_signed_without_signed_attachment(db_session):
    contract = Contract(
        contract_no="HT202604200001",
        title="线下签约测试合同",
        customer_id=1,
        service_type=1,
        total_amount=1000,
        status=ContractStatus.DRAFT,
    )
    db_session.add(contract)
    db_session.commit()

    from app.crud.contract import crud_contract
    import pytest

    with pytest.raises(Exception, match="请先上传已签合同附件"):
        crud_contract.update_status(
            db_session,
            db_obj=contract,
            new_status=ContractStatus.SIGNED,
            changed_by=1,
        )


def test_latest_draft_and_signed_attachment_are_separated(db_session):
    contract = Contract(
        contract_no="HT202604200002",
        title="附件追溯测试合同",
        customer_id=1,
        service_type=1,
        total_amount=1000,
        status=ContractStatus.DRAFT,
    )
    db_session.add(contract)
    db_session.flush()

    db_session.add_all(
        [
            ContractAttachment(
                contract_id=contract.id,
                file_name="draft.docx",
                file_url="contracts/draft.docx",
                file_type="draft",
                uploaded_by=1,
            ),
            ContractAttachment(
                contract_id=contract.id,
                file_name="signed.pdf",
                file_url="contracts/signed.pdf",
                file_type="signed",
                uploaded_by=1,
            ),
        ]
    )
    db_session.commit()

    assert contract.attachments[0].file_type == "draft"
    assert contract.attachments[1].file_type == "signed"
```

- [ ] **Step 3: Run the focused backend tests and confirm they fail first**

Run: `cd /Users/yinchengchen/ClaudeCode/safety-bms/backend && PYTHONPATH=. pytest tests/test_contract_rewrite_flow.py -q`

Expected: FAIL because `ContractAttachment` does not exist yet and the transition map still contains `review` / `active`.

- [ ] **Step 4: Implement the model, schema, CRUD, and migration changes**

```python
# backend/app/core/constants.py
class ContractStatus(StrEnum):
    DRAFT = "draft"
    SIGNED = "signed"
    EXECUTING = "executing"
    COMPLETED = "completed"
    TERMINATED = "terminated"
```

```python
# backend/app/models/contract.py
class ContractAttachment(Base, TimestampMixin):
    __tablename__ = "contract_attachments"

    id = Column(Integer, primary_key=True, index=True)
    contract_id = Column(Integer, ForeignKey("contracts.id", ondelete="CASCADE"), nullable=False)
    file_name = Column(String(255), nullable=False)
    file_url = Column(String(500), nullable=False)
    file_type = Column(String(20), nullable=False, comment="draft / signed / other")
    remark = Column(Text)
    uploaded_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    uploaded_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    contract = relationship("Contract", back_populates="attachments")


class Contract(Base, TimestampMixin, SoftDeleteMixin):
    attachments = relationship(
        "ContractAttachment",
        back_populates="contract",
        cascade="all, delete-orphan",
        order_by="ContractAttachment.uploaded_at.asc()",
    )
```

```python
# backend/app/schemas/contract.py
class ContractAttachmentOut(BaseModel):
    id: int
    file_name: str
    file_url: str
    file_type: str
    remark: str | None = None
    uploaded_by: int | None = None
    uploaded_at: datetime

    model_config = {"from_attributes": True}


class ContractAttachmentCreate(BaseModel):
    file_name: str
    file_url: str
    file_type: Literal["draft", "signed", "other"]
    remark: str | None = None


class ContractOut(ContractBase):
    id: int
    status: ContractStatus
    draft_doc_url: str | None = None
    signed_at: datetime | None = None
    attachments: list[ContractAttachmentOut] = []
```

```python
# backend/app/crud/contract.py
ALLOWED_TRANSITIONS = {
    ContractStatus.DRAFT: {ContractStatus.SIGNED, ContractStatus.TERMINATED},
    ContractStatus.SIGNED: {ContractStatus.EXECUTING, ContractStatus.TERMINATED},
    ContractStatus.EXECUTING: {ContractStatus.COMPLETED, ContractStatus.TERMINATED},
    ContractStatus.COMPLETED: set(),
    ContractStatus.TERMINATED: set(),
}


def has_signed_attachment(self, db: Session, *, contract_id: int) -> bool:
    return (
        db.query(ContractAttachment)
        .filter(
            ContractAttachment.contract_id == contract_id,
            ContractAttachment.file_type == "signed",
        )
        .count()
        > 0
    )


def update_status(
    self,
    db: Session,
    *,
    db_obj: Contract,
    new_status: ContractStatus,
    changed_by: int,
    remark: str = "",
):
    if new_status == ContractStatus.SIGNED and not self.has_signed_attachment(db, contract_id=db_obj.id):
        raise BusinessError("请先上传已签合同附件")
```

```python
# backend/migrations/versions/20260420_01_rewrite_contract_flow.py
def upgrade() -> None:
    op.create_table(
        "contract_attachments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("contract_id", sa.Integer(), sa.ForeignKey("contracts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("file_name", sa.String(length=255), nullable=False),
        sa.Column("file_url", sa.String(length=500), nullable=False),
        sa.Column("file_type", sa.String(length=20), nullable=False),
        sa.Column("remark", sa.Text(), nullable=True),
        sa.Column("uploaded_by", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("uploaded_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
    )
    op.execute(
        """
        INSERT INTO contract_attachments (contract_id, file_name, file_url, file_type, uploaded_by, uploaded_at, created_at, updated_at)
        SELECT id, 'legacy-draft.docx', draft_doc_url, 'draft', created_by, NOW(), NOW(), NOW()
        FROM contracts WHERE draft_doc_url IS NOT NULL
        """
    )
```

- [ ] **Step 5: Run the tests again and commit the data-model foundation**

Run: `cd /Users/yinchengchen/ClaudeCode/safety-bms/backend && PYTHONPATH=. pytest tests/test_contract_rewrite_flow.py -q`

Expected: PASS

```bash
git add backend/app/core/constants.py backend/app/models/contract.py backend/app/schemas/contract.py backend/app/crud/contract.py backend/migrations/versions/20260420_01_rewrite_contract_flow.py backend/tests/test_contract_rewrite_flow.py
git commit -m "feat(contracts): simplify status model and add attachments"
```

## Task 2: Rewrite Contract Endpoints Around Offline Signing

**Files:**
- Modify: `backend/app/api/v1/endpoints/contracts.py`
- Modify: `backend/app/services/contract_doc_service.py`
- Modify: `backend/app/schemas/contract.py`
- Modify: `backend/tests/test_contract_rewrite_flow.py`

- [ ] **Step 1: Add failing API tests for simplified status, draft generation, and signed attachment upload**

```python
def test_upload_signed_attachment_marks_contract_signed(client, admin_token, draft_contract):
    response = client.post(
        f"/api/v1/contracts/{draft_contract.id}/attachments",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "file_name": "signed-contract.pdf",
            "file_url": "contracts/signed-contract.pdf",
            "file_type": "signed",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "signed"
    assert any(item["file_type"] == "signed" for item in data["attachments"])


def test_generate_draft_creates_draft_attachment(client, admin_token, draft_contract, monkeypatch):
    monkeypatch.setattr(
        "app.api.v1.endpoints.contracts.render_standard_contract_draft",
        lambda contract, db: "contracts/generated-draft.docx",
    )

    response = client.post(
        f"/api/v1/contracts/{draft_contract.id}/generate-draft",
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["draft_doc_url"] == "contracts/generated-draft.docx"
    assert any(item["file_type"] == "draft" for item in data["attachments"])
```

- [ ] **Step 2: Run the targeted API tests and verify endpoint failures**

Run: `cd /Users/yinchengchen/ClaudeCode/safety-bms/backend && PYTHONPATH=. pytest tests/test_contract_rewrite_flow.py -q`

Expected: FAIL because `/contracts/{id}/attachments` does not exist yet and `/generate-draft` does not create attachment records.

- [ ] **Step 3: Implement the rewritten contract endpoints**

```python
# backend/app/api/v1/endpoints/contracts.py
@router.post("/{contract_id}/attachments", response_model=ContractOut)
def upload_contract_attachment(
    contract_id: int,
    body: ContractAttachmentCreate,
    current_user: User = Depends(require_permissions(PermissionCode.CONTRACT_UPDATE)),
    db: Session = Depends(get_db),
):
    contract = _get_editable_contract(db, contract_id, current_user)
    attachment = ContractAttachment(
        contract_id=contract.id,
        file_name=body.file_name,
        file_url=body.file_url,
        file_type=body.file_type,
        remark=body.remark,
        uploaded_by=current_user.id,
    )
    db.add(attachment)

    if body.file_type == "signed" and contract.status == ContractStatus.DRAFT:
        contract.status = ContractStatus.SIGNED
        contract.signed_at = datetime.now(UTC)

    db.commit()
    db.refresh(contract)
    return _build_contract_out(db, contract)


@router.delete("/{contract_id}/attachments/{attachment_id}", response_model=ResponseMsg)
def delete_contract_attachment(
    contract_id: int,
    attachment_id: int,
    current_user: User = Depends(require_permissions(PermissionCode.CONTRACT_UPDATE)),
    db: Session = Depends(get_db),
):
    if attachment.file_type == "signed" and contract.status in {
        ContractStatus.SIGNED,
        ContractStatus.EXECUTING,
        ContractStatus.COMPLETED,
    }:
        raise BusinessError("当前状态依赖已签合同附件，请先调整合同状态")
```

```python
# backend/app/api/v1/endpoints/contracts.py
@router.post("/{contract_id}/generate-draft", response_model=ContractOut)
def generate_contract_draft(
    contract_id: int,
    current_user: User = Depends(require_permissions(PermissionCode.CONTRACT_UPDATE)),
    db: Session = Depends(get_db),
):
    object_name = render_standard_contract_draft(contract, db)
    contract.draft_doc_url = object_name
    db.add(
        ContractAttachment(
            contract_id=contract.id,
            file_name=object_name.rsplit("/", 1)[-1],
            file_url=object_name,
            file_type="draft",
            uploaded_by=current_user.id,
        )
    )
    db.commit()
    db.refresh(contract)
    return _build_contract_out(db, contract)
```

- [ ] **Step 4: Re-run the API tests and the existing contract document tests**

Run: `cd /Users/yinchengchen/ClaudeCode/safety-bms/backend && PYTHONPATH=. pytest tests/test_contract_rewrite_flow.py tests/test_contract_doc_service.py tests/test_contract_standard_template.py -q`

Expected: PASS

- [ ] **Step 5: Commit the contract API rewrite**

```bash
git add backend/app/api/v1/endpoints/contracts.py backend/app/services/contract_doc_service.py backend/app/schemas/contract.py backend/tests/test_contract_rewrite_flow.py
git commit -m "feat(contracts): rewrite endpoints for offline signing"
```

## Task 3: Align Downstream Backend Rules With The New Contract Lifecycle

**Files:**
- Modify: `backend/app/api/v1/endpoints/invoices.py`
- Modify: `backend/app/api/v1/endpoints/payments.py`
- Modify: `backend/app/api/v1/endpoints/services.py`
- Modify: `backend/scripts/api_validation_tests.py`
- Modify: `backend/tests/test_concurrent_business.py`

- [ ] **Step 1: Add failing checks for invoice/payment/service behavior with `signed` contracts**

```python
def test_invoice_requires_signed_or_executing_contract(client, admin_token, draft_contract, signed_contract):
    draft_resp = client.post(
        "/api/v1/invoices",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "contract_id": draft_contract.id,
            "invoice_no": "INV-DRAFT-001",
            "invoice_type": "general",
            "amount": 100,
            "tax_rate": 0.06,
            "invoice_date": "2026-04-20",
        },
    )
    signed_resp = client.post(
        "/api/v1/invoices",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "contract_id": signed_contract.id,
            "invoice_no": "INV-SIGNED-001",
            "invoice_type": "general",
            "amount": 100,
            "tax_rate": 0.06,
            "invoice_date": "2026-04-20",
        },
    )

    assert draft_resp.status_code == 400
    assert signed_resp.status_code == 201
```

- [ ] **Step 2: Run the affected backend tests and capture the current failure**

Run: `cd /Users/yinchengchen/ClaudeCode/safety-bms/backend && PYTHONPATH=. pytest tests/test_concurrent_business.py -q`

Expected: FAIL because invoice/payment/service code still assumes `active` is the precondition.

- [ ] **Step 3: Replace old `active` assumptions with `signed` and above**

```python
# backend/app/api/v1/endpoints/invoices.py
if contract.status not in {
    ContractStatus.SIGNED,
    ContractStatus.EXECUTING,
    ContractStatus.COMPLETED,
}:
    raise BusinessError("仅已签订或履行中的合同可创建发票")
```

```python
# backend/app/api/v1/endpoints/payments.py
if contract.status not in {
    ContractStatus.SIGNED,
    ContractStatus.EXECUTING,
    ContractStatus.COMPLETED,
}:
    raise BusinessError("仅已签订或履行中的合同可登记收款")
```

```python
# backend/scripts/api_validation_tests.py
def create_contract(customer_id: int, total_amount: float = 10000):
    payload = {
        "contract_no": f"C-{date.today().isoformat()}-{total_amount}",
        "title": "测试合同",
        "customer_id": customer_id,
        "service_type": get_service_type_id(),
        "total_amount": total_amount,
        "start_date": date.today().isoformat(),
        "end_date": (date.today() + timedelta(days=30)).isoformat(),
        "sign_date": date.today().isoformat(),
    }
    r = session.post(f"{BASE_URL}/contracts", json=payload)
    assert r.status_code == 201, f"创建合同失败: {r.text}"
    contract_id = r.json()["id"]
    session.post(
        f"{BASE_URL}/contracts/{contract_id}/attachments",
        json={
            "file_name": "signed.pdf",
            "file_url": f"contracts/{contract_id}/signed.pdf",
            "file_type": "signed",
        },
    )
```

- [ ] **Step 4: Run backend regression tests and the API validation script**

Run: `cd /Users/yinchengchen/ClaudeCode/safety-bms/backend && PYTHONPATH=. pytest tests/test_concurrent_business.py tests/test_contract_rewrite_flow.py -q`

Expected: PASS

Run: `cd /Users/yinchengchen/ClaudeCode/safety-bms/backend && PYTHONPATH=. python scripts/api_validation_tests.py`

Expected: Script prints success lines for login, contract creation, signed attachment upload, invoice limit, and payment limit.

- [ ] **Step 5: Commit the downstream backend adaptations**

```bash
git add backend/app/api/v1/endpoints/invoices.py backend/app/api/v1/endpoints/payments.py backend/app/api/v1/endpoints/services.py backend/scripts/api_validation_tests.py backend/tests/test_concurrent_business.py
git commit -m "fix(contracts): align downstream flows with signed lifecycle"
```

## Task 4: Update Frontend Types, API Slice, And Shared Labels

**Files:**
- Modify: `frontend/src/types/index.ts`
- Modify: `frontend/src/utils/constants.ts`
- Modify: `frontend/src/store/api/contractsApi.ts`
- Delete: `frontend/src/components/ContractSignModal.tsx`

- [ ] **Step 1: Update the shared frontend types and API contracts**

```ts
// frontend/src/types/index.ts
export type ContractStatus = 'draft' | 'signed' | 'executing' | 'completed' | 'terminated'

export interface ContractAttachment {
  id: number
  file_name: string
  file_url: string
  file_type: 'draft' | 'signed' | 'other'
  remark?: string
  uploaded_by?: number
  uploaded_at: string
}

export interface Contract {
  id: number
  contract_no: string
  title: string
  customer_id: number
  customer_name?: string
  service_type: number
  total_amount: number
  payment_plan: PaymentPlan
  status: ContractStatus
  start_date?: string
  end_date?: string
  sign_date?: string
  remark?: string
  draft_doc_url?: string
  signed_at?: string
  created_at: string
  attachments?: ContractAttachment[]
}

export interface ContractAttachmentCreate {
  file_name: string
  file_url: string
  file_type: 'draft' | 'signed' | 'other'
  remark?: string
}
```

- [ ] **Step 2: Replace old contract labels and RTK Query endpoints**

```ts
// frontend/src/utils/constants.ts
export const ContractStatusLabels: Record<string, string> = {
  draft: '草稿',
  signed: '已签订',
  executing: '履行中',
  completed: '已完成',
  terminated: '已终止',
}
```

```ts
// frontend/src/store/api/contractsApi.ts
uploadContractAttachment: builder.mutation<Contract, { id: number; data: ContractAttachmentCreate }>({
  query: ({ id, data }) => ({ url: `/contracts/${id}/attachments`, method: 'POST', body: data }),
  invalidatesTags: (_, __, { id }) => [{ type: 'Contract', id }, 'Contract'],
}),
deleteContractAttachment: builder.mutation<{ message: string }, { id: number; attachmentId: number }>({
  query: ({ id, attachmentId }) => ({ url: `/contracts/${id}/attachments/${attachmentId}`, method: 'DELETE' }),
  invalidatesTags: (_, __, { id }) => [{ type: 'Contract', id }, 'Contract'],
}),
```

- [ ] **Step 3: Remove the online-sign contract modal from the UI layer**

```ts
// frontend/src/pages/Contracts/index.tsx
// delete:
// import ContractSignModal from '@/components/ContractSignModal'
// const [signModalOpen, setSignModalOpen] = useState(false)
// const [signingContractId, setSigningContractId] = useState<number | null>(null)
```

```bash
rm frontend/src/components/ContractSignModal.tsx
```

- [ ] **Step 4: Run frontend lint and build to catch type errors**

Run: `cd /Users/yinchengchen/ClaudeCode/safety-bms/frontend && npm run lint`

Expected: PASS

Run: `cd /Users/yinchengchen/ClaudeCode/safety-bms/frontend && npm run build`

Expected: PASS

- [ ] **Step 5: Commit the shared frontend contract changes**

```bash
git add frontend/src/types/index.ts frontend/src/utils/constants.ts frontend/src/store/api/contractsApi.ts frontend/src/pages/Contracts/index.tsx frontend/src/components/ContractSignModal.tsx
git commit -m "refactor(frontend): remove online-sign contract primitives"
```

## Task 5: Rebuild The Contract Page Around Draft, Attach, And Archive

**Files:**
- Modify: `frontend/src/pages/Contracts/index.tsx`

- [ ] **Step 1: Rewrite the list actions and filters to match the new lifecycle**

```tsx
const columns = [
  { title: '合同编号', dataIndex: 'contract_no', key: 'contract_no' },
  { title: '合同名称', dataIndex: 'title', key: 'title', ellipsis: true },
  { title: '客户', dataIndex: 'customer_name', key: 'customer_name' },
  { title: '收款计划', dataIndex: 'payment_plan', key: 'payment_plan', render: (v: PaymentPlan) => PaymentPlanLabels[v] },
  { title: '服务周期', key: 'service_period', render: (_: unknown, r: Contract) => `${r.start_date || '-'} ~ ${r.end_date || '-'}` },
  { title: '状态', dataIndex: 'status', key: 'status', render: (s: ContractStatus) => <Tag color={statusColors[s]}>{ContractStatusLabels[s]}</Tag> },
]
```

```tsx
<DatePicker.RangePicker onChange={(value) => {
  setServiceDateRange(value ? [value[0]?.format('YYYY-MM-DD'), value[1]?.format('YYYY-MM-DD')] : undefined)
}} />
```

- [ ] **Step 2: Rebuild the drawer form into grouped sections and keep draft generation separate**

```tsx
<Form layout="vertical" form={form} onFinish={handleCreate}>
  <Divider orientation="left">基本信息</Divider>
  <Form.Item name="contract_no" label="合同编号" rules={[{ required: true }]}><Input disabled /></Form.Item>
  <Form.Item name="title" label="合同名称" rules={[{ required: true }]}><Input /></Form.Item>
  <Form.Item name="customer_id" label="客户" rules={[{ required: true }]}><Select options={customerOptions} /></Form.Item>

  <Divider orientation="left">商务信息</Divider>
  <Form.Item name="total_amount" label="合同金额(元)" rules={[{ required: true }]}><InputNumber min={0} style={{ width: '100%' }} /></Form.Item>
  <Form.Item name="payment_plan" label="收款计划"><Select options={paymentPlanOptions} /></Form.Item>

  <Divider orientation="left">履约信息</Divider>
  <Form.Item name="sign_date" label="签订日期"><DatePicker style={{ width: '100%' }} /></Form.Item>
  <Form.Item name="start_date" label="开始日期"><DatePicker style={{ width: '100%' }} /></Form.Item>
  <Form.Item name="end_date" label="结束日期"><DatePicker style={{ width: '100%' }} /></Form.Item>

  <Divider orientation="left">补充信息</Divider>
  <Form.Item name="remark" label="备注"><Input.TextArea rows={4} /></Form.Item>
</Form>
```

- [ ] **Step 3: Add attachment upload and archive-focused detail sections**

```tsx
const handleUploadSigned = async (record: Contract, fileUrl: string, fileName: string) => {
  await uploadContractAttachment({
    id: record.id,
    data: { file_name: fileName, file_url: fileUrl, file_type: 'signed' },
  }).unwrap()
  message.success('已签合同上传成功，合同已更新为已签订')
}
```

```tsx
<Descriptions title="文件资料" column={1}>
  <Descriptions.Item label="合同草稿">
    {latestDraft ? <Button type="link" onClick={() => window.open(latestDraft.file_url, '_blank')}>下载草稿</Button> : '未生成'}
  </Descriptions.Item>
  <Descriptions.Item label="已签附件">
    {latestSigned ? <Button type="link" onClick={() => window.open(latestSigned.file_url, '_blank')}>查看已签合同</Button> : '未上传'}
  </Descriptions.Item>
</Descriptions>
```

- [ ] **Step 4: Run frontend lint and build after the page rewrite**

Run: `cd /Users/yinchengchen/ClaudeCode/safety-bms/frontend && npm run lint`

Expected: PASS

Run: `cd /Users/yinchengchen/ClaudeCode/safety-bms/frontend && npm run build`

Expected: PASS

- [ ] **Step 5: Commit the rewritten contract page**

```bash
git add frontend/src/pages/Contracts/index.tsx
git commit -m "feat(contracts): rebuild offline signing workflow ui"
```

## Task 6: Update Frontend Downstream Consumers And Run End-To-End Verification

**Files:**
- Modify: `frontend/src/pages/Invoices/index.tsx`
- Modify: `frontend/src/pages/Payments/index.tsx`
- Modify: `frontend/src/pages/Services/index.tsx`
- Modify: `docs/superpowers/specs/2026-04-20-contract-module-rewrite-design.md`

- [ ] **Step 1: Replace remaining frontend `active` assumptions with the new signed-first lifecycle**

```tsx
// frontend/src/pages/Invoices/index.tsx
const { data: contractsData } = useListContractsQuery({ page: 1, page_size: 200, status: undefined })
const selectableContracts = (contractsData?.items || []).filter((c) =>
  ['signed', 'executing', 'completed'].includes(c.status)
)
```

```tsx
// frontend/src/pages/Payments/index.tsx
const availableContracts = (contractsData?.items || []).filter((c) =>
  ['signed', 'executing', 'completed'].includes(c.status)
)
```

- [ ] **Step 2: Run frontend lint/build and backend regression tests together**

Run: `cd /Users/yinchengchen/ClaudeCode/safety-bms/backend && PYTHONPATH=. pytest tests/test_contract_rewrite_flow.py tests/test_concurrent_business.py tests/test_contract_doc_service.py tests/test_contract_standard_template.py -q`

Expected: PASS

Run: `cd /Users/yinchengchen/ClaudeCode/safety-bms/frontend && npm run lint && npm run build`

Expected: PASS

- [ ] **Step 3: Execute the manual end-to-end verification checklist against a local stack**

```bash
cd /Users/yinchengchen/ClaudeCode/safety-bms/backend
PYTHONPATH=. uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

```bash
cd /Users/yinchengchen/ClaudeCode/safety-bms/frontend
npm run dev
```

Manual checklist:

- Create a new contract and save it as `草稿`.
- Generate a draft file and confirm it appears in the detail drawer.
- Upload a signed PDF and confirm the contract becomes `已签订`.
- Move the contract to `履行中`, then `已完成`.
- Open invoice/payment pages and verify the signed contract is selectable.
- Open a historical migrated contract and confirm both draft and signed files are visible when present.

- [ ] **Step 4: Update the design spec with implementation notes only if behavior changed during delivery**

```markdown
## Implementation Notes

- Historical `active` contracts without signed files are migrated to `draft`.
- Signed attachment deletion is blocked once the contract is `signed` or beyond.
```

Only apply this step if implementation behavior differs from the approved design; otherwise leave the spec unchanged.

- [ ] **Step 5: Commit the downstream UI alignment and verification-ready state**

```bash
git add frontend/src/pages/Invoices/index.tsx frontend/src/pages/Payments/index.tsx frontend/src/pages/Services/index.tsx docs/superpowers/specs/2026-04-20-contract-module-rewrite-design.md
git commit -m "chore(contracts): finish downstream lifecycle alignment"
```

## Self-Review

### Spec coverage

- Status simplification and offline-sign lifecycle: covered by Task 1 and Task 2.
- Attachment model and dual-file traceability: covered by Task 1, Task 2, and Task 5.
- Contract page rewrite: covered by Task 4 and Task 5.
- Historical branch preservation: covered by Task 1 Step 1.
- Downstream invoice/payment/service alignment: covered by Task 3 and Task 6.
- Migration and historical file compatibility: covered by Task 1 Step 4 and Task 6 Step 3.

### Placeholder scan

- No unfinished marker words remain in the plan body.
- Every task has exact file paths, commands, and concrete code snippets.
- The one conditional step in Task 6 Step 4 is explicitly bounded to a real condition and does not block execution.

### Type consistency

- Backend and frontend both use `draft` / `signed` / `executing` / `completed` / `terminated`.
- Attachment type names are consistently `draft`, `signed`, and `other`.
- Attachment upload API is consistently `/contracts/{id}/attachments`.

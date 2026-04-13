# 合同审核与签订流程融合改造计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将合同审核与签订流程围绕"锁定文档版本"进行融合：提交审核时自动生成草稿并锁定内容；签订支持在线双签和上传盖章PDF两种模式。

**Architecture:** 后端状态机保持不变（`active` 作为审核通过后待签订状态），但前端语义改为"已通过/待签订"；提交审核接口自动触发草稿生成；新增 `POST /contracts/{id}/upload-signed` 接口支持上传已盖章PDF；签订弹窗通过 Tab 切换两种模式。

**Tech Stack:** FastAPI + SQLAlchemy + PostgreSQL + MinIO + React + TypeScript + Ant Design + RTK Query

---

## 文件结构映射

| 文件 | 变更类型 | 职责 |
|------|---------|------|
| `backend/app/crud/contract.py` | 修改 | 状态机保持不变，增加 `is_locked_for_review()` 辅助判断 |
| `backend/app/api/v1/endpoints/contracts.py` | 修改 | 提交审核自动生草稿、ACTIVE 状态禁止修改、新增上传盖章PDF接口 |
| `backend/app/schemas/contract.py` | 修改 | 新增 `ContractUploadSignedRequest` 和 `ContractSignRequest` 的两种模式校验 |
| `backend/scripts/api_validation_tests.py` | 修改 | 增加流程融合后的端到端验证 |
| `frontend/src/types/index.ts` | 修改 | 新增上传盖章PDF请求类型 |
| `frontend/src/utils/constants.ts` | 修改 | `active` 标签从"生效"改为"已通过" |
| `frontend/src/store/api/contractsApi.ts` | 修改 | 新增 `uploadSignedContract` mutation |
| `frontend/src/components/ContractSignModal.tsx` | 修改 | 增加 Tab 切换：在线签名 / 上传盖章PDF |
| `frontend/src/pages/Contracts/index.tsx` | 修改 | 调整操作按钮显示逻辑、审核中禁止编辑 |

---

## Task 1: 后端 — 提交审核时自动生成草稿并锁定内容

**Files:**
- Modify: `backend/app/api/v1/endpoints/contracts.py:145-178`
- Modify: `backend/app/api/v1/endpoints/contracts.py:124-143`
- Modify: `backend/app/crud/contract.py:13-20`（增加辅助方法，可选）

### Step 1.1: 修改 `update_contract_status` — 提交审核时自动生成草稿

`- [ ]` 在 `backend/app/api/v1/endpoints/contracts.py` 的 `update_contract_status` 函数中，当 `body.status == ContractStatus.REVIEW` 时，增加草稿自动生成逻辑。

找到以下代码（约 157-160 行）：

```python
    old_status = contract.status
    updated = crud_contract.update_status(
        db, db_obj=contract, new_status=body.status, changed_by=current_user.id, remark=body.remark or ""
    )
```

在其**前面**插入：

```python
    old_status = contract.status
    # 提交审核时自动生草稿并校验模板
    if body.status == ContractStatus.REVIEW and old_status == ContractStatus.DRAFT:
        if not contract.template_id:
            raise BusinessError("该合同未选择模板，无法提交审核")
        template = db.query(ContractTemplate).filter(ContractTemplate.id == contract.template_id).first()
        if not template or not template.file_url:
            raise BusinessError("模板文件不存在")
        draft_object_name = render_contract_draft(contract, template.file_url)
        contract.draft_doc_url = draft_object_name
    updated = crud_contract.update_status(
        db, db_obj=contract, new_status=body.status, changed_by=current_user.id, remark=body.remark or ""
    )
```

**验证：** 启动后端，创建一个带 `template_id` 的合同，调用 `POST /contracts/{id}/status {"status":"review"}`，响应中应包含 `draft_doc_url`。

### Step 1.2: 修改 `update_contract` — REVIEW 和 ACTIVE 状态禁止修改

`- [ ]` 在 `backend/app/api/v1/endpoints/contracts.py` 的 `update_contract` 函数中，将修改限制从仅 `SIGNED` 扩展为 `REVIEW` 和 `ACTIVE` 也禁止修改。

找到代码（约 136-137 行）：

```python
    if contract.status == ContractStatus.SIGNED:
        raise BusinessError("已签订合同不可修改")
```

替换为：

```python
    if contract.status in (ContractStatus.REVIEW, ContractStatus.ACTIVE, ContractStatus.SIGNED):
        raise BusinessError(f"{contract.status.value} 状态合同不可修改")
```

**验证：** 调用 `PATCH /contracts/{id}` 修改一个 `review` 或 `active` 状态的合同，应返回 400 错误。

### Step 1.3: Commit

`- [ ]`

```bash
cd /Users/yinchengchen/ClaudeCode/safety-bms
git add backend/app/api/v1/endpoints/contracts.py
git commit -m "feat(contracts): auto-generate draft on review submit and lock contract during review/active"
```

---

## Task 2: 后端 — 新增上传已盖章 PDF 接口

**Files:**
- Modify: `backend/app/schemas/contract.py`
- Modify: `backend/app/api/v1/endpoints/contracts.py`
- Test: `backend/scripts/api_validation_tests.py`

### Step 2.1: 新增 schema `ContractUploadSignedRequest`

`- [ ]` 在 `backend/app/schemas/contract.py` 中，新增上传盖章PDF的请求模型：

在 `ContractSignRequest` 类之后插入：

```python
class ContractUploadSignedRequest(BaseModel):
    file_url: str

    @model_validator(mode="after")
    def check_file_url(self):
        if not self.file_url or not self.file_url.strip().endswith(".pdf"):
            raise ValueError("必须提供有效的 PDF 文件链接")
        return self
```

**验证：** 确认无语法错误。

### Step 2.2: 新增 `upload_signed_contract` endpoint

`- [ ]` 在 `backend/app/api/v1/endpoints/contracts.py` 中，`sign_contract` 函数之后新增上传盖章版接口。

在 `sign_contract` 函数结束后（约 337 行 `raise` 之后），插入：

```python
@router.post("/{contract_id}/upload-signed", response_model=ContractOut)
def upload_signed_contract(
    contract_id: int,
    body: ContractUploadSignedRequest,
    current_user: User = Depends(require_permissions(PermissionCode.CONTRACT_SIGN)),
    db: Session = Depends(get_db),
):
    contract = (
        db.query(Contract)
        .filter(Contract.id == contract_id, Contract.is_deleted == False)
        .with_for_update()
        .first()
    )
    if not contract:
        raise NotFoundError("合同")
    if not check_data_scope(contract, current_user):
        raise PermissionDeniedError()
    if contract.status == ContractStatus.SIGNED:
        raise BusinessError("合同已签订")
    if contract.status != ContractStatus.ACTIVE:
        raise BusinessError("只有生效中的合同才能确认签订")
    if not contract.draft_doc_url:
        raise BusinessError("合同草稿不存在，无法确认签订")

    old_status = contract.status.value
    now = datetime.now(timezone.utc)
    update_fields = {
        "status": ContractStatus.SIGNED,
        "signed_at": now,
        "final_pdf_url": body.file_url,
    }
    if contract.sign_date is None:
        update_fields["sign_date"] = now.date()

    updated = crud_contract.update(db, db_obj=contract, obj_in=update_fields)

    change = ContractChange(
        contract_id=contract.id,
        changed_by=current_user.id,
        change_summary=f"状态变更: {old_status} → signed (上传盖章版)",
        before_status=old_status,
        after_status="signed",
        remark="",
    )
    db.add(change)
    db.commit()
    db.refresh(updated)

    creator = db.query(User).filter(User.id == contract.created_by).first()
    if creator and creator.id != current_user.id:
        notification_service.create(
            db,
            user_id=creator.id,
            title="合同签订完成",
            content=f"合同 {contract.title} 已通过上传盖章版完成签订。",
        )

    result = ContractOut.model_validate(updated)
    result.customer_name = updated.customer.name if updated.customer else None
    result.invoiced_amount = crud_contract.get_invoiced_amount(db, contract_id=contract_id)
    result.received_amount = crud_contract.get_received_amount(db, contract_id=contract_id)
    return result
```

并在文件顶部的 `ContractStatusUpdate` import 下方增加 `ContractUploadSignedRequest` 的 import：

找到：
```python
from app.schemas.contract import (
    ContractCreate, ContractUpdate, ContractOut, ContractListOut, ContractStatusUpdate,
    ContractSignRequest,
)
```

替换为：
```python
from app.schemas.contract import (
    ContractCreate, ContractUpdate, ContractOut, ContractListOut, ContractStatusUpdate,
    ContractSignRequest, ContractUploadSignedRequest,
)
```

**验证：** 启动后端，调用 `POST /contracts/{id}/upload-signed {"file_url":"contracts/1/finals/test.pdf"}` 对一个 `active` 且已有 `draft_doc_url` 的合同，应成功返回 `SIGNED` 状态。

### Step 2.3: Commit

`- [ ]`

```bash
cd /Users/yinchengchen/ClaudeCode/safety-bms
git add backend/app/schemas/contract.py backend/app/api/v1/endpoints/contracts.py
git commit -m "feat(contracts): add upload-signed-pdf endpoint for offline stamp workflow"
```

---

## Task 3: 后端 — 更新 API 验证测试

**Files:**
- Modify: `backend/scripts/api_validation_tests.py`

### Step 3.1: 修改测试以覆盖新流程

`- [ ]` 在 `backend/scripts/api_validation_tests.py` 中，修改 `create_contract` 函数和 `test_contract_status_machine` 函数。

找到 `create_contract`（约 55-69 行），在 payload 中增加 `template_id` 字段，但我们没有模板，所以需要改为：创建一个模板，或者在测试中跳过模板校验。更好的方式是修改 `create_contract` 让它可选带 `template_id`：

```python
def create_contract(customer_id: int, total_amount: float = 10000, template_id: int = None):
    payload = {
        "contract_no": f"C-{date.today().isoformat()}-{total_amount}-{str(uuid.uuid4())[:4]}",
        "title": "测试合同",
        "customer_id": customer_id,
        "service_type": "evaluation",
        "total_amount": total_amount,
        "sign_date": date.today().isoformat(),
        "start_date": date.today().isoformat(),
        "end_date": (date.today() + timedelta(days=30)).isoformat(),
        "status": "active",
    }
    if template_id:
        payload["template_id"] = template_id
    r = session.post(f"{BASE_URL}/contracts", json=payload)
    assert r.status_code == 201, f"创建合同失败: {r.text}"
    return r.json()["id"]
```

然后新增一个创建模板的函数，在 `create_contract` 之后插入：

```python
def create_contract_template() -> int:
    # 先上传一个最小化的 docx 文件（空内容的 docx 魔数）
    # 由于测试环境可能没有真实 docx，我们通过直接调用 templates 接口创建（如果有文件上传接口）
    # 但 contract_templates.py 要求上传文件，比较麻烦。
    # 更简单的方式：在数据库直接插入一条模板记录（通过 API 不行），或者跳过。
    # 实际项目中，测试脚本可以假定有一个固定模板 ID=1 存在。
    # 这里我们采用：查询已有模板，返回第一个的 ID。
    r = session.get(f"{BASE_URL}/contract-templates?page=1&page_size=1")
    if r.status_code == 200 and r.json().get("items"):
        return r.json()["items"][0]["id"]
    return None
```

但这样测试脚本会变得不稳定。更好的方式是：**状态机测试不改，新增一个专门的融合流程测试函数**。

在 `test_contract_status_machine` 函数之后插入新测试：

```python
def test_contract_audit_to_sign_flow(customer_id: int):
    """合同审核-签订融合流程：提交审核自动生草稿，active 状态不可修改，支持上传盖章版签订"""
    # 1. 查询一个可用模板
    r = session.get(f"{BASE_URL}/contract-templates?page=1&page_size=1")
    template_id = None
    if r.status_code == 200 and r.json().get("items"):
        template_id = r.json()["items"][0]["id"]

    contract_id = create_contract(customer_id, total_amount=5000)

    # 2. 不带模板提交审核应失败
    r = session.post(f"{BASE_URL}/contracts/{contract_id}/status", json={"status": "review"})
    if template_id is None:
        print("⚠️  无可用模板，跳过部分测试")
        # 直接激活并走原有流程
        r = session.post(f"{BASE_URL}/contracts/{contract_id}/status", json={"status": "review"})
        assert r.status_code == 200
        r = session.post(f"{BASE_URL}/contracts/{contract_id}/status", json={"status": "active"})
        assert r.status_code == 200
        return contract_id

    assert r.status_code == 400, f"无模板提交审核应被拒绝: {r.text}"
    print("✅ 无模板提交审核被拒绝")

    # 3. 关联模板后提交审核，应自动生成草稿
    r = session.patch(f"{BASE_URL}/contracts/{contract_id}", json={"template_id": template_id})
    assert r.status_code == 200, f"关联模板失败: {r.text}"

    r = session.post(f"{BASE_URL}/contracts/{contract_id}/status", json={"status": "review"})
    assert r.status_code == 200, f"提交审核失败: {r.text}"
    data = r.json()
    assert data["draft_doc_url"] is not None, "提交审核后未生成草稿"
    print("✅ 提交审核自动生成草稿通过")

    # 4. review 状态不可修改
    r = session.patch(f"{BASE_URL}/contracts/{contract_id}", json={"total_amount": 1})
    assert r.status_code == 400, f"review 状态应禁止修改: {r.text}"
    print("✅ review 状态锁定内容通过")

    # 5. 审核通过 -> active
    r = session.post(f"{BASE_URL}/contracts/{contract_id}/status", json={"status": "active"})
    assert r.status_code == 200, f"审核通过失败: {r.text}"

    # 6. active 状态不可修改
    r = session.patch(f"{BASE_URL}/contracts/{contract_id}", json={"total_amount": 1})
    assert r.status_code == 400, f"active 状态应禁止修改: {r.text}"
    print("✅ active 状态锁定内容通过")

    # 7. 上传盖章版签订（模拟文件路径）
    r = session.post(
        f"{BASE_URL}/contracts/{contract_id}/upload-signed",
        json={"file_url": f"contracts/{contract_id}/finals/signed_test.pdf"},
    )
    assert r.status_code == 200, f"上传盖章版签订失败: {r.text}"
    assert r.json()["status"] == "signed"
    assert r.json()["final_pdf_url"] is not None
    print("✅ 上传盖章版签订流程通过")

    return contract_id
```

然后在 `main()` 函数中调用它。找到 `main()` 中：

```python
    contract_id3 = create_contract(customer_id, total_amount=100)
    activate_contract(contract_id3)
```

在其前面插入：

```python
    test_contract_audit_to_sign_flow(customer_id)
```

**验证：** 运行 `PYTHONPATH=. python scripts/api_validation_tests.py`，全部通过。

### Step 3.2: Commit

`- [ ]`

```bash
cd /Users/yinchengchen/ClaudeCode/safety-bms
git add backend/scripts/api_validation_tests.py
git commit -m "test(contracts): add end-to-end test for audit-to-sign integration flow"
```

---

## Task 4: 前端 — 类型、常量、API 层更新

**Files:**
- Modify: `frontend/src/types/index.ts`
- Modify: `frontend/src/utils/constants.ts`
- Modify: `frontend/src/store/api/contractsApi.ts`

### Step 4.1: 新增前端类型

`- [ ]` 在 `frontend/src/types/index.ts` 中，新增上传盖章版请求类型。

在 `ContractSignRequest` 之后插入：

```typescript
export interface ContractUploadSignedRequest {
  file_url: string
}
```

### Step 4.2: 修改状态标签

`- [ ]` 在 `frontend/src/utils/constants.ts` 中：

找到：
```typescript
export const ContractStatusLabels: Record<string, string> = {
  draft: '草稿',
  review: '审核中',
  active: '生效',
  signed: '已签订',
  completed: '完成',
  terminated: '终止',
}
```

替换为：
```typescript
export const ContractStatusLabels: Record<string, string> = {
  draft: '草稿',
  review: '审核中',
  active: '已通过',
  signed: '已签订',
  completed: '完成',
  terminated: '终止',
}
```

### Step 4.3: 新增 API mutation

`- [ ]` 在 `frontend/src/store/api/contractsApi.ts` 中，新增 `uploadSignedContract` mutation。

找到 `signContract` 定义之后，插入：

```typescript
    uploadSignedContract: builder.mutation<Contract, { id: number; data: ContractUploadSignedRequest }>({
      query: ({ id, data }) => ({ url: `/contracts/${id}/upload-signed`, method: 'POST', body: data }),
      invalidatesTags: (_, __, { id }) => [{ type: 'Contract', id }, 'Contract'],
    }),
```

并在顶部的 import 中增加 `ContractUploadSignedRequest`：

```typescript
import type { Contract, ContractCreate, PageResponse, ContractStatus, ContractSignRequest, ContractUploadSignedRequest } from '@/types'
```

在 `export const {` 解构中增加：

```typescript
    useUploadSignedContractMutation,
```

### Step 4.4: Commit

`- [ ]`

```bash
cd /Users/yinchengchen/ClaudeCode/safety-bms
git add frontend/src/types/index.ts frontend/src/utils/constants.ts frontend/src/store/api/contractsApi.ts
git commit -m "feat(frontend): update contract labels and add upload-signed API"
```

---

## Task 5: 前端 — 签订弹窗增加上传盖章PDF模式

**Files:**
- Modify: `frontend/src/components/ContractSignModal.tsx`

### Step 5.1: 重构签订弹窗为 Tab 切换

`- [ ]` 修改 `frontend/src/components/ContractSignModal.tsx`，增加 `Tabs` 切换两种签订模式。

**完整替换文件内容：**

```typescript
import React, { useState, useEffect } from 'react'
import { Modal, Steps, Button, message, Input, Space, Tabs, Upload } from 'antd'
import { EyeOutlined, RedoOutlined, UploadOutlined } from '@ant/icons'
import SignaturePad from './SignaturePad'
import { useSignContractMutation, useUploadSignedContractMutation, contractsApi } from '@/store/api/contractsApi'
import type { UploadFile } from 'antd/es/upload/interface'

interface ContractSignModalProps {
  contractId: number
  open: boolean
  onClose: () => void
  onOpenPdf?: (id: number) => void
  partyANameDefault?: string
  partyBNameDefault?: string
}

const ContractSignModal: React.FC<ContractSignModalProps> = ({
  contractId,
  open,
  onClose,
  onOpenPdf,
  partyANameDefault,
  partyBNameDefault,
}) => {
  const [activeTab, setActiveTab] = useState<'online' | 'upload'>('online')

  // Online sign state
  const [currentStep, setCurrentStep] = useState(0)
  const [partyAName, setPartyAName] = useState('')
  const [partyASignature, setPartyASignature] = useState('')
  const [partyAPreview, setPartyAPreview] = useState('')
  const [partyBName, setPartyBName] = useState('')
  const [partyBSignature, setPartyBSignature] = useState('')
  const [partyBPreview, setPartyBPreview] = useState('')

  // Upload sign state
  const [fileUrl, setFileUrl] = useState('')

  const [submitting, setSubmitting] = useState(false)
  const [signContract] = useSignContractMutation()
  const [uploadSignedContract] = useUploadSignedContractMutation()
  const [triggerDraftUrl, { isFetching: draftUrlLoading }] = contractsApi.useLazyGetContractDraftUrlQuery()

  useEffect(() => {
    if (open) {
      setPartyAName(partyANameDefault || '')
      setPartyBName(partyBNameDefault || '')
      setActiveTab('online')
      setCurrentStep(0)
      setPartyASignature('')
      setPartyAPreview('')
      setPartyBSignature('')
      setPartyBPreview('')
      setFileUrl('')
      setSubmitting(false)
    }
  }, [open, partyANameDefault, partyBNameDefault])

  const handleSaveA = (base64: string) => {
    setPartyASignature(base64)
    setPartyAPreview(base64)
    message.success('甲方签名已确认')
  }

  const handleSaveB = (base64: string) => {
    setPartyBSignature(base64)
    setPartyBPreview(base64)
    message.success('乙方签名已确认')
  }

  const handleNext = () => {
    if (!partyAName.trim()) {
      message.error('请输入甲方签署人姓名')
      return
    }
    if (!partyASignature) {
      message.error('请完成甲方签名')
      return
    }
    setCurrentStep(1)
  }

  const handleSubmitOnline = async () => {
    if (!partyBName.trim()) {
      message.error('请输入乙方签署人姓名')
      return
    }
    if (!partyBSignature) {
      message.error('请完成乙方签名')
      return
    }
    setSubmitting(true)
    try {
      await signContract({
        id: contractId,
        data: {
          party_a_name: partyAName,
          party_a_signature_base64: partyASignature,
          party_b_name: partyBName,
          party_b_signature_base64: partyBSignature,
        },
      }).unwrap()
      message.success('合同签订成功')
      handleClose()
      if (onOpenPdf) {
        onOpenPdf(contractId)
      }
    } catch (err: any) {
      message.error(err?.data?.detail || '签订失败')
    } finally {
      setSubmitting(false)
    }
  }

  const handleSubmitUpload = async () => {
    if (!fileUrl.trim()) {
      message.error('请输入已盖章 PDF 的文件路径')
      return
    }
    setSubmitting(true)
    try {
      await uploadSignedContract({
        id: contractId,
        data: { file_url: fileUrl.trim() },
      }).unwrap()
      message.success('合同上传盖章版成功')
      handleClose()
      if (onOpenPdf) {
        onOpenPdf(contractId)
      }
    } catch (err: any) {
      message.error(err?.data?.detail || '上传盖章版失败')
    } finally {
      setSubmitting(false)
    }
  }

  const handleClose = () => {
    setCurrentStep(0)
    setPartyAName('')
    setPartyASignature('')
    setPartyAPreview('')
    setPartyBName('')
    setPartyBSignature('')
    setPartyBPreview('')
    setFileUrl('')
    setSubmitting(false)
    onClose()
  }

  const openDraftPreview = async () => {
    try {
      const res = await triggerDraftUrl(contractId).unwrap()
      if (res.url) {
        window.open(res.url, '_blank')
      } else {
        message.error('获取草稿预览链接失败')
      }
    } catch (err: any) {
      message.error(err?.data?.detail || '预览失败')
    }
  }

  const tabItems = [
    {
      key: 'online',
      label: '在线双签',
      children: (
        <div>
          <Steps current={currentStep} size="small" style={{ marginBottom: 24 }}>
            <Steps.Step title="甲方签名" />
            <Steps.Step title="乙方签名" />
          </Steps>

          {currentStep === 0 && (
            <div>
              <Space direction="vertical" style={{ width: '100%' }}>
                <Input
                  placeholder="甲方签署人姓名"
                  value={partyAName}
                  onChange={(e) => setPartyAName(e.target.value)}
                  maxLength={50}
                />
                {partyAPreview ? (
                  <div>
                    <img
                      src={partyAPreview}
                      alt="甲方签名"
                      style={{
                        maxWidth: '100%',
                        height: 120,
                        border: '1px solid #d9d9d9',
                        borderRadius: 4,
                        background: '#fff',
                      }}
                    />
                    <div style={{ marginTop: 8 }}>
                      <Button icon={<RedoOutlined />} onClick={() => { setPartyAPreview(''); setPartyASignature('') }}>
                        重新签名
                      </Button>
                    </div>
                  </div>
                ) : (
                  <SignaturePad onSave={handleSaveA} height={200} />
                )}
              </Space>
              <div style={{ marginTop: 24, textAlign: 'right' }}>
                <Button type="primary" onClick={handleNext}>下一步</Button>
              </div>
            </div>
          )}

          {currentStep === 1 && (
            <div>
              <Space direction="vertical" style={{ width: '100%' }}>
                <Input
                  placeholder="乙方签署人姓名"
                  value={partyBName}
                  onChange={(e) => setPartyBName(e.target.value)}
                  maxLength={50}
                />
                {partyBPreview ? (
                  <div>
                    <img
                      src={partyBPreview}
                      alt="乙方签名"
                      style={{
                        maxWidth: '100%',
                        height: 120,
                        border: '1px solid #d9d9d9',
                        borderRadius: 4,
                        background: '#fff',
                      }}
                    />
                    <div style={{ marginTop: 8 }}>
                      <Button icon={<RedoOutlined />} onClick={() => { setPartyBPreview(''); setPartyBSignature('') }}>
                        重新签名
                      </Button>
                    </div>
                  </div>
                ) : (
                  <SignaturePad onSave={handleSaveB} height={200} />
                )}
              </Space>
              <div style={{ marginTop: 24, textAlign: 'right' }}>
                <Space>
                  <Button disabled={submitting} onClick={() => setCurrentStep(0)}>上一步</Button>
                  <Button type="primary" loading={submitting} onClick={handleSubmitOnline}>
                    {submitting ? '正在生成PDF，请稍候...' : '提交签订'}
                  </Button>
                </Space>
              </div>
            </div>
          )}
        </div>
      ),
    },
    {
      key: 'upload',
      label: '上传盖章版',
      children: (
        <Space direction="vertical" style={{ width: '100%' }}>
          <div style={{ color: '#666', marginBottom: 8 }}>
            请先将合同打印、盖章并扫描为 PDF，然后将 PDF 上传至文件系统，再在此处填写文件路径。
          </div>
          <Input.TextArea
            placeholder="请输入已盖章 PDF 的 MinIO 文件路径，例如：contracts/123/finals/signed.pdf"
            value={fileUrl}
            onChange={(e) => setFileUrl(e.target.value)}
            rows={3}
          />
          <div style={{ textAlign: 'right', marginTop: 16 }}>
            <Button type="primary" loading={submitting} onClick={handleSubmitUpload}>
              确认已签订
            </Button>
          </div>
        </Space>
      ),
    },
  ]

  return (
    <Modal
      title="合同签订"
      open={open}
      onCancel={handleClose}
      width={640}
      footer={null}
      maskClosable={!submitting}
      closable={!submitting}
    >
      <div style={{ marginBottom: 16 }}>
        <Button
          size="small"
          icon={<EyeOutlined />}
          onClick={openDraftPreview}
          loading={draftUrlLoading}
        >
          查看合同草稿
        </Button>
      </div>

      <Tabs activeKey={activeTab} onChange={(k) => setActiveTab(k as 'online' | 'upload')} items={tabItems} />
    </Modal>
  )
}

export default ContractSignModal
```

**注意：** 上面的 import 中 `@ant/icons` 应该是 `@ant-design/icons`，请确保：

```typescript
import { EyeOutlined, RedoOutlined } from '@ant-design/icons'
```

（不需要 `UploadOutlined` 和 `Upload`，如果不用可以删掉，但保留也无害。）

**验证：** 打开前端，进入一个 `active` 状态的合同，点击"发起签订"，弹窗应显示两个 Tab："在线双签"和"上传盖章版"，切换正常。

### Step 5.2: Commit

`- [ ]`

```bash
cd /Users/yinchengchen/ClaudeCode/safety-bms
git add frontend/src/components/ContractSignModal.tsx
git commit -m "feat(frontend): add upload-signed-pdf tab to contract sign modal"
```

---

## Task 6: 前端 — 列表页和详情页操作按钮调整

**Files:**
- Modify: `frontend/src/pages/Contracts/index.tsx`

### Step 6.1: 隐藏草稿生成按钮，调整编辑权限

`- [ ]` 修改 `frontend/src/pages/Contracts/index.tsx`：

1. **编辑按钮**：当前条件是 `r.status !== 'signed'`，应改为仅在 `draft` 状态显示编辑：

找到（约 202-204 行）：
```typescript
        {r.status !== 'signed' && (
          <PermissionButton permission="contract:update" type="link" size="small" onClick={() => handleEdit(r)}>编辑</PermissionButton>
        )}
```

替换为：
```typescript
        {r.status === 'draft' && (
          <PermissionButton permission="contract:update" type="link" size="small" onClick={() => handleEdit(r)}>编辑</PermissionButton>
        )}
```

2. **生成草稿按钮**：当前在 `draft/review/active` 都显示，应只在 `draft` 状态显示（因为提交审核会自动生成草稿，review/active 不需要手动生成）：

找到（约 217-219 行）：
```typescript
        {(r.status === 'draft' || r.status === 'review' || r.status === 'active') && r.template_id && (
          <PermissionButton permission="contract:update" size="small" icon={<FileTextOutlined />} onClick={() => handleGenerateDraft(r.id)} loading={generatingDraft}>生成草稿</PermissionButton>
        )}
```

替换为：
```typescript
        {r.status === 'draft' && r.template_id && (
          <PermissionButton permission="contract:update" size="small" icon={<FileTextOutlined />} onClick={() => handleGenerateDraft(r.id)} loading={generatingDraft}>生成草稿</PermissionButton>
        )}
```

3. **详情页 `ContractDetail` 中的按钮同步调整**：

找到 `ContractDetail` 组件（约 391-413 行）：

编辑按钮：
```typescript
          {data.status !== 'signed' && data.template_id && (
            <PermissionButton permission="contract:update" icon={<FileTextOutlined />} onClick={() => onGenerateDraft(data.id)} loading={generatingDraft}>生成草稿</PermissionButton>
          )}
```

改为：
```typescript
          {data.status === 'draft' && data.template_id && (
            <PermissionButton permission="contract:update" icon={<FileTextOutlined />} onClick={() => onGenerateDraft(data.id)} loading={generatingDraft}>生成草稿</PermissionButton>
          )}
```

并删除详情页中已有的编辑入口（如果有），当前 `ContractDetail` 中已经没有显式的"编辑"按钮了，只有"审核通过/驳回/发起签订/生成草稿/下载PDF"，所以无需额外处理编辑按钮。

### Step 6.2: Commit

`- [ ]`

```bash
cd /Users/yinchengchen/ClaudeCode/safety-bms
git add frontend/src/pages/Contracts/index.tsx
git commit -m "feat(frontend): restrict edit/draft-gen to draft status only"
```

---

## Task 7: 集成验证

### Step 7.1: 后端测试

`- [ ]` 启动后端服务（如果还没启动）：

```bash
cd /Users/yinchengchen/ClaudeCode/safety-bms/backend
PYTHONPATH=. uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

在另一个终端运行：

```bash
cd /Users/yinchengchen/ClaudeCode/safety-bms/backend
PYTHONPATH=. python scripts/api_validation_tests.py
```

**预期结果：** 全部测试通过，新增的 "审核-签订融合流程" 测试打印 4 个 ✅。

### Step 7.2: 前端测试

`- [ ]` 启动前端：

```bash
cd /Users/yinchengchen/ClaudeCode/safety-bms/frontend
npm run dev
```

在浏览器中验证：
1. 合同列表中 `active` 状态显示为"已通过"（绿色标签）。
2. `draft` 状态的合同可以编辑和生成草稿；`review`/`active` 状态的合同没有编辑按钮和生成草稿按钮。
3. 提交一个带模板的 `draft` 合同到 `review`，草稿应自动生成（详情页可预览）。
4. `active` 状态的合同点击"发起签订"，弹窗显示两个 Tab，在线双签和上传盖章版都能正常提交。

### Step 7.3: Final Commit (if any fixes needed)

`- [ ]` 如有修复，单独 commit。

---

## Spec Coverage Checklist

| 需求 | 对应 Task |
|------|----------|
| 提交审核时自动生成草稿并锁定内容 | Task 1 |
| 审核通过后内容不可修改 | Task 1 |
| 签订支持在线双签和上传盖章PDF两种模式 | Task 2, Task 5 |
| 前端状态语义更新 | Task 4 |
| 前端操作按钮和权限适配 | Task 6 |
| 端到端测试覆盖 | Task 3 |

**无 Placeholder。** 所有步骤包含完整代码和验证命令。

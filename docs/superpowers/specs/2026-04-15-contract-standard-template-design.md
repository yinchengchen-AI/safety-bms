# 固定标准合同模板功能设计文档

## 1. 概述

在 `safety-bms` 系统中引入「固定标准合同模板」功能。当业务人员将合同提交审核时，系统自动根据默认的 Word 模板（`.docx`）填充合同数据，生成一份标准合同草稿并存储到 MinIO，供后续下载使用。

## 2. 目标

- 基于已有的 `安全生产社会化服务_template.docx`（已制作完成并放置于 `backend/templates/contracts/`），使用 `docxtpl` 实现自动化填充。
- 在合同提交审核（状态流转至 `review`）时，自动触发标准合同草稿生成。
- 前端在合同详情页提供下载入口，无需额外按钮或页面跳转。
- 模板渲染失败不得阻断合同提交审核的主业务流。

## 3. 模板文件与占位符映射

模板文件路径（预置资产）：
```
backend/templates/contracts/安全生产社会化服务_template.docx
```

已注入的 Jinja2 占位符及映射规则：

| 占位符 | 数据来源 | 说明 |
|--------|----------|------|
| `{{contract_reg_no}}` | `contract.contract_no` | 合同编号 |
| `{{party_a_name}}` | `contract.customer.name` | 甲方（客户）名称 |
| `{{sign_location}}` | `f"{customer.city or ''}{customer.district or ''}"` | 客户城市 + 区县拼接 |
| `{{sign_year}}` | `contract.sign_date.year` | 签订日期-年 |
| `{{sign_month}}` | `contract.sign_date.month` | 签订日期-月 |
| `{{sign_day}}` | `contract.sign_date.day` | 签订日期-日 |
| `{{valid_start_year}}` | `contract.valid_start.year` | 有效期起-年 |
| `{{valid_start_month}}` | `contract.valid_start.month` | 有效期起-月 |
| `{{valid_start_day}}` | `contract.valid_start.day` | 有效期起-日 |
| `{{valid_end_year}}` | `contract.valid_end.year` | 有效期止-年 |
| `{{valid_end_month}}` | `contract.valid_end.month` | 有效期止-月 |
| `{{valid_end_day}}` | `contract.valid_end.day` | 有效期止-日 |
| `{{service_start_year}}` | `contract.service_start.year` | 服务期起-年 |
| `{{service_start_month}}` | `contract.service_start.month` | 服务期起-月 |
| `{{service_start_day}}` | `contract.service_start.day` | 服务期起-日 |
| `{{service_end_year}}` | `contract.service_end.year` | 服务期止-年 |
| `{{service_end_month}}` | `contract.service_end.month` | 服务期止-月 |
| `{{service_end_day}}` | `contract.service_end.day` | 服务期止-日 |
| `{{total_amount}}` | `contract.total_amount` | 合同总金额（数字） |
| `{{total_amount_upper}}` | `number_to_chinese_upper(contract.total_amount)` | 合同总金额中文大写 |
| `{{payment_amount}}` | `contract.total_amount`（首期款，默认等于总金额，后续可扩展） | 付款金额 |
| `{{service_address}}` | `contract.service_address or customer.address or ""` | 服务地点 |

> **注**：金额大写函数 `number_to_chinese_upper(amount: Decimal | float | int) -> str` 为内置标准实现，支持到分（角、分），例如 `12345.67` → `壹万贰仟叁佰肆拾伍元陆角柒分`。

## 4. 后端渲染流程

### 4.1 数据模型与存储

复用现有的 `ContractTemplate` 模型和 `contract_templates` 表：
- 新增一条默认记录（通过 `init_db.py` 或 migration seed 插入），`name="安全生产社会化服务标准模板"`，`is_default=true`，`file_url` 指向 MinIO 中预上传的模板文件。
- `Contract` 模型已包含 `template_id`（可空外键）。当合同使用标准模板生成草稿时，不强制设置 `template_id`，保持其为 `NULL`；仅当用户显式选择某个模板时才赋值。
- 生成的草稿文件通过 MinIO 存储，URL 回写到合同的 `standard_doc_url` 字段（需新增该字段，类型 `String`, nullable）。

### 4.2 渲染服务扩展

在 `backend/app/services/contract_doc_service.py` 中新增：

```python
def render_standard_contract_draft(contract: Contract, db: Session) -> str | None:
    """
    查找默认模板，渲染标准合同草稿，上传 MinIO，返回文件 URL。
    若找不到默认模板或渲染失败，返回 None 并记录日志。
    """

def _build_standard_contract_context(contract: Contract) -> dict:
    """
    将合同对象转换为 docxtpl 所需的上下文字典。
    """

def number_to_chinese_upper(amount) -> str:
    """
    数字金额转中文大写。
    """
```

渲染流程：
1. 查询 `db.query(ContractTemplate).filter_by(is_default=True, is_active=True).first()`。
2. 若未找到，记录 `logger.warning` 并返回 `None`。
3. 从 MinIO 下载模板字节流，用 `DocxTemplate` 加载。
4. 调用 `_build_standard_contract_context(contract)` 构建上下文。
5. 执行 `doc.render(context)`，保存到临时文件。
6. 上传临时文件到 MinIO（key 建议为 `contracts/standard_drafts/{contract.id}_{timestamp}.docx`）。
7. 返回 MinIO 的 `file_url`，由调用方写入 `contract.standard_doc_url`。

### 4.3 状态流转 Hook

在 `backend/app/api/v1/endpoints/contracts.py` 的 `update_contract_status` 中：

当目标状态为 `ContractStatus.REVIEW` 且当前合同 `template_id is None` 时：
```python
if new_status == ContractStatus.REVIEW and contract.template_id is None:
    try:
        file_url = contract_doc_service.render_standard_contract_draft(contract, db)
        if file_url:
            contract.standard_doc_url = file_url
            db.commit()
            db.refresh(contract)
    except Exception:
        logger.exception("标准合同草稿生成失败，不影响审核提交")
```

> 状态机校验、权限校验、现有 `with_for_update()` 加锁逻辑均保持不变。

## 5. 前端交互

变更范围集中在 `frontend/src/pages/Contracts/index.tsx` 的 `ContractDetail` 组件。

1. **基本信息 Tab 新增区域**：
   - 若 `contract.standard_doc_url` 存在：显示「标准合同草稿」+ 文件名（或固定文案）+「下载」按钮（点击 `window.open(contract.standard_doc_url, '_blank')`）。
   - 若不存在：显示灰色提示「尚未生成标准合同草稿（提交审核后自动生成）」。
2. **提交审核按钮**：保持现有位置和样式。点击后调用 `updateContractStatus({ id, status: 'review' })`，成功提示改为 `message.success('已提交审核，标准合同草稿已生成')`，然后 `refetch()` 刷新详情。
3. **合同模板管理页** (`ContractTemplates/index.tsx`)：无需改动，继续支持上传 `.docx` 并标记默认模板。

## 6. 错误处理

采用「失败不阻断主业务流，但明确记录与提示」的策略：

1. **缺少默认模板**：`render_standard_contract_draft` 返回 `None`，合同仍可正常提交审核。前端详情页不显示下载入口。
2. **模板渲染失败**（`docxtpl` 异常、字段缺失、MinIO 上传失败）：`update_contract_status` 中用 `try/except` 包裹渲染调用，捕获后记录 `error` 日志，向上不抛异常，合同状态流转成功。
3. **字段缺失**：`_build_standard_contract_context` 中对可能为空的字段（`city`, `district`, `service_address` 等）统一做 `or ""` 回退，避免 `None` 注入模板导致渲染错误。

## 7. 测试与验证

### 7.1 单元测试

文件：`backend/app/tests/services/test_number_to_chinese_upper.py`

覆盖用例：
- 整数：`0` → `零元整`；`100000` → `壹拾万元整`；`1004` → `壹仟零肆元整`。
- 带角分：`1234.56` → `壹仟贰佰叁拾肆元伍角陆分`；`0.07` → `柒分`。
- 壹拾规则：`10` → `壹拾元整`；`1010` → `壹仟零壹拾元整`。

### 7.2 集成测试

在 API validation tests 或独立测试文件中：
1. 构造一个完整合同及客户数据（含所有日期字段和金额）。
2. 调用 `render_standard_contract_draft(contract, db)`。
3. 断言返回的 URL 非空，且下载后的 `.docx` 可以用 `python-docx` 读取，段落文本中包含 `contract_no`、`customer.name`、金额大写等关键字。

### 7.3 手工验证清单

- [ ] 管理员在「合同模板」页上传 `安全生产社会化服务_template.docx` 并设为默认。
- [ ] 创建一条新合同，填写客户、金额、日期、服务地址。
- [ ] 点击「提交审核」，提示成功。
- [ ] 进入合同详情，基本信息中出现「下载标准合同草稿」按钮。
- [ ] 下载并打开 Word 文档，检查所有占位符已正确替换，合同内容与原文件一致。

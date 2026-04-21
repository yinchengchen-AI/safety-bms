from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field, model_validator

from app.core.constants import ContractStatus, PaymentPlan


class ContractBase(BaseModel):
    contract_no: str
    title: str
    customer_id: int
    service_type: int
    total_amount: Decimal
    payment_plan: PaymentPlan = PaymentPlan.ONCE
    start_date: date | None = None
    end_date: date | None = None
    sign_date: date | None = None
    content: str | None = None
    remark: str | None = None

    @model_validator(mode="after")
    def check_dates(self):
        if self.start_date and self.end_date and self.start_date > self.end_date:
            raise ValueError("结束日期不能早于开始日期")
        if self.sign_date and self.end_date and self.sign_date > self.end_date:
            raise ValueError("结束日期不能早于签订日期")
        return self


class ContractCreate(ContractBase):
    template_id: int | None = None


class ContractUpdate(BaseModel):
    contract_no: str | None = None
    title: str | None = None
    total_amount: Decimal | None = None
    payment_plan: PaymentPlan | None = None
    start_date: date | None = None
    end_date: date | None = None
    sign_date: date | None = None
    content: str | None = None
    remark: str | None = None
    file_url: str | None = None
    template_id: int | None = None

    @model_validator(mode="after")
    def check_dates(self):
        if self.start_date and self.end_date and self.start_date > self.end_date:
            raise ValueError("结束日期不能早于开始日期")
        if self.sign_date and self.end_date and self.sign_date > self.end_date:
            raise ValueError("结束日期不能早于签订日期")
        return self


class ContractAttachmentCreate(BaseModel):
    file_name: str
    file_url: str
    file_type: Literal["draft", "signed", "other"]
    remark: str | None = None


class ContractAttachmentOut(BaseModel):
    id: int
    contract_id: int
    file_name: str
    file_url: str
    file_type: str
    remark: str | None = None
    uploaded_by: int | None = None
    uploaded_at: datetime

    model_config = {"from_attributes": True}


class ContractStatusUpdate(BaseModel):
    status: ContractStatus
    remark: str | None = None


class ContractTemplateCreate(BaseModel):
    name: str
    service_type: int
    is_default: bool = False


class ContractTemplateOut(BaseModel):
    id: int
    name: str
    service_type: int
    service_type_id: int | None = None
    service_type_name: str | None = None
    service_type_code: str | None = None
    file_url: str | None = None
    is_default: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class ContractSignatureOut(BaseModel):
    id: int
    contract_id: int
    party: str
    signed_by: str | None = None
    signature_url: str
    signed_at: datetime

    model_config = {"from_attributes": True}


class ContractSignRequest(BaseModel):
    party_a_name: str
    party_a_signature_base64: str
    party_b_name: str
    party_b_signature_base64: str
    sign_date: date | None = None

    @model_validator(mode="after")
    def check_signature_size(self):
        # base64 长度约为原始字节的 4/3，2MB ≈ 2.8MB base64 字符串
        max_base64_len = 3 * 1024 * 1024
        for field in ["party_a_signature_base64", "party_b_signature_base64"]:
            value = getattr(self, field)
            if value and len(value) > max_base64_len:
                raise ValueError("单张签名图片过大，请压缩后重新上传")
        return self


class ContractSingleSignRequest(BaseModel):
    party: str = Field(..., pattern="^(party_a|party_b)$")
    signed_by: str
    signature_base64: str

    @model_validator(mode="after")
    def check_signature_size(self):
        max_base64_len = 3 * 1024 * 1024
        if self.signature_base64 and len(self.signature_base64) > max_base64_len:
            raise ValueError("签名图片过大，请压缩后重新上传")
        return self


class ContractUploadSignedRequest(BaseModel):
    file_url: str
    sign_date: date | None = None

    @model_validator(mode="after")
    def check_file_url(self):
        if not self.file_url or not self.file_url.strip().endswith(".pdf"):
            raise ValueError("必须提供有效的 PDF 文件链接")
        return self


class ContractOut(ContractBase):
    id: int
    status: ContractStatus
    file_url: str | None = None
    template_id: int | None = None
    standard_doc_url: str | None = None
    draft_doc_url: str | None = None
    final_pdf_url: str | None = None
    signed_at: datetime | None = None
    created_at: datetime
    customer_name: str | None = None
    signatures: list[ContractSignatureOut] = Field(default_factory=list)
    attachments: list[ContractAttachmentOut] = Field(default_factory=list)
    # 统计字段（由service层计算）
    invoiced_amount: Decimal | None = None
    received_amount: Decimal | None = None
    service_type_id: int | None = None
    service_type_name: str | None = None
    service_type_code: str | None = None

    model_config = {"from_attributes": True}


class ContractListOut(BaseModel):
    id: int
    contract_no: str
    title: str
    customer_id: int
    customer_name: str | None = None
    service_type: int
    service_type_id: int | None = None
    service_type_name: str | None = None
    service_type_code: str | None = None
    total_amount: Decimal
    payment_plan: PaymentPlan
    status: ContractStatus
    sign_date: date | None = None
    start_date: date | None = None
    end_date: date | None = None
    template_id: int | None = None
    standard_doc_url: str | None = None
    draft_doc_url: str | None = None
    final_pdf_url: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}

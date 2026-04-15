from typing import Optional, List
from pydantic import BaseModel, model_validator
from datetime import datetime, date
from decimal import Decimal

from app.core.constants import ContractStatus, PaymentPlan


class ContractBase(BaseModel):
    contract_no: str
    title: str
    customer_id: int
    service_type: int
    total_amount: Decimal
    payment_plan: PaymentPlan = PaymentPlan.ONCE
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    sign_date: Optional[date] = None
    content: Optional[str] = None
    remark: Optional[str] = None

    @model_validator(mode="after")
    def check_dates(self):
        if self.start_date and self.end_date and self.start_date > self.end_date:
            raise ValueError("结束日期不能早于开始日期")
        if self.sign_date and self.end_date and self.sign_date > self.end_date:
            raise ValueError("结束日期不能早于签订日期")
        return self


class ContractCreate(ContractBase):
    template_id: Optional[int] = None


class ContractUpdate(BaseModel):
    contract_no: Optional[str] = None
    title: Optional[str] = None
    total_amount: Optional[Decimal] = None
    payment_plan: Optional[PaymentPlan] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    sign_date: Optional[date] = None
    content: Optional[str] = None
    remark: Optional[str] = None
    file_url: Optional[str] = None
    template_id: Optional[int] = None

    @model_validator(mode="after")
    def check_dates(self):
        if self.start_date and self.end_date and self.start_date > self.end_date:
            raise ValueError("结束日期不能早于开始日期")
        if self.sign_date and self.end_date and self.sign_date > self.end_date:
            raise ValueError("结束日期不能早于签订日期")
        return self


class ContractStatusUpdate(BaseModel):
    status: ContractStatus
    remark: Optional[str] = None


class ContractTemplateCreate(BaseModel):
    name: str
    service_type: int
    is_default: bool = False


class ContractTemplateOut(BaseModel):
    id: int
    name: str
    service_type: int
    service_type_id: int
    service_type_name: Optional[str] = None
    service_type_code: Optional[str] = None
    file_url: str
    is_default: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class ContractSignatureOut(BaseModel):
    id: int
    contract_id: int
    party: str
    signed_by: Optional[str] = None
    signature_url: str
    signed_at: datetime

    model_config = {"from_attributes": True}


class ContractSignRequest(BaseModel):
    party_a_name: str
    party_a_signature_base64: str
    party_b_name: str
    party_b_signature_base64: str

    @model_validator(mode="after")
    def check_signature_size(self):
        # base64 长度约为原始字节的 4/3，2MB ≈ 2.8MB base64 字符串
        max_base64_len = 3 * 1024 * 1024
        for field in ["party_a_signature_base64", "party_b_signature_base64"]:
            value = getattr(self, field)
            if value and len(value) > max_base64_len:
                raise ValueError("单张签名图片过大，请压缩后重新上传")
        return self


class ContractUploadSignedRequest(BaseModel):
    file_url: str

    @model_validator(mode="after")
    def check_file_url(self):
        if not self.file_url or not self.file_url.strip().endswith(".pdf"):
            raise ValueError("必须提供有效的 PDF 文件链接")
        return self


class ContractOut(ContractBase):
    id: int
    status: ContractStatus
    file_url: Optional[str] = None
    template_id: Optional[int] = None
    standard_doc_url: Optional[str] = None
    draft_doc_url: Optional[str] = None
    final_pdf_url: Optional[str] = None
    signed_at: Optional[datetime] = None
    created_at: datetime
    customer_name: Optional[str] = None
    signatures: List[ContractSignatureOut] = []
    # 统计字段（由service层计算）
    invoiced_amount: Optional[Decimal] = None
    received_amount: Optional[Decimal] = None
    service_type_id: Optional[int] = None
    service_type_name: Optional[str] = None
    service_type_code: Optional[str] = None

    model_config = {"from_attributes": True}


class ContractListOut(BaseModel):
    id: int
    contract_no: str
    title: str
    customer_id: int
    customer_name: Optional[str] = None
    service_type: int
    service_type_id: Optional[int] = None
    service_type_name: Optional[str] = None
    service_type_code: Optional[str] = None
    total_amount: Decimal
    payment_plan: PaymentPlan
    status: ContractStatus
    sign_date: Optional[date] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    template_id: Optional[int] = None
    standard_doc_url: Optional[str] = None
    draft_doc_url: Optional[str] = None
    final_pdf_url: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}

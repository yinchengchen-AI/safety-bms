from datetime import datetime

from pydantic import BaseModel, EmailStr, field_validator

from app.core.constants import CustomerStatus


class CustomerContactBase(BaseModel):
    name: str
    position: str | None = None
    phone: str | None = None
    email: EmailStr | None = None
    is_primary: bool = False


class CustomerContactCreate(CustomerContactBase):
    pass


class CustomerContactOut(CustomerContactBase):
    id: int
    customer_id: int
    created_at: datetime

    model_config = {"from_attributes": True}


class CustomerFollowUpCreate(BaseModel):
    content: str
    follow_up_at: datetime
    next_follow_up_at: datetime | None = None


class CustomerFollowUpOut(CustomerFollowUpCreate):
    id: int
    customer_id: int
    creator_id: int | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class CustomerBase(BaseModel):
    name: str
    credit_code: str | None = None
    industry: str | None = None
    scale: str | None = None
    province: str | None = None
    city: str | None = None
    district: str | None = None
    street: str | None = None
    address: str | None = None
    website: str | None = None
    contact_name: str | None = None
    contact_phone: str | None = None
    status: CustomerStatus = CustomerStatus.PROSPECT
    remark: str | None = None

    @field_validator("credit_code")
    @classmethod
    def validate_credit_code(cls, v: str | None) -> str | None:
        if v is not None and v != "":
            if len(v) != 18:
                raise ValueError("统一社会信用代码长度必须为18位")
            if not v[:-1].isalnum():
                raise ValueError("统一社会信用代码前17位必须为字母或数字")
        return v


class CustomerCreate(CustomerBase):
    contacts: list[CustomerContactCreate] = []


class CustomerUpdate(BaseModel):
    name: str | None = None
    credit_code: str | None = None
    industry: str | None = None
    scale: str | None = None
    province: str | None = None
    city: str | None = None
    district: str | None = None
    street: str | None = None
    address: str | None = None
    website: str | None = None
    contact_name: str | None = None
    contact_phone: str | None = None
    status: CustomerStatus | None = None
    remark: str | None = None


class CustomerOut(CustomerBase):
    id: int
    created_at: datetime
    contacts: list[CustomerContactOut] = []

    model_config = {"from_attributes": True}


class CustomerListOut(CustomerBase):
    id: int
    created_at: datetime

    model_config = {"from_attributes": True}

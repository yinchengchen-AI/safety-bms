from typing import List, Optional
from pydantic import BaseModel, field_validator, EmailStr
from datetime import datetime

from app.core.constants import CustomerStatus


class CustomerContactBase(BaseModel):
    name: str
    position: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
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
    next_follow_up_at: Optional[datetime] = None


class CustomerFollowUpOut(CustomerFollowUpCreate):
    id: int
    customer_id: int
    creator_id: Optional[int] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class CustomerBase(BaseModel):
    name: str
    credit_code: Optional[str] = None
    industry: Optional[str] = None
    scale: Optional[str] = None
    province: Optional[str] = None
    city: Optional[str] = None
    district: Optional[str] = None
    street: Optional[str] = None
    address: Optional[str] = None
    website: Optional[str] = None
    contact_name: Optional[str] = None
    contact_phone: Optional[str] = None
    status: CustomerStatus = CustomerStatus.PROSPECT
    remark: Optional[str] = None

    @field_validator("credit_code")
    @classmethod
    def validate_credit_code(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v != "":
            if len(v) != 18:
                raise ValueError("统一社会信用代码长度必须为18位")
            if not v[:-1].isalnum():
                raise ValueError("统一社会信用代码前17位必须为字母或数字")
        return v


class CustomerCreate(CustomerBase):
    contacts: List[CustomerContactCreate] = []


class CustomerUpdate(BaseModel):
    name: Optional[str] = None
    credit_code: Optional[str] = None
    industry: Optional[str] = None
    scale: Optional[str] = None
    province: Optional[str] = None
    city: Optional[str] = None
    district: Optional[str] = None
    street: Optional[str] = None
    address: Optional[str] = None
    website: Optional[str] = None
    contact_name: Optional[str] = None
    contact_phone: Optional[str] = None
    status: Optional[CustomerStatus] = None
    remark: Optional[str] = None


class CustomerOut(CustomerBase):
    id: int
    created_at: datetime
    contacts: List[CustomerContactOut] = []

    model_config = {"from_attributes": True}


class CustomerListOut(CustomerBase):
    id: int
    created_at: datetime

    model_config = {"from_attributes": True}

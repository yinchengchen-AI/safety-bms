from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import relationship

from app.core.constants import CustomerStatus
from app.db.base import Base, SoftDeleteMixin, TimestampMixin


class Customer(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False, index=True, comment="公司名称")
    credit_code = Column(String(50), unique=True, comment="统一社会信用代码")
    industry = Column(String(100), comment="行业")
    scale = Column(String(50), comment="企业规模")
    province = Column(String(50), comment="省")
    city = Column(String(50), comment="市")
    district = Column(String(50), comment="区/县")
    street = Column(String(100), comment="街道/镇")
    address = Column(String(300), comment="地址")
    website = Column(String(200))
    contact_name = Column(String(100), comment="联系人")
    contact_phone = Column(String(20), comment="联系电话")
    status = Column(
        SAEnum(CustomerStatus, name="customer_status"),
        default=CustomerStatus.PROSPECT,
        nullable=False,
    )
    remark = Column(Text)
    created_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    contacts = relationship(
        "CustomerContact", back_populates="customer", cascade="all, delete-orphan"
    )
    follow_ups = relationship(
        "CustomerFollowUp", back_populates="customer", cascade="all, delete-orphan"
    )
    contracts = relationship("Contract", back_populates="customer")


class CustomerContact(Base, TimestampMixin):
    __tablename__ = "customer_contacts"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(100), nullable=False)
    position = Column(String(100), comment="职位")
    phone = Column(String(20))
    email = Column(String(100))
    is_primary = Column(Boolean, default=False, comment="是否主联系人")

    customer = relationship("Customer", back_populates="contacts")


class CustomerFollowUp(Base, TimestampMixin):
    __tablename__ = "customer_follow_ups"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id", ondelete="CASCADE"), nullable=False)
    creator_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    content = Column(Text, nullable=False, comment="跟进内容")
    follow_up_at = Column(DateTime(timezone=True), nullable=False, comment="跟进时间")
    next_follow_up_at = Column(DateTime(timezone=True), comment="下次跟进时间")

    customer = relationship("Customer", back_populates="follow_ups")
    creator = relationship("User", back_populates="follow_ups")

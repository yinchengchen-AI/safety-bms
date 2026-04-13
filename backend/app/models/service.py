from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Numeric, Enum as SAEnum, Date
from sqlalchemy.orm import relationship

from app.db.base import Base, TimestampMixin
from app.core.constants import ServiceOrderStatus, ServiceType


class ServiceOrder(Base, TimestampMixin):
    __tablename__ = "service_orders"

    id = Column(Integer, primary_key=True, index=True)
    order_no = Column(String(50), unique=True, nullable=False, index=True, comment="工单编号")
    contract_id = Column(Integer, ForeignKey("contracts.id", ondelete="RESTRICT"), nullable=False)
    assignee_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, comment="负责人")
    title = Column(String(300), nullable=False)
    service_type = Column(SAEnum(ServiceType, name="service_type_order", create_constraint=False), nullable=False)
    status = Column(
        SAEnum(ServiceOrderStatus, name="service_order_status"),
        default=ServiceOrderStatus.PENDING,
        nullable=False,
    )
    planned_start = Column(Date, comment="计划开始日期")
    planned_end = Column(Date, comment="计划结束日期")
    actual_start = Column(Date, comment="实际开始日期")
    actual_end = Column(Date, comment="实际结束日期")
    remark = Column(Text)

    contract = relationship("Contract", back_populates="service_orders")
    assignee = relationship("User", back_populates="service_orders", foreign_keys=[assignee_id])
    items = relationship("ServiceItem", back_populates="order", cascade="all, delete-orphan")
    reports = relationship("ServiceReport", back_populates="order", cascade="all, delete-orphan")


class ServiceItem(Base, TimestampMixin):
    __tablename__ = "service_items"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("service_orders.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(200), nullable=False, comment="服务项目名称")
    description = Column(Text)
    quantity = Column(Numeric(10, 2), default=1)
    unit = Column(String(20), default="次")
    remark = Column(Text)

    order = relationship("ServiceOrder", back_populates="items")


class ServiceReport(Base, TimestampMixin):
    __tablename__ = "service_reports"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("service_orders.id", ondelete="CASCADE"), nullable=False)
    uploaded_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    file_name = Column(String(300), nullable=False)
    file_url = Column(String(500), nullable=False, comment="MinIO 路径")
    file_size = Column(Integer, comment="文件大小(字节)")
    remark = Column(Text)

    order = relationship("ServiceOrder", back_populates="reports")

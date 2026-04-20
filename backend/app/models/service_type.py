from sqlalchemy import Boolean, Column, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import relationship

from app.db.base import Base, TimestampMixin


class ServiceType(Base, TimestampMixin):
    __tablename__ = "service_types"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True, nullable=False, comment="机器标识")
    name = Column(String(100), nullable=False, comment="展示名称")
    default_price = Column(Numeric(18, 2), nullable=True, comment="默认单价")
    standard_duration_days = Column(Integer, nullable=True, comment="标准工期(天)")
    qualification_requirements = Column(Text, nullable=True, comment="资质要求")
    default_contract_template_id = Column(
        Integer,
        ForeignKey("contract_templates.id", ondelete="SET NULL"),
        nullable=True,
        comment="默认合同模板",
    )
    is_active = Column(Boolean, default=True, nullable=False, comment="是否启用")

    default_contract_template = relationship(
        "ContractTemplate", foreign_keys=[default_contract_template_id]
    )

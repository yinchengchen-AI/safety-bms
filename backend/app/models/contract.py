from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Numeric, Enum as SAEnum, Date, Boolean
from sqlalchemy.orm import relationship

from app.db.base import Base, TimestampMixin, SoftDeleteMixin
from app.core.constants import ContractStatus, PaymentPlan


class Contract(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "contracts"

    id = Column(Integer, primary_key=True, index=True)
    contract_no = Column(String(50), unique=True, nullable=False, index=True, comment="合同编号")
    title = Column(String(300), nullable=False, comment="合同名称")
    customer_id = Column(Integer, ForeignKey("customers.id", ondelete="RESTRICT"), nullable=False)
    service_type = Column(
        Integer,
        ForeignKey("service_types.id", ondelete="RESTRICT"),
        nullable=False,
        comment="服务类型",
    )
    total_amount = Column(Numeric(15, 2), nullable=False, comment="合同总金额")
    payment_plan = Column(
        SAEnum(PaymentPlan, name="payment_plan"),
        default=PaymentPlan.ONCE,
        nullable=False,
    )
    status = Column(
        SAEnum(ContractStatus, name="contract_status"),
        default=ContractStatus.DRAFT,
        nullable=False,
    )
    start_date = Column(Date, comment="合同开始日期")
    end_date = Column(Date, comment="合同结束日期")
    sign_date = Column(Date, comment="签订日期")
    content = Column(Text, comment="合同正文摘要")
    remark = Column(Text)
    file_url = Column(String(500), comment="合同附件 MinIO 路径")
    template_id = Column(Integer, ForeignKey("contract_templates.id", ondelete="SET NULL"), nullable=True, comment="关联模板ID")
    draft_doc_url = Column(String(500), comment="待签文档 MinIO 路径")
    final_pdf_url = Column(String(500), comment="最终PDF MinIO 路径")
    standard_doc_url = Column(String(500), comment="标准合同草稿 MinIO 路径")
    signed_at = Column(DateTime(timezone=True), comment="签订时间")
    created_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    customer = relationship("Customer", back_populates="contracts")
    service_type_obj = relationship("ServiceType")
    template = relationship("ContractTemplate", back_populates="contracts")
    changes = relationship("ContractChange", back_populates="contract", cascade="all, delete-orphan")
    signatures = relationship("ContractSignature", back_populates="contract", cascade="all, delete-orphan")
    service_orders = relationship("ServiceOrder", back_populates="contract")
    invoices = relationship("Invoice", back_populates="contract")
    payments = relationship("Payment", back_populates="contract")


class ContractTemplate(Base, TimestampMixin):
    __tablename__ = "contract_templates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False, comment="模板名称")
    service_type = Column(
        Integer,
        ForeignKey("service_types.id", ondelete="RESTRICT"),
        nullable=False,
        comment="适用服务类型",
    )
    file_url = Column(String(500), nullable=False, comment="模板文件 MinIO 路径")
    is_default = Column(Boolean, default=False, comment="是否默认模板")
    created_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    service_type_obj = relationship("ServiceType", foreign_keys=[service_type])
    contracts = relationship("Contract", back_populates="template")


class ContractSignature(Base, TimestampMixin):
    __tablename__ = "contract_signatures"

    id = Column(Integer, primary_key=True, index=True)
    contract_id = Column(Integer, ForeignKey("contracts.id", ondelete="CASCADE"), nullable=False)
    party = Column(String(20), nullable=False, comment="签署方: party_a / party_b")
    signed_by = Column(String(100), comment="签署人姓名")
    signature_url = Column(String(500), nullable=False, comment="签名图片 MinIO 路径")
    signed_at = Column(DateTime(timezone=True), nullable=False, comment="签署时间")

    contract = relationship("Contract", back_populates="signatures")


class ContractChange(Base, TimestampMixin):
    __tablename__ = "contract_changes"

    id = Column(Integer, primary_key=True, index=True)
    contract_id = Column(Integer, ForeignKey("contracts.id", ondelete="CASCADE"), nullable=False)
    changed_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    change_summary = Column(String(500), nullable=False, comment="变更摘要")
    before_status = Column(String(50))
    after_status = Column(String(50))
    remark = Column(Text)

    contract = relationship("Contract", back_populates="changes")

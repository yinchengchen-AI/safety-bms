from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Numeric, Enum as SAEnum, Date
from sqlalchemy.orm import relationship

from app.db.base import Base, TimestampMixin
from app.core.constants import InvoiceType, InvoiceStatus


class Invoice(Base, TimestampMixin):
    __tablename__ = "invoices"

    id = Column(Integer, primary_key=True, index=True)
    invoice_no = Column(String(50), unique=True, nullable=False, index=True, comment="发票编号（内部流水号）")
    contract_id = Column(Integer, ForeignKey("contracts.id", ondelete="RESTRICT"), nullable=False)
    invoice_type = Column(
        SAEnum(InvoiceType, name="invoice_type"),
        nullable=False,
        comment="发票类型",
    )
    status = Column(
        SAEnum(InvoiceStatus, name="invoice_status"),
        default=InvoiceStatus.APPLYING,
        nullable=False,
    )
    amount = Column(Numeric(15, 2), nullable=False, comment="含税金额")
    tax_rate = Column(Numeric(5, 4), default=0.06, comment="税率")
    tax_amount = Column(Numeric(15, 2), comment="税额")
    invoice_title = Column(String(200), comment="发票抬头（公司名）")
    tax_number = Column(String(50), comment="纳税人识别号")
    invoice_date = Column(Date, comment="开票日期")
    actual_invoice_no = Column(String(100), comment="实际发票号码")
    file_url = Column(String(500), comment="发票扫描件 MinIO 路径")
    remark = Column(Text)
    applied_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    contract = relationship("Contract", back_populates="invoices")
    payments = relationship("Payment", back_populates="invoice")

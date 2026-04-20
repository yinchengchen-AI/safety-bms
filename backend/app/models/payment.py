from sqlalchemy import Boolean, Column, Date, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import relationship

from app.core.constants import PaymentMethod
from app.db.base import Base, TimestampMixin


class Payment(Base, TimestampMixin):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    payment_no = Column(String(50), unique=True, nullable=False, index=True, comment="收款流水号")
    contract_id = Column(Integer, ForeignKey("contracts.id", ondelete="RESTRICT"), nullable=False)
    invoice_id = Column(
        Integer,
        ForeignKey("invoices.id", ondelete="SET NULL"),
        nullable=True,
        comment="关联发票（可选）",
    )
    amount = Column(Numeric(15, 2), nullable=False, comment="收款金额")
    payment_method = Column(
        SAEnum(PaymentMethod, name="payment_method"),
        nullable=False,
    )
    payment_date = Column(Date, nullable=False, comment="收款日期")
    bank_account = Column(String(100), comment="收款银行账号")
    transaction_ref = Column(String(100), comment="交易流水号/支票号")
    file_url = Column(String(500), comment="收款凭证 MinIO 路径")
    remark = Column(Text)
    is_overdue = Column(Boolean, default=False, comment="是否已逾期")
    created_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    contract = relationship("Contract", back_populates="payments")
    invoice = relationship("Invoice", back_populates="payments")

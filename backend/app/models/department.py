from sqlalchemy import Column, Integer, String, Text, ForeignKey
from sqlalchemy.orm import relationship

from app.db.base import Base, TimestampMixin


class Department(Base, TimestampMixin):
    __tablename__ = "departments"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, comment="部门名称")
    description = Column(String(500), nullable=True, comment="部门描述")
    parent_id = Column(Integer, ForeignKey("departments.id", ondelete="SET NULL"), nullable=True, comment="上级部门ID")

    parent = relationship("Department", remote_side="Department.id", back_populates="children")
    children = relationship("Department", back_populates="parent")
    users = relationship("User", back_populates="department")

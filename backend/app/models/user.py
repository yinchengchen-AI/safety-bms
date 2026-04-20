import enum

from sqlalchemy import Boolean, Column, DateTime, Enum, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.db.base import Base, TimestampMixin


class DataScope(enum.Enum):
    ALL = "ALL"
    DEPT = "DEPT"
    SELF = "SELF"


class UserRole(Base):
    __tablename__ = "user_roles"
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    role_id = Column(Integer, ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True)


class RolePermission(Base):
    __tablename__ = "role_permissions"
    role_id = Column(Integer, ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True)
    permission_id = Column(
        Integer, ForeignKey("permissions.id", ondelete="CASCADE"), primary_key=True
    )


class Permission(Base, TimestampMixin):
    __tablename__ = "permissions"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(100), unique=True, nullable=False, index=True, comment="权限码")
    name = Column(String(100), nullable=False, comment="权限名称")
    description = Column(String(255), comment="描述")

    roles = relationship("Role", secondary="role_permissions", back_populates="permissions")


class Role(Base, TimestampMixin):
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False, index=True)
    description = Column(String(200))
    data_scope = Column(
        Enum(DataScope), default=DataScope.SELF, nullable=False, comment="数据权限范围"
    )

    users = relationship("User", secondary="user_roles", back_populates="roles")
    permissions = relationship("Permission", secondary="role_permissions", back_populates="roles")


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    full_name = Column(String(100))
    hashed_password = Column(String(200), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_superuser = Column(Boolean, default=False, nullable=False)
    phone = Column(String(20))
    avatar_url = Column(String(500))
    last_login_at = Column(DateTime(timezone=True))
    department_id = Column(
        Integer,
        ForeignKey("departments.id", ondelete="SET NULL"),
        nullable=True,
        comment="所属部门ID",
    )

    roles = relationship("Role", secondary="user_roles", back_populates="users")
    department = relationship("Department", back_populates="users")
    # 服务工单分配
    service_orders = relationship(
        "ServiceOrder", back_populates="assignee", foreign_keys="ServiceOrder.assignee_id"
    )
    # 跟进记录
    follow_ups = relationship("CustomerFollowUp", back_populates="creator")

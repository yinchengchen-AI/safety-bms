"""
导入所有模型，使 Alembic 能发现所有表进行 migration
"""
from app.db.base import Base  # noqa: F401
from app.models.department import Department  # noqa: F401
from app.models.user import User, Role, UserRole, Permission, RolePermission  # noqa: F401
from app.models.customer import Customer, CustomerContact, CustomerFollowUp  # noqa: F401
from app.models.contract import Contract, ContractChange, ContractTemplate, ContractSignature  # noqa: F401
from app.models.service import ServiceOrder, ServiceItem, ServiceReport  # noqa: F401
from app.models.invoice import Invoice  # noqa: F401
from app.models.payment import Payment  # noqa: F401
from app.models.notification import Notification  # noqa: F401

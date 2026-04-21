"""
导入所有模型，使 Alembic 能发现所有表进行 migration
"""

from app.db.base import Base  # noqa: F401
from app.models.contract import (  # noqa: F401
    Contract,
    ContractChange,
    ContractTemplate,
)
from app.models.customer import Customer, CustomerContact, CustomerFollowUp  # noqa: F401
from app.models.department import Department  # noqa: F401
from app.models.invoice import Invoice  # noqa: F401
from app.models.notification import Notification  # noqa: F401
from app.models.payment import Payment  # noqa: F401
from app.models.service import ServiceItem, ServiceOrder, ServiceReport  # noqa: F401
from app.models.user import Permission, Role, RolePermission, User, UserRole  # noqa: F401

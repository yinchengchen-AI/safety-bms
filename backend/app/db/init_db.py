from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.db.base_all import Base  # noqa: F401
from app.core.security import get_password_hash
from app.core.constants import UserRole as UserRoleEnum, DataScope, PermissionCode
from app.models.user import User, Role, Permission


DEFAULT_ROLES = [
    {"name": UserRoleEnum.ADMIN, "description": "系统管理员，拥有所有权限", "data_scope": DataScope.ALL},
    {"name": UserRoleEnum.SALES, "description": "销售，管理客户和合同", "data_scope": DataScope.DEPT},
    {"name": UserRoleEnum.SERVICE, "description": "服务人员，处理服务工单", "data_scope": DataScope.DEPT},
    {"name": UserRoleEnum.FINANCE, "description": "财务，管理开票和收款", "data_scope": DataScope.DEPT},
    {"name": UserRoleEnum.VIEWER, "description": "只读查看", "data_scope": DataScope.SELF},
]

ROLE_DEFAULT_PERMISSIONS = {
    UserRoleEnum.ADMIN: [p.value for p in PermissionCode],
    UserRoleEnum.SALES: [
        PermissionCode.CUSTOMER_READ,
        PermissionCode.CUSTOMER_CREATE,
        PermissionCode.CUSTOMER_UPDATE,
        PermissionCode.CUSTOMER_DELETE,
        PermissionCode.CUSTOMER_EXPORT,
        PermissionCode.CONTRACT_READ,
        PermissionCode.CONTRACT_CREATE,
        PermissionCode.CONTRACT_UPDATE,
        PermissionCode.CONTRACT_DELETE,
        PermissionCode.CONTRACT_EXPORT,
        PermissionCode.CONTRACT_SIGN,
        PermissionCode.SERVICE_READ,
        PermissionCode.SERVICE_CREATE,
        PermissionCode.SERVICE_UPDATE,
        PermissionCode.SERVICE_DELETE,
        PermissionCode.SERVICE_EXPORT,
        PermissionCode.DASHBOARD_READ,
    ],
    UserRoleEnum.SERVICE: [
        PermissionCode.SERVICE_READ,
        PermissionCode.SERVICE_CREATE,
        PermissionCode.SERVICE_UPDATE,
        PermissionCode.SERVICE_DELETE,
        PermissionCode.SERVICE_EXPORT,
        PermissionCode.CONTRACT_READ,
        PermissionCode.CUSTOMER_READ,
        PermissionCode.DASHBOARD_READ,
    ],
    UserRoleEnum.FINANCE: [
        PermissionCode.INVOICE_READ,
        PermissionCode.INVOICE_CREATE,
        PermissionCode.INVOICE_UPDATE,
        PermissionCode.INVOICE_DELETE,
        PermissionCode.INVOICE_EXPORT,
        PermissionCode.PAYMENT_READ,
        PermissionCode.PAYMENT_CREATE,
        PermissionCode.PAYMENT_UPDATE,
        PermissionCode.PAYMENT_DELETE,
        PermissionCode.PAYMENT_EXPORT,
        PermissionCode.CONTRACT_READ,
        PermissionCode.DASHBOARD_READ,
    ],
    UserRoleEnum.VIEWER: [
        PermissionCode.CUSTOMER_READ,
        PermissionCode.CONTRACT_READ,
        PermissionCode.SERVICE_READ,
        PermissionCode.INVOICE_READ,
        PermissionCode.PAYMENT_READ,
        PermissionCode.DASHBOARD_READ,
    ],
}


def init_db(db: Session) -> None:
    # 初始化角色
    for role_data in DEFAULT_ROLES:
        role = db.query(Role).filter(Role.name == role_data["name"]).first()
        if not role:
            role = Role(**role_data)
            db.add(role)
        else:
            # 更新已有角色的 data_scope
            role.data_scope = role_data["data_scope"]
    db.commit()

    # 绑定默认权限
    for role_name, perm_codes in ROLE_DEFAULT_PERMISSIONS.items():
        role = db.query(Role).filter(Role.name == role_name).first()
        if role:
            perms = db.query(Permission).filter(Permission.code.in_(perm_codes)).all()
            existing_codes = {p.code for p in role.permissions}
            for perm in perms:
                if perm.code not in existing_codes:
                    role.permissions.append(perm)
    db.commit()

    # 初始化超管账号
    admin_user = db.query(User).filter(User.username == "admin").first()
    if not admin_user:
        admin_role = db.query(Role).filter(Role.name == UserRoleEnum.ADMIN).first()
        admin_user = User(
            username="admin",
            email="admin@safety-bms.com",
            full_name="系统管理员",
            hashed_password=get_password_hash("Admin@123456"),
            is_active=True,
            is_superuser=True,
        )
        if admin_role:
            admin_user.roles.append(admin_role)
        db.add(admin_user)
        db.commit()
        print("✅ 初始管理员账号已创建: admin / Admin@123456")


def main():
    db = SessionLocal()
    try:
        init_db(db)
    finally:
        db.close()


if __name__ == "__main__":
    main()

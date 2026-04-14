"""
同步系统权限到数据库，并将全部权限赋予 admin 角色。
用法：
    PYTHONPATH=. python app/cli/sync_permissions.py
"""
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.db.base_all import Base  # noqa: F401
from app.core.constants import PermissionCode
from app.models.user import Permission, Role


PERMISSIONS = [
    {"code": PermissionCode.CUSTOMER_READ, "name": "客户查看"},
    {"code": PermissionCode.CUSTOMER_CREATE, "name": "客户创建"},
    {"code": PermissionCode.CUSTOMER_UPDATE, "name": "客户编辑"},
    {"code": PermissionCode.CUSTOMER_DELETE, "name": "客户删除"},
    {"code": PermissionCode.CUSTOMER_EXPORT, "name": "客户导出"},
    {"code": PermissionCode.CONTRACT_READ, "name": "合同查看"},
    {"code": PermissionCode.CONTRACT_CREATE, "name": "合同创建"},
    {"code": PermissionCode.CONTRACT_UPDATE, "name": "合同编辑"},
    {"code": PermissionCode.CONTRACT_DELETE, "name": "合同删除"},
    {"code": PermissionCode.CONTRACT_EXPORT, "name": "合同导出"},
    {"code": PermissionCode.CONTRACT_SIGN, "name": "合同签订"},
    {"code": PermissionCode.SERVICE_READ, "name": "服务查看"},
    {"code": PermissionCode.SERVICE_CREATE, "name": "服务创建"},
    {"code": PermissionCode.SERVICE_UPDATE, "name": "服务编辑"},
    {"code": PermissionCode.SERVICE_DELETE, "name": "服务删除"},
    {"code": PermissionCode.SERVICE_EXPORT, "name": "服务导出"},
    {"code": PermissionCode.INVOICE_READ, "name": "开票查看"},
    {"code": PermissionCode.INVOICE_CREATE, "name": "开票创建"},
    {"code": PermissionCode.INVOICE_UPDATE, "name": "开票编辑"},
    {"code": PermissionCode.INVOICE_DELETE, "name": "开票删除"},
    {"code": PermissionCode.INVOICE_EXPORT, "name": "开票导出"},
    {"code": PermissionCode.PAYMENT_READ, "name": "收款查看"},
    {"code": PermissionCode.PAYMENT_CREATE, "name": "收款创建"},
    {"code": PermissionCode.PAYMENT_UPDATE, "name": "收款编辑"},
    {"code": PermissionCode.PAYMENT_DELETE, "name": "收款删除"},
    {"code": PermissionCode.PAYMENT_EXPORT, "name": "收款导出"},
    {"code": PermissionCode.USER_READ, "name": "用户查看"},
    {"code": PermissionCode.USER_CREATE, "name": "用户创建"},
    {"code": PermissionCode.USER_UPDATE, "name": "用户编辑"},
    {"code": PermissionCode.USER_DELETE, "name": "用户删除"},
    {"code": PermissionCode.USER_EXPORT, "name": "用户导出"},
    {"code": PermissionCode.ROLE_READ, "name": "角色查看"},
    {"code": PermissionCode.ROLE_CREATE, "name": "角色创建"},
    {"code": PermissionCode.ROLE_UPDATE, "name": "角色编辑"},
    {"code": PermissionCode.ROLE_DELETE, "name": "角色删除"},
    {"code": PermissionCode.ROLE_EXPORT, "name": "角色导出"},
    {"code": PermissionCode.DEPARTMENT_READ, "name": "部门查看"},
    {"code": PermissionCode.DEPARTMENT_CREATE, "name": "部门创建"},
    {"code": PermissionCode.DEPARTMENT_UPDATE, "name": "部门编辑"},
    {"code": PermissionCode.DEPARTMENT_DELETE, "name": "部门删除"},
    {"code": PermissionCode.DEPARTMENT_EXPORT, "name": "部门导出"},
    {"code": PermissionCode.DASHBOARD_READ, "name": "仪表盘查看"},
    {"code": PermissionCode.ANALYTICS_READ, "name": "分析查看"},
]


def sync_permissions(db: Session) -> None:
    created = []
    for p in PERMISSIONS:
        perm = db.query(Permission).filter(Permission.code == p["code"]).first()
        if not perm:
            perm = Permission(**p)
            db.add(perm)
            created.append(p["code"])
    db.commit()

    # 为 admin 角色绑定全部权限
    admin_role = db.query(Role).filter(Role.name == "admin").first()
    if admin_role:
        all_perms = db.query(Permission).all()
        admin_perm_codes = {p.code for p in admin_role.permissions}
        for perm in all_perms:
            if perm.code not in admin_perm_codes:
                admin_role.permissions.append(perm)
        db.commit()
        print(f"✅ admin 角色权限已同步，共 {len(all_perms)} 条权限")
    else:
        print("⚠️ 未找到 admin 角色，跳过权限分配")

    if created:
        print(f"✅ 新增权限 {len(created)} 条")
    else:
        print("✅ 权限无变化")


def main():
    db = SessionLocal()
    try:
        sync_permissions(db)
    finally:
        db.close()


if __name__ == "__main__":
    main()

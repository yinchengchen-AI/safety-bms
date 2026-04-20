"""
同步系统权限到数据库，并将全部权限赋予 admin 角色。
用法：
    PYTHONPATH=. python app/cli/sync_permissions.py
"""

from sqlalchemy.orm import Session

from app.core.constants import PermissionCode
from app.db.base_all import Base  # noqa: F401
from app.db.session import SessionLocal
from app.models.user import Permission, Role

PERMISSIONS = [
    {
        "code": PermissionCode.CUSTOMER_READ,
        "name": "客户查看",
        "description": "查看客户列表及客户详情",
    },
    {"code": PermissionCode.CUSTOMER_CREATE, "name": "客户创建", "description": "创建新客户信息"},
    {"code": PermissionCode.CUSTOMER_UPDATE, "name": "客户编辑", "description": "编辑客户基础资料"},
    {"code": PermissionCode.CUSTOMER_DELETE, "name": "客户删除", "description": "删除客户记录"},
    {"code": PermissionCode.CUSTOMER_EXPORT, "name": "客户导出", "description": "导出客户数据"},
    {
        "code": PermissionCode.CONTRACT_READ,
        "name": "合同查看",
        "description": "查看合同列表及合同详情",
    },
    {"code": PermissionCode.CONTRACT_CREATE, "name": "合同创建", "description": "创建新合同"},
    {"code": PermissionCode.CONTRACT_UPDATE, "name": "合同编辑", "description": "编辑合同内容"},
    {"code": PermissionCode.CONTRACT_DELETE, "name": "合同删除", "description": "删除合同记录"},
    {"code": PermissionCode.CONTRACT_EXPORT, "name": "合同导出", "description": "导出合同数据"},
    {"code": PermissionCode.CONTRACT_SIGN, "name": "合同签订", "description": "执行合同签订流程"},
    {"code": PermissionCode.SERVICE_READ, "name": "服务查看", "description": "查看服务工单及报告"},
    {"code": PermissionCode.SERVICE_CREATE, "name": "服务创建", "description": "创建服务工单"},
    {"code": PermissionCode.SERVICE_UPDATE, "name": "服务编辑", "description": "编辑服务工单信息"},
    {"code": PermissionCode.SERVICE_DELETE, "name": "服务删除", "description": "删除服务工单"},
    {"code": PermissionCode.SERVICE_EXPORT, "name": "服务导出", "description": "导出服务数据"},
    {"code": PermissionCode.INVOICE_READ, "name": "开票查看", "description": "查看发票记录"},
    {"code": PermissionCode.INVOICE_CREATE, "name": "开票创建", "description": "申请开具发票"},
    {"code": PermissionCode.INVOICE_UPDATE, "name": "开票编辑", "description": "编辑发票信息"},
    {"code": PermissionCode.INVOICE_DELETE, "name": "开票删除", "description": "删除发票记录"},
    {"code": PermissionCode.INVOICE_EXPORT, "name": "开票导出", "description": "导出发票数据"},
    {"code": PermissionCode.PAYMENT_READ, "name": "收款查看", "description": "查看收款记录"},
    {"code": PermissionCode.PAYMENT_CREATE, "name": "收款创建", "description": "登记收款信息"},
    {"code": PermissionCode.PAYMENT_UPDATE, "name": "收款编辑", "description": "编辑收款记录"},
    {"code": PermissionCode.PAYMENT_DELETE, "name": "收款删除", "description": "删除收款记录"},
    {"code": PermissionCode.PAYMENT_EXPORT, "name": "收款导出", "description": "导出收款数据"},
    {"code": PermissionCode.USER_READ, "name": "用户查看", "description": "查看系统用户列表"},
    {"code": PermissionCode.USER_CREATE, "name": "用户创建", "description": "创建新用户账号"},
    {"code": PermissionCode.USER_UPDATE, "name": "用户编辑", "description": "编辑用户信息"},
    {"code": PermissionCode.USER_DELETE, "name": "用户删除", "description": "删除用户账号"},
    {"code": PermissionCode.USER_EXPORT, "name": "用户导出", "description": "导出用户数据"},
    {"code": PermissionCode.ROLE_READ, "name": "角色查看", "description": "查看角色及权限配置"},
    {"code": PermissionCode.ROLE_CREATE, "name": "角色创建", "description": "创建新角色"},
    {"code": PermissionCode.ROLE_UPDATE, "name": "角色编辑", "description": "编辑角色权限"},
    {"code": PermissionCode.ROLE_DELETE, "name": "角色删除", "description": "删除角色"},
    {"code": PermissionCode.ROLE_EXPORT, "name": "角色导出", "description": "导出角色数据"},
    {"code": PermissionCode.DEPARTMENT_READ, "name": "部门查看", "description": "查看部门架构"},
    {"code": PermissionCode.DEPARTMENT_CREATE, "name": "部门创建", "description": "创建新部门"},
    {"code": PermissionCode.DEPARTMENT_UPDATE, "name": "部门编辑", "description": "编辑部门信息"},
    {"code": PermissionCode.DEPARTMENT_DELETE, "name": "部门删除", "description": "删除部门"},
    {"code": PermissionCode.DEPARTMENT_EXPORT, "name": "部门导出", "description": "导出部门数据"},
    {
        "code": PermissionCode.DASHBOARD_READ,
        "name": "仪表盘查看",
        "description": "查看首页仪表盘数据",
    },
    {"code": PermissionCode.ANALYTICS_READ, "name": "分析查看", "description": "查看统计分析图表"},
    {"code": PermissionCode.REPORT_READ, "name": "报表查看", "description": "查看及导出预置报表"},
]


def sync_permissions(db: Session) -> None:
    created = []
    updated = []
    for p in PERMISSIONS:
        perm = db.query(Permission).filter(Permission.code == p["code"]).first()
        if not perm:
            perm = Permission(**p)
            db.add(perm)
            created.append(p["code"])
        else:
            changed = False
            if perm.name != p["name"]:
                perm.name = p["name"]
                changed = True
            if perm.description != p.get("description"):
                perm.description = p.get("description")
                changed = True
            if changed:
                updated.append(p["code"])
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
    if updated:
        print(f"✅ 更新权限 {len(updated)} 条")
    if not created and not updated:
        print("✅ 权限无变化")


def main():
    db = SessionLocal()
    try:
        sync_permissions(db)
    finally:
        db.close()


if __name__ == "__main__":
    main()

# 导出字段中文映射

CUSTOMER_STATUS_MAP = {
    "prospect": "意向",
    "signed": "成交",
    "churned": "流失",
}

CONTRACT_STATUS_MAP = {
    "draft": "草稿",
    "review": "审核中",
    "active": "已通过",
    "signed": "已签订",
    "completed": "完成",
    "terminated": "终止",
}

SERVICE_ORDER_STATUS_MAP = {
    "pending": "待开始",
    "in_progress": "进行中",
    "completed": "已完成",
    "accepted": "已验收",
}

INVOICE_TYPE_MAP = {
    "special": "增值税专用发票",
    "general": "增值税普通发票",
}

INVOICE_STATUS_MAP = {
    "applying": "申请中",
    "issued": "已开票",
    "sent": "已寄出",
    "rejected": "已拒绝",
}

PAYMENT_METHOD_MAP = {
    "bank_transfer": "银行转账",
    "cash": "现金",
    "check": "支票",
}

PAYMENT_PLAN_MAP = {
    "once": "一次性",
    "installment": "分期",
}

USER_ROLE_MAP = {
    "admin": "系统管理员",
    "sales": "销售",
    "service": "服务人员",
    "finance": "财务",
    "viewer": "只读查看",
}

DATA_SCOPE_MAP = {
    "ALL": "全部数据",
    "DEPT": "本部门数据",
    "SELF": "仅本人数据",
}

ANALYTICS_CATEGORY_MAP = {
    "contract": "合同",
    "invoice": "发票",
    "payment": "收款",
    "customer": "客户",
    "service": "服务",
}


def map_value(value, mapping: dict) -> str:
    if value is None:
        return ""
    return mapping.get(str(value), str(value))

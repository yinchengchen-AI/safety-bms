from enum import StrEnum


class PermissionCode(StrEnum):
    # customer
    CUSTOMER_READ = "customer:read"
    CUSTOMER_CREATE = "customer:create"
    CUSTOMER_UPDATE = "customer:update"
    CUSTOMER_DELETE = "customer:delete"
    CUSTOMER_EXPORT = "customer:export"
    # contract
    CONTRACT_READ = "contract:read"
    CONTRACT_CREATE = "contract:create"
    CONTRACT_UPDATE = "contract:update"
    CONTRACT_DELETE = "contract:delete"
    CONTRACT_EXPORT = "contract:export"
    # service
    SERVICE_READ = "service:read"
    SERVICE_CREATE = "service:create"
    SERVICE_UPDATE = "service:update"
    SERVICE_DELETE = "service:delete"
    SERVICE_EXPORT = "service:export"
    # invoice
    INVOICE_READ = "invoice:read"
    INVOICE_CREATE = "invoice:create"
    INVOICE_UPDATE = "invoice:update"
    INVOICE_DELETE = "invoice:delete"
    INVOICE_EXPORT = "invoice:export"
    # payment
    PAYMENT_READ = "payment:read"
    PAYMENT_CREATE = "payment:create"
    PAYMENT_UPDATE = "payment:update"
    PAYMENT_DELETE = "payment:delete"
    PAYMENT_EXPORT = "payment:export"
    # user
    USER_READ = "user:read"
    USER_CREATE = "user:create"
    USER_UPDATE = "user:update"
    USER_DELETE = "user:delete"
    USER_EXPORT = "user:export"
    # role
    ROLE_READ = "role:read"
    ROLE_CREATE = "role:create"
    ROLE_UPDATE = "role:update"
    ROLE_DELETE = "role:delete"
    ROLE_EXPORT = "role:export"
    # department
    DEPARTMENT_READ = "department:read"
    DEPARTMENT_CREATE = "department:create"
    DEPARTMENT_UPDATE = "department:update"
    DEPARTMENT_DELETE = "department:delete"
    DEPARTMENT_EXPORT = "department:export"
    # dashboard
    DASHBOARD_READ = "dashboard:read"
    ANALYTICS_READ = "analytics:read"
    REPORT_READ = "report:read"


class DataScope(StrEnum):
    ALL = "ALL"  # 全部数据
    DEPT = "DEPT"  # 本部门数据
    SELF = "SELF"  # 仅本人数据


class UserRole(StrEnum):
    ADMIN = "admin"  # 系统管理员
    SALES = "sales"  # 销售
    SERVICE = "service"  # 服务人员
    FINANCE = "finance"  # 财务
    VIEWER = "viewer"  # 只读查看


class CustomerStatus(StrEnum):
    PROSPECT = "prospect"  # 意向
    SIGNED = "signed"  # 成交
    CHURNED = "churned"  # 流失


class ContractStatus(StrEnum):
    DRAFT = "draft"  # 草稿
    SIGNED = "signed"  # 已签订
    EXECUTING = "executing"  # 履行中
    COMPLETED = "completed"  # 已完成
    TERMINATED = "terminated"  # 终止
    # 兼容旧代码路径，后续合同 API 重写完成后会移除。
    REVIEW = DRAFT
    ACTIVE = SIGNED


class ServiceType(StrEnum):
    EVALUATION = "evaluation"  # 安全评价
    TRAINING = "training"  # 安全培训
    INSPECTION = "inspection"  # 安全检测检验
    CONSULTING = "consulting"  # 安全咨询顾问
    EMERGENCY_PLAN = "emergency_plan"  # 应急预案编制


class ServiceOrderStatus(StrEnum):
    PENDING = "pending"  # 待开始
    IN_PROGRESS = "in_progress"  # 进行中
    COMPLETED = "completed"  # 已完成
    ACCEPTED = "accepted"  # 已验收


class InvoiceType(StrEnum):
    SPECIAL = "special"  # 增值税专用发票
    GENERAL = "general"  # 增值税普通发票


class InvoiceStatus(StrEnum):
    APPLYING = "applying"  # 申请中
    ISSUED = "issued"  # 已开票
    SENT = "sent"  # 已寄出
    REJECTED = "rejected"  # 已拒绝


class PaymentMethod(StrEnum):
    BANK_TRANSFER = "bank_transfer"  # 银行转账
    CASH = "cash"  # 现金
    CHECK = "check"  # 支票


class PaymentPlan(StrEnum):
    ONCE = "once"  # 一次性
    INSTALLMENT = "installment"  # 分期

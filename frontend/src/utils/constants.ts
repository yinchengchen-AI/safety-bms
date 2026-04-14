// 枚举标签映射
export const CustomerStatusLabels: Record<string, string> = {
  prospect: '意向',
  signed: '成交',
  churned: '流失',
}

export const ContractStatusLabels: Record<string, string> = {
  draft: '草稿',
  review: '审核中',
  active: '已通过',
  signed: '已签订',
  completed: '完成',
  terminated: '终止',
}

export const ServiceTypeLabels: Record<string, string> = {
  evaluation: '安全评价',
  training: '安全培训',
  inspection: '安全检测检验',
  consulting: '安全咨询顾问',
  emergency_plan: '应急预案编制',
}

export const ServiceOrderStatusLabels: Record<string, string> = {
  pending: '待开始',
  in_progress: '进行中',
  completed: '已完成',
  accepted: '已验收',
}

export const InvoiceTypeLabels: Record<string, string> = {
  special: '增值税专用发票',
  general: '增值税普通发票',
}

export const InvoiceStatusLabels: Record<string, string> = {
  applying: '申请中',
  issued: '已开票',
  sent: '已寄出',
  rejected: '已拒绝',
}

export const PaymentMethodLabels: Record<string, string> = {
  bank_transfer: '银行转账',
  cash: '现金',
  check: '支票',
}

export const PaymentPlanLabels: Record<string, string> = {
  once: '一次性',
  installment: '分期',
}

// 格式化金额
export const formatAmount = (amount: number | string | undefined): string => {
  if (amount === undefined || amount === null) return '¥0.00'
  return `¥${Number(amount).toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
}

// 自动生成业务编号
export const generateBizNo = (prefix: string): string => {
  const now = new Date()
  const dateStr = `${now.getFullYear()}${String(now.getMonth() + 1).padStart(2, '0')}${String(now.getDate()).padStart(2, '0')}`
  const random = Math.floor(1000 + Math.random() * 9000)
  return `${prefix}${dateStr}${random}`
}

// 角色名称
export const RoleLabels: Record<string, string> = {
  admin: '系统管理员',
  sales: '销售',
  service: '服务人员',
  finance: '财务',
  viewer: '只读查看',
}

// ========== 通用 ==========
export interface PageResponse<T> {
  total: number
  page: number
  page_size: number
  items: T[]
}

export interface ApiError {
  detail: string
}

// ========== 枚举 ==========
export type CustomerStatus = 'prospect' | 'signed' | 'churned'
export type ContractStatus = 'draft' | 'signed' | 'executing' | 'completed' | 'terminated'
export type ServiceType = 'evaluation' | 'training' | 'inspection' | 'consulting' | 'emergency_plan'
export type ServiceOrderStatus = 'pending' | 'in_progress' | 'completed' | 'accepted'
export type InvoiceType = 'special' | 'general'
export type InvoiceStatus = 'applying' | 'issued' | 'sent' | 'rejected'
export type PaymentMethod = 'bank_transfer' | 'cash' | 'check'
export type PaymentPlan = 'once' | 'installment'

// ========== 用户 ==========
export interface Permission {
  id: number
  code: string
  name: string
  description?: string
  created_at: string
}

export interface Role {
  id: number
  name: string
  display_name?: string
  description?: string
  created_at: string
  permissions?: Permission[]
}

export interface Department {
  id: number
  name: string
  description?: string
  parent_id?: number | null
  created_at?: string
  updated_at?: string
}

export interface User {
  id: number
  username: string
  email: string
  full_name?: string
  phone?: string
  is_active: boolean
  is_superuser: boolean
  avatar_url?: string
  last_login_at?: string
  created_at: string
  roles: Role[]
  department_id?: number
  department?: Department
}

export interface UserCreate {
  username: string
  email: string
  full_name?: string
  phone?: string
  password: string
  role_ids: number[]
  department_id?: number
}

export interface UserUpdate {
  full_name?: string
  phone?: string
  email?: string
  is_active?: boolean
  role_ids?: number[]
  department_id?: number
}

// ========== 客户 ==========
export interface CustomerContact {
  id: number
  customer_id: number
  name: string
  position?: string
  phone?: string
  email?: string
  is_primary: boolean
  created_at: string
}

export interface CustomerFollowUp {
  id: number
  customer_id: number
  creator_id?: number
  content: string
  follow_up_at: string
  next_follow_up_at?: string
  created_at: string
}

export interface Customer {
  id: number
  name: string
  credit_code?: string
  industry?: string
  scale?: string
  province?: string
  city?: string
  district?: string
  street?: string
  address?: string
  website?: string
  contact_name?: string
  contact_phone?: string
  status: CustomerStatus
  remark?: string
  created_at: string
  contacts: CustomerContact[]
}

export type CustomerListItem = Omit<Customer, 'contacts'>

export interface CustomerCreate {
  name: string
  credit_code?: string
  industry?: string
  scale?: string
  province?: string
  city?: string
  district?: string
  street?: string
  address?: string
  website?: string
  contact_name?: string
  contact_phone?: string
  status?: CustomerStatus
  remark?: string
  contacts?: Omit<CustomerContact, 'id' | 'customer_id' | 'created_at'>[]
}

// ========== 合同 ==========
export interface ContractTemplate {
  id: number
  name: string
  service_type: number
  file_url: string
  is_default: boolean
  created_at: string
}

export interface ContractAttachment {
  id: number
  contract_id: number
  file_name: string
  file_url: string
  file_type: 'draft' | 'signed' | 'other'
  remark?: string
  uploaded_by?: number
  uploaded_at: string
}

export interface ContractAttachmentCreate {
  file_name: string
  file_url: string
  file_type: 'draft' | 'signed' | 'other'
  remark?: string
}

export interface Contract {
  id: number
  contract_no: string
  title: string
  customer_id: number
  customer_name?: string
  service_type: number
  total_amount: number
  payment_plan: PaymentPlan
  status: ContractStatus
  start_date?: string
  end_date?: string
  sign_date?: string
  content?: string
  remark?: string
  file_url?: string
  template_id?: number
  standard_doc_url?: string
  draft_doc_url?: string
  final_pdf_url?: string
  signed_at?: string
  created_at: string
  invoiced_amount?: number
  received_amount?: number
  attachments?: ContractAttachment[]
}

export interface ContractCreate {
  contract_no: string
  title: string
  customer_id: number
  service_type: number
  total_amount: number
  payment_plan?: PaymentPlan
  start_date?: string
  end_date?: string
  sign_date?: string
  content?: string
  remark?: string
  template_id?: number
}

// ========== 服务工单 ==========
export interface ServiceItem {
  id: number
  order_id: number
  name: string
  description?: string
  quantity: number
  unit: string
  remark?: string
}

export interface ServiceItemUpdate {
  name?: string
  description?: string
  quantity?: number
  unit?: string
  remark?: string
}

export interface ServiceReport {
  id: number
  order_id: number
  file_name: string
  file_url: string
  file_size?: number
  remark?: string
  created_at: string
}

export interface ServiceOrder {
  id: number
  order_no: string
  contract_id: number
  title: string
  service_type: number
  status: ServiceOrderStatus
  assignee_id?: number
  assignee_name?: string
  customer_name?: string
  planned_start?: string
  planned_end?: string
  actual_start?: string
  actual_end?: string
  remark?: string
  created_at: string
  items: ServiceItem[]
  reports: ServiceReport[]
}

export interface ServiceOrderCreate {
  order_no: string
  contract_id: number
  title: string
  service_type: number
  assignee_id?: number
  planned_start?: string
  planned_end?: string
  remark?: string
  items?: Omit<ServiceItem, 'id' | 'order_id'>[]
}

// ========== 发票 ==========
export interface Invoice {
  id: number
  invoice_no: string
  contract_id: number
  customer_name?: string
  invoice_type: InvoiceType
  status: InvoiceStatus
  amount: number
  tax_rate: number
  tax_amount?: number
  invoice_title?: string
  tax_number?: string
  invoice_date?: string
  actual_invoice_no?: string
  file_url?: string
  applied_by?: number
  remark?: string
  created_at: string
}

export interface InvoiceCreate {
  invoice_no: string
  contract_id: number
  invoice_type: InvoiceType
  amount: number
  tax_rate?: number
  invoice_title?: string
  tax_number?: string
  remark?: string
}

// ========== 收款 ==========
export interface Payment {
  id: number
  payment_no: string
  contract_id: number
  contract_no?: string
  invoice_id?: number
  customer_name?: string
  amount: number
  payment_method: PaymentMethod
  payment_date: string
  bank_account?: string
  transaction_ref?: string
  file_url?: string
  is_overdue: boolean
  created_by?: number
  remark?: string
  created_at: string
}

export interface PaymentCreate {
  payment_no: string
  contract_id: number
  invoice_id?: number
  amount: number
  payment_method: PaymentMethod
  payment_date: string
  bank_account?: string
  transaction_ref?: string
  remark?: string
}

export interface ContractReceivable {
  id?: number
  contract_id: number
  contract_no: string
  customer_name?: string
  end_date?: string
  total_amount: number
  received_amount: number
  receivable_amount: number
  is_overdue: boolean
}

// ========== Auth ==========
export interface LoginRequest {
  username: string
  password: string
}

export interface TokenResponse {
  access_token: string
  refresh_token: string
  token_type: string
}

// ========== 通知 ==========
export interface Notification {
  id: number
  user_id: number
  title: string
  content: string
  is_read: boolean
  notification_type: string
  created_at: string
}

// ========== 仪表盘 ==========
export interface DashboardStats {
  contract_status_distribution: { status: string; count: number }[]
  service_status_distribution: { status: string; count: number }[]
  monthly_invoice_amount: number
  monthly_payment_amount: number
  total_receivable: number
  overdue_contract_count: number
  monthly_invoice_trend: { month: number; total: number }[]
  monthly_payment_trend: { month: number; total: number }[]
  overdue_contracts: ContractReceivable[]
  customer_growth_trend: { month: number; count: number }[]
  contract_amount_by_service_type: { service_type: string; total_amount: number }[]
  top_performers: { user_id: number; full_name: string; total_amount: number }[]
  monthly_new_service_orders: number
}

export interface AnalyticsOverview {
  signed_amount: number
  invoiced_amount: number
  received_amount: number
  collection_rate: number
  receivable_balance: number
  overdue_contract_count: number
}

export interface RevenueTrendItem {
  period: string
  signed_amount: number
  invoiced_amount: number
  received_amount: number
  receivable_balance: number
}

export interface RevenueTrendResponse {
  items: RevenueTrendItem[]
}

export interface PerformanceRankingItem {
  user_id?: number
  full_name: string
  signed_amount: number
  invoiced_amount: number
  received_amount: number
}

export interface PerformanceRankingResponse {
  items: PerformanceRankingItem[]
}

export interface ReceivableAgingBucket {
  range: string
  contract_count: number
  amount: number
}

export interface RiskContract {
  contract_id: number
  contract_no: string
  customer_name?: string
  end_date?: string
  receivable_amount: number
  overdue_days: number
}

export interface ReceivableAgingResponse {
  buckets: ReceivableAgingBucket[]
  risk_contracts: RiskContract[]
}

export interface CustomerGrowthItem {
  period: string
  new_customers: number
}

export interface CustomerIndustryDistributionItem {
  industry: string
  count: number
}

export interface CustomerStatusDistributionItem {
  status: string
  count: number
}

export interface CustomerInsightsResponse {
  growth_trend: CustomerGrowthItem[]
  industry_distribution: CustomerIndustryDistributionItem[]
  status_distribution: CustomerStatusDistributionItem[]
}

export interface ServiceEfficiencyTrendItem {
  period: string
  new_orders: number
  completed_orders: number
  on_time_rate: number
  overdue_orders: number
}

export interface ServiceTypeDistributionItem {
  service_type: string
  order_count: number
}

export interface ServiceEfficiencyResponse {
  trend: ServiceEfficiencyTrendItem[]
  service_type_distribution: ServiceTypeDistributionItem[]
}

export interface AnalyticsDrilldownItem {
  id: number
  category: string
  primary_label: string
  secondary_label?: string
  amount?: number
  date_label?: string
  status?: string
  extra?: string
}

export interface AnalyticsDrilldownResponse {
  total: number
  items: AnalyticsDrilldownItem[]
}

from datetime import date
from typing import Optional

from pydantic import BaseModel


class AnalyticsOverviewOut(BaseModel):
    signed_amount: float
    invoiced_amount: float
    received_amount: float
    collection_rate: float
    receivable_balance: float
    overdue_contract_count: int


class RevenueTrendItemOut(BaseModel):
    period: str
    signed_amount: float
    invoiced_amount: float
    received_amount: float
    receivable_balance: float


class RevenueTrendOut(BaseModel):
    items: list[RevenueTrendItemOut]


class PerformanceRankingItemOut(BaseModel):
    user_id: Optional[int] = None
    full_name: str
    signed_amount: float
    invoiced_amount: float
    received_amount: float


class PerformanceRankingOut(BaseModel):
    items: list[PerformanceRankingItemOut]


class ReceivableAgingBucketOut(BaseModel):
    range: str
    contract_count: int
    amount: float


class RiskContractOut(BaseModel):
    contract_id: int
    contract_no: str
    customer_name: Optional[str] = None
    end_date: Optional[date] = None
    receivable_amount: float
    overdue_days: int


class ReceivableAgingOut(BaseModel):
    buckets: list[ReceivableAgingBucketOut]
    risk_contracts: list[RiskContractOut]


class CustomerGrowthItemOut(BaseModel):
    period: str
    new_customers: int


class CustomerIndustryDistributionItemOut(BaseModel):
    industry: str
    count: int


class CustomerStatusDistributionItemOut(BaseModel):
    status: str
    count: int


class CustomerInsightsOut(BaseModel):
    growth_trend: list[CustomerGrowthItemOut]
    industry_distribution: list[CustomerIndustryDistributionItemOut]
    status_distribution: list[CustomerStatusDistributionItemOut]


class ServiceEfficiencyTrendItemOut(BaseModel):
    period: str
    new_orders: int
    completed_orders: int
    on_time_rate: float
    overdue_orders: int


class ServiceTypeDistributionItemOut(BaseModel):
    service_type: str
    order_count: int


class ServiceEfficiencyOut(BaseModel):
    trend: list[ServiceEfficiencyTrendItemOut]
    service_type_distribution: list[ServiceTypeDistributionItemOut]


class AnalyticsDrilldownItemOut(BaseModel):
    id: int
    category: str
    primary_label: str
    secondary_label: Optional[str] = None
    amount: Optional[float] = None
    date_label: Optional[str] = None
    status: Optional[str] = None
    extra: Optional[str] = None


class AnalyticsDrilldownOut(BaseModel):
    total: int
    items: list[AnalyticsDrilldownItemOut]

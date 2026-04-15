import React, { useMemo, useState } from 'react'
import {
  Alert,
  Button,
  Card,
  Col,
  DatePicker,
  Drawer,
  Empty,
  message,
  Row,
  Space,
  Spin,
  Statistic,
  Table,
  Tabs,
} from 'antd'
import { Line, Column, Pie } from '@ant-design/charts'
import dayjs, { Dayjs } from 'dayjs'

import {
  type AnalyticsDrilldownParams,
  useGetAnalyticsOverviewQuery,
  useGetCustomerInsightsQuery,
  useGetPerformanceRankingQuery,
  useGetReceivableAgingQuery,
  useGetRevenueTrendQuery,
  useGetServiceEfficiencyQuery,
  useLazyGetAnalyticsDrilldownQuery,
} from '@/store/api/analyticsApi'
import { downloadExport } from '@/utils/export'
import { ContractStatusLabels, CustomerStatusLabels, InvoiceStatusLabels, ServiceOrderStatusLabels, ServiceTypeLabels, formatAmount } from '@/utils/constants'
import type { AnalyticsDrilldownItem } from '@/types'

const { RangePicker } = DatePicker

const Analytics: React.FC = () => {
  const [range, setRange] = useState<[Dayjs | null, Dayjs | null] | null>([
    dayjs().startOf('year'),
    dayjs().endOf('month'),
  ])
  const [detailTitle, setDetailTitle] = useState('')
  const [detailRows, setDetailRows] = useState<AnalyticsDrilldownItem[]>([])
  const [detailLoading, setDetailLoading] = useState(false)
  const [detailParams, setDetailParams] = useState<AnalyticsDrilldownParams | null>(null)
  const [triggerDrilldown] = useLazyGetAnalyticsDrilldownQuery()

  const params = useMemo(() => ({
    date_from: range?.[0] ? range[0].format('YYYY-MM-DD') : undefined,
    date_to: range?.[1] ? range[1].format('YYYY-MM-DD') : undefined,
  }), [range])

  const overviewQuery = useGetAnalyticsOverviewQuery(params)
  const revenueQuery = useGetRevenueTrendQuery(params)
  const rankingQuery = useGetPerformanceRankingQuery(params)
  const agingQuery = useGetReceivableAgingQuery(params)
  const customerQuery = useGetCustomerInsightsQuery(params)
  const serviceQuery = useGetServiceEfficiencyQuery(params)

  const isLoading = [overviewQuery, revenueQuery, rankingQuery, agingQuery, customerQuery, serviceQuery].some((query) => query.isLoading)

  const revenueTrendData = (revenueQuery.data?.items || []).flatMap((item) => ([
    { period: item.period, amount: item.signed_amount, type: '签约额' },
    { period: item.period, amount: item.invoiced_amount, type: '开票额' },
    { period: item.period, amount: item.received_amount, type: '收款额' },
  ]))

  const performanceData = rankingQuery.data?.items.map((item) => ({
    name: item.full_name,
    amount: item.signed_amount,
    userId: item.user_id,
  })) || []

  const agingData = agingQuery.data?.buckets.map((item) => ({
    range: item.range,
    amount: item.amount,
  })) || []

  const customerGrowthData = customerQuery.data?.growth_trend.map((item) => ({
    period: item.period,
    value: item.new_customers,
  })) || []

  const customerIndustryData = customerQuery.data?.industry_distribution.map((item) => ({
    type: item.industry,
    value: item.count,
  })) || []

  const customerStatusData = customerQuery.data?.status_distribution.map((item) => ({
    type: CustomerStatusLabels[item.status] || item.status,
    value: item.count,
  })) || []

  const serviceTrendData = (serviceQuery.data?.trend || []).flatMap((item) => ([
    { period: item.period, value: item.new_orders, type: '新增工单' },
    { period: item.period, value: item.completed_orders, type: '完成工单' },
    { period: item.period, value: item.overdue_orders, type: '逾期工单' },
  ]))

  const serviceTypeData = serviceQuery.data?.service_type_distribution.map((item) => ({
    type: ServiceTypeLabels[item.service_type] || item.service_type,
    value: item.order_count,
    rawType: item.service_type,
  })) || []

  const detailColumns = [
    { title: '主项', dataIndex: 'primary_label', key: 'primary_label' },
    { title: '关联信息', dataIndex: 'secondary_label', key: 'secondary_label' },
    { title: '金额', dataIndex: 'amount', key: 'amount', render: (value?: number) => value !== undefined && value !== null ? formatAmount(value) : '-' },
    { title: '日期', dataIndex: 'date_label', key: 'date_label' },
    {
      title: '状态/天数',
      dataIndex: 'status',
      key: 'status',
      render: (value?: string, record?: AnalyticsDrilldownItem) => {
        if (!value) return '-'
        if (record?.category === 'invoice') return InvoiceStatusLabels[value] || value
        if (record?.category === 'customer') return CustomerStatusLabels[value] || value
        if (record?.category === 'service') return ServiceOrderStatusLabels[value] || value
        return ContractStatusLabels[value] || value
      },
    },
    { title: '附加信息', dataIndex: 'extra', key: 'extra' },
  ]

  const openDrilldown = async (requestParams: AnalyticsDrilldownParams, title: string) => {
    setDetailLoading(true)
    try {
      const data = await triggerDrilldown(requestParams, true).unwrap()
      setDetailTitle(title)
      setDetailRows(data.items)
      setDetailParams(requestParams)
    } catch (err: any) {
      message.error(err?.data?.detail || '加载明细失败')
    } finally {
      setDetailLoading(false)
    }
  }

  const exportDetail = async () => {
    if (!detailParams) return
    const searchParams = new URLSearchParams()
    Object.entries(detailParams).forEach(([key, value]) => {
      if (value) searchParams.append(key, value)
    })
    try {
      await downloadExport(`/api/v1/analytics/export?${searchParams.toString()}`, `analytics_${dayjs().format('YYYYMMDD_HHmmss')}.xlsx`)
    } catch (err: any) {
      message.error(err.message || '导出失败')
    }
  }

  const openRevenueDrilldown = async (datum: { type: string; period: string }) => {
    await openDrilldown({ source: 'revenue', series_type: datum.type, period: datum.period, ...params }, `${datum.type}明细 - ${datum.period}`)
  }

  const openPerformanceDrilldown = async (datum: { userId?: number; name: string }) => {
    if (!datum.userId) return
    await openDrilldown({ source: 'performance', group_value: String(datum.userId), ...params }, `签约排行明细 - ${datum.name}`)
  }

  const openAgingDrilldown = async (datum?: { range: string }) => {
    await openDrilldown({ source: datum?.range ? 'aging' : 'aging-risk', group_value: datum?.range, ...params }, datum?.range ? `账龄明细 - ${datum.range}` : '高风险合同明细')
  }

  const openCustomerIndustryDrilldown = async (datum: { type: string }) => {
    await openDrilldown({ source: 'customer-industry', group_value: datum.type, ...params }, `客户行业明细 - ${datum.type}`)
  }

  const openCustomerStatusDrilldown = async (datum: { type: string }) => {
    const rawStatus = Object.entries(CustomerStatusLabels).find(([, label]) => label === datum.type)?.[0] || datum.type
    await openDrilldown({ source: 'customer-status', group_value: rawStatus, ...params }, `客户状态明细 - ${datum.type}`)
  }

  const openServiceTypeDrilldown = async (datum: { type: string; rawType?: string }) => {
    await openDrilldown({ source: 'service-type', group_value: datum.rawType || datum.type, ...params }, `服务类型明细 - ${datum.type}`)
  }

  if (isLoading) {
    return (
      <div style={{ textAlign: 'center', padding: 120 }}>
        <Spin size="large" />
      </div>
    )
  }

  return (
    <div>
      <Space style={{ marginBottom: 16 }}>
        <RangePicker value={range} onChange={(value) => setRange(value as [Dayjs | null, Dayjs | null])} />
      </Space>

      <Row gutter={[16, 16]}>
        <Col span={4}><Card><Statistic title="签约额" value={overviewQuery.data?.signed_amount || 0} formatter={(v) => formatAmount(Number(v))} /></Card></Col>
        <Col span={4}><Card><Statistic title="开票额" value={overviewQuery.data?.invoiced_amount || 0} formatter={(v) => formatAmount(Number(v))} /></Card></Col>
        <Col span={4}><Card><Statistic title="收款额" value={overviewQuery.data?.received_amount || 0} formatter={(v) => formatAmount(Number(v))} /></Card></Col>
        <Col span={4}><Card><Statistic title="回款率" value={overviewQuery.data?.collection_rate || 0} suffix="%" precision={2} /></Card></Col>
        <Col span={4}><Card><Statistic title="应收余额" value={overviewQuery.data?.receivable_balance || 0} formatter={(v) => formatAmount(Number(v))} /></Card></Col>
        <Col span={4}><Card><Statistic title="逾期合同数" value={overviewQuery.data?.overdue_contract_count || 0} suffix="个" /></Card></Col>
      </Row>

      <Tabs
        style={{ marginTop: 16 }}
        items={[
          {
            key: 'business',
            label: '经营分析',
            children: (
              <>
                <Row gutter={[16, 16]}>
                  <Col span={16}>
                    <Card title="签约 / 开票 / 收款趋势">
                      {revenueTrendData.length === 0 ? <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="暂无数据" /> : (
                        <Line
                          data={revenueTrendData}
                          xField="period"
                          yField="amount"
                          seriesField="type"
                          colorField="type"
                          smooth
                          height={300}
                          onReady={(plot) => {
                            plot.on('element:click', (event: any) => {
                              const datum = event?.data?.data
                              if (datum) void openRevenueDrilldown(datum)
                            })
                          }}
                        />
                      )}
                    </Card>
                  </Col>
                  <Col span={8}>
                    <Card title="签约排行">
                      {performanceData.length === 0 ? <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="暂无数据" /> : (
                        <Column
                          data={performanceData}
                          xField="name"
                          yField="amount"
                          height={300}
                          onReady={(plot) => {
                            plot.on('element:click', (event: any) => {
                              const datum = event?.data?.data
                              if (datum) void openPerformanceDrilldown(datum)
                            })
                          }}
                        />
                      )}
                    </Card>
                  </Col>
                </Row>
                <Alert style={{ marginTop: 16 }} type="info" message="签约额统一按合同 sign_date 统计；图表口径与分析模块保持一致。" />
              </>
            ),
          },
          {
            key: 'finance',
            label: '财务分析',
            children: (
              <>
                <Row gutter={[16, 16]}>
                  <Col span={12}>
                    <Card title="应收账龄分布" extra={<a onClick={() => void openAgingDrilldown()}>查看明细</a>}>
                      {agingData.length === 0 ? <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="暂无数据" /> : (
                        <Column
                          data={agingData}
                          xField="range"
                          yField="amount"
                          height={280}
                          onReady={(plot) => {
                            plot.on('element:click', (event: any) => {
                              const datum = event?.data?.data
                              if (datum) void openAgingDrilldown(datum)
                            })
                          }}
                        />
                      )}
                    </Card>
                  </Col>
                  <Col span={12}>
                    <Card title="高风险合同">
                      <Table
                        rowKey="contract_id"
                        pagination={false}
                        dataSource={(agingQuery.data?.risk_contracts || []).slice(0, 5)}
                        columns={[
                          { title: '合同编号', dataIndex: 'contract_no', key: 'contract_no' },
                          { title: '客户', dataIndex: 'customer_name', key: 'customer_name' },
                          { title: '逾期天数', dataIndex: 'overdue_days', key: 'overdue_days' },
                          { title: '应收余额', dataIndex: 'receivable_amount', key: 'receivable_amount', render: (value: number) => formatAmount(value) },
                        ]}
                      />
                    </Card>
                  </Col>
                </Row>
              </>
            ),
          },
          {
            key: 'customer-service',
            label: '客户与服务分析',
            children: (
              <>
                <Row gutter={[16, 16]}>
                  <Col span={12}>
                    <Card title="客户增长趋势">
                      {customerGrowthData.length === 0 ? <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="暂无数据" /> : (
                        <Line data={customerGrowthData} xField="period" yField="value" height={260} />
                      )}
                    </Card>
                  </Col>
                  <Col span={6}>
                    <Card title="客户行业分布">
                      {customerIndustryData.length === 0 ? <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="暂无数据" /> : (
                        <Pie
                          data={customerIndustryData}
                          angleField="value"
                          colorField="type"
                          height={260}
                          onReady={(plot) => {
                            plot.on('element:click', (event: any) => {
                              const datum = event?.data?.data
                              if (datum) void openCustomerIndustryDrilldown(datum)
                            })
                          }}
                        />
                      )}
                    </Card>
                  </Col>
                  <Col span={6}>
                    <Card title="客户状态分布">
                      {customerStatusData.length === 0 ? <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="暂无数据" /> : (
                        <Pie
                          data={customerStatusData}
                          angleField="value"
                          colorField="type"
                          height={260}
                          onReady={(plot) => {
                            plot.on('element:click', (event: any) => {
                              const datum = event?.data?.data
                              if (datum) void openCustomerStatusDrilldown(datum)
                            })
                          }}
                        />
                      )}
                    </Card>
                  </Col>
                </Row>
                <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
                  <Col span={16}>
                    <Card title="服务效率趋势">
                      {serviceTrendData.length === 0 ? <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="暂无数据" /> : (
                        <Line data={serviceTrendData} xField="period" yField="value" seriesField="type" colorField="type" height={280} />
                      )}
                    </Card>
                  </Col>
                  <Col span={8}>
                    <Card title="服务类型工作量分布">
                      {serviceTypeData.length === 0 ? <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="暂无数据" /> : (
                        <Column
                          data={serviceTypeData}
                          xField="type"
                          yField="value"
                          height={280}
                          onReady={(plot) => {
                            plot.on('element:click', (event: any) => {
                              const datum = event?.data?.data
                              if (datum) void openServiceTypeDrilldown(datum)
                            })
                          }}
                        />
                      )}
                    </Card>
                  </Col>
                </Row>
              </>
            ),
          },
        ]}
      />

      <Drawer
        title={detailTitle}
        open={detailRows.length > 0 || detailLoading}
        onClose={() => {
          setDetailRows([])
          setDetailParams(null)
        }}
        width={820}
        extra={<Button onClick={exportDetail} disabled={!detailParams}>导出</Button>}
      >
        <Table
          rowKey="id"
          dataSource={detailRows}
          loading={detailLoading}
          pagination={false}
          columns={detailColumns}
        />
      </Drawer>
    </div>
  )
}

export default Analytics

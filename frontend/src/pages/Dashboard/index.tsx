import React from 'react'
import { Row, Col, Card, Statistic, Spin, Tag, Empty } from 'antd'
import {
  FileTextOutlined,
  DollarOutlined,
  ExclamationCircleOutlined,
  RiseOutlined,
  UserOutlined,
  ToolOutlined,
} from '@ant-design/icons'
import { Line, Pie, Column } from '@ant-design/charts'
import { useGetDashboardStatsQuery } from '@/store/api/dashboardApi'
import {
  formatAmount,
  ContractStatusLabels,
  ServiceOrderStatusLabels,
  ServiceTypeLabels,
} from '@/utils/constants'

interface KPICardProps {
  title: string
  value: number | string
  prefix: React.ReactNode
  gradient: string
  suffix?: string
  formatter?: (v: number | string) => string
}

const KPICard: React.FC<KPICardProps> = ({
  title,
  value,
  prefix,
  gradient,
  suffix,
  formatter,
}) => (
  <Card
    bodyStyle={{ padding: 20 }}
    style={{
      borderRadius: 12,
      background: gradient,
      border: 'none',
      color: '#fff',
    }}
  >
    <Statistic
      title={<span style={{ color: 'rgba(255,255,255,0.85)', fontSize: 14 }}>{title}</span>}
      value={value}
      prefix={<span style={{ color: '#fff', fontSize: 18, marginRight: 8 }}>{prefix}</span>}
      suffix={suffix ? <span style={{ color: 'rgba(255,255,255,0.85)', fontSize: 14 }}>{suffix}</span> : undefined}
      valueStyle={{ color: '#fff', fontSize: 24, fontWeight: 700 }}
      formatter={(v) => (formatter ? formatter(v as number) : String(v))}
    />
  </Card>
)

const Dashboard: React.FC = () => {
  const { data: stats, isLoading } = useGetDashboardStatsQuery()

  if (isLoading) {
    return (
      <div style={{ textAlign: 'center', padding: 120 }}>
        <Spin size="large" />
      </div>
    )
  }
  if (!stats) return null

  // 月度开票/收款趋势
  const invoiceTrend = (stats.monthly_invoice_trend || []).map((d: any) => ({
    '月份': `${d.month}月`,
    '金额': Number(d.total || 0),
    '类型': '开票金额',
  }))
  const paymentTrend = (stats.monthly_payment_trend || []).map((d: any) => ({
    '月份': `${d.month}月`,
    '金额': Number(d.total || 0),
    '类型': '收款金额',
  }))
  const trendData = [...invoiceTrend, ...paymentTrend]

  // 合同状态分布
  const contractPieData = (stats.contract_status_distribution || []).map((d: any) => ({
    '状态': ContractStatusLabels[d.status as keyof typeof ContractStatusLabels] || d.status,
    '数量': Number(d.count),
  }))

  // 服务工单状态分布
  const serviceBarData = (stats.service_status_distribution || []).map((d: any) => ({
    '状态': ServiceOrderStatusLabels[d.status as keyof typeof ServiceOrderStatusLabels] || d.status,
    '数量': Number(d.count),
  }))

  // 客户增长趋势
  const customerGrowthData = ((stats as any).customer_growth_trend || []).map((d: any) => ({
    '月份': `${d.month}月`,
    '新增客户数': Number(d.count),
  }))

  // 合同金额按服务类型分布
  const contractAmountByServiceData = ((stats as any).contract_amount_by_service_type || []).map(
    (d: any) => ({
      '服务类型': ServiceTypeLabels[d.service_type as keyof typeof ServiceTypeLabels] || d.service_type,
      '金额': Number(d.total_amount),
    })
  )

  // 员工业绩排行
  const topPerformers = (stats as any).top_performers || []

  // 逾期合同
  const overdueContracts = (stats.overdue_contracts || []).slice(0, 5)

  const trendConfig = {
    data: trendData,
    xField: '月份',
    yField: '金额',
    seriesField: '类型',
    colorField: '类型',
    smooth: true,
    color: ['#1890ff', '#52c41a'],
    legend: { position: 'top-right' as const },
    yAxis: {
      title: { text: '金额（万）' },
      labelFormatter: (v: number) => `¥${(v / 10000).toFixed(1)}万`,
    },
    xAxis: { title: { text: '月份' } },
    tooltip: {
      items: [
        (d: any) => ({
          name: d['类型'],
          value: formatAmount(d['金额']),
        }),
      ],
    },
  }

  const pieConfig = {
    data: contractPieData,
    angleField: '数量',
    colorField: '状态',
    innerRadius: 0.5,
    legend: {
      color: { position: 'bottom' as const, layout: { justifyContent: 'center' } },
    },
    label: {
      text: (d: any) => `${d['状态']}\n${d['数量']}个`,
      style: { fontSize: 12 },
    },
    tooltip: {
      items: [
        (d: any) => ({
          name: d['状态'],
          value: `${d['数量']}个`,
        }),
      ],
    },
  }

  const serviceBarConfig = {
    data: serviceBarData,
    xField: '状态',
    yField: '数量',
    color: '#1890ff',
    xAxis: { title: { text: '状态' } },
    yAxis: { title: { text: '数量（个）' } },
    label: {
      text: (d: any) => `${d['数量']}个`,
      style: { fill: '#fff' },
    },
    tooltip: {
      items: [
        (d: any) => ({
          name: '工单数量',
          value: `${d['数量']}个`,
        }),
      ],
    },
    style: { radiusTopLeft: 4, radiusTopRight: 4 },
  }

  const amountByServiceConfig = {
    data: contractAmountByServiceData,
    xField: '服务类型',
    yField: '金额',
    color: '#722ed1',
    xAxis: {
      title: { text: '服务类型' },
      labelAutoRotate: true,
    },
    yAxis: {
      title: { text: '金额（万）' },
      labelFormatter: (v: number) => `¥${(v / 10000).toFixed(1)}万`,
    },
    label: {
      text: (d: any) => `¥${(d['金额'] / 10000).toFixed(1)}万`,
      style: { fill: '#fff' },
    },
    tooltip: {
      items: [
        (d: any) => ({
          name: '合同金额',
          value: formatAmount(d['金额']),
        }),
      ],
    },
    style: { radiusTopLeft: 4, radiusTopRight: 4 },
  }

  const customerGrowthConfig = {
    data: customerGrowthData,
    xField: '月份',
    yField: '新增客户数',
    smooth: true,
    color: '#13c2c2',
    areaStyle: { fill: 'rgba(19, 194, 194, 0.15)' },
    xAxis: { title: { text: '月份' } },
    yAxis: { title: { text: '新增客户数（个）' }, labelFormatter: (v: number) => `${v} 个` },
    tooltip: {
      items: [
        (d: any) => ({
          name: '新增客户数',
          value: `${d['新增客户数']} 个`,
        }),
      ],
    },
  }

  return (
    <div style={{ paddingBottom: 24 }}>
      {/* KPI 卡片 */}
      <Row gutter={[16, 16]}>
        <Col span={4}>
          <KPICard
            title="本月开票金额"
            value={stats.monthly_invoice_amount || 0}
            prefix={<FileTextOutlined />}
            gradient="linear-gradient(135deg, #1890ff 0%, #36cfc9 100%)"
            formatter={(v) => formatAmount(Number(v))}
          />
        </Col>
        <Col span={4}>
          <KPICard
            title="本月收款金额"
            value={stats.monthly_payment_amount || 0}
            prefix={<DollarOutlined />}
            gradient="linear-gradient(135deg, #52c41a 0%, #95de64 100%)"
            formatter={(v) => formatAmount(Number(v))}
          />
        </Col>
        <Col span={4}>
          <KPICard
            title="总应收余额"
            value={stats.total_receivable || 0}
            prefix={<RiseOutlined />}
            gradient="linear-gradient(135deg, #fa8c16 0%, #ffc53d 100%)"
            formatter={(v) => formatAmount(Number(v))}
          />
        </Col>
        <Col span={4}>
          <KPICard
            title="本月新增客户"
            value={customerGrowthData.reduce((sum: number, d: any) => sum + d['新增客户数'], 0)}
            prefix={<UserOutlined />}
            gradient="linear-gradient(135deg, #722ed1 0%, #b37feb 100%)"
            suffix="个"
          />
        </Col>
        <Col span={4}>
          <KPICard
            title="本月新增工单"
            value={(stats as any).monthly_new_service_orders || 0}
            prefix={<ToolOutlined />}
            gradient="linear-gradient(135deg, #13c2c2 0%, #5cdbd3 100%)"
            suffix="个"
          />
        </Col>
        <Col span={4}>
          <KPICard
            title="逾期合同数"
            value={stats.overdue_contract_count || 0}
            prefix={<ExclamationCircleOutlined />}
            gradient="linear-gradient(135deg, #f5222d 0%, #ff7875 100%)"
            suffix="个"
          />
        </Col>
      </Row>

      {/* 财务趋势 + 业绩排行 */}
      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        <Col span={16}>
          <Card title="月度开票/收款趋势" bodyStyle={{ padding: 12 }}>
            {trendData.length === 0 ? (
              <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="暂无数据" style={{ padding: '80px 0' }} />
            ) : (
              <Line {...trendConfig} height={300} />
            )}
          </Card>
        </Col>
        <Col span={8}>
          <Card title="员工业绩排行（前5名）" bodyStyle={{ padding: '12px 20px' }}>
            {topPerformers.length === 0 && (
              <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="暂无数据" />
            )}
            {topPerformers.map((p: any, index: number) => {
              const colors = ['#ff4d4f', '#ff7875', '#ffa39e', '#bfbfbf', '#bfbfbf']
              return (
                <div
                  key={p.user_id}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    padding: '14px 0',
                    borderBottom: '1px solid #f0f0f0',
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                    <div
                      style={{
                        width: 26,
                        height: 26,
                        borderRadius: '50%',
                        background: colors[index] || '#bfbfbf',
                        color: '#fff',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        fontWeight: 700,
                        fontSize: 13,
                      }}
                    >
                      {index + 1}
                    </div>
                    <div style={{ fontWeight: 500, fontSize: 14 }}>{p.full_name || '-'}</div>
                  </div>
                  <div style={{ color: '#cf1322', fontWeight: 600, fontSize: 14 }}>
                    {formatAmount(p.total_amount)}
                  </div>
                </div>
              )
            })}
          </Card>
        </Col>
      </Row>

      {/* 合同状态 + 服务类型金额 + 服务工单状态 */}
      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        <Col span={8}>
          <Card title="合同状态分布" bodyStyle={{ padding: 12 }}>
            {contractPieData.length === 0 ? (
              <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="暂无数据" style={{ padding: '60px 0' }} />
            ) : (
              <Pie {...pieConfig} height={260} />
            )}
          </Card>
        </Col>
        <Col span={8}>
          <Card title="合同金额按服务类型" bodyStyle={{ padding: 12 }}>
            {contractAmountByServiceData.length === 0 ? (
              <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="暂无数据" style={{ padding: '60px 0' }} />
            ) : (
              <Column {...amountByServiceConfig} height={260} />
            )}
          </Card>
        </Col>
        <Col span={8}>
          <Card title="服务工单状态分布" bodyStyle={{ padding: 12 }}>
            {serviceBarData.length === 0 ? (
              <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="暂无数据" style={{ padding: '60px 0' }} />
            ) : (
              <Column {...serviceBarConfig} height={260} />
            )}
          </Card>
        </Col>
      </Row>

      {/* 客户增长趋势 + 逾期合同 */}
      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        <Col span={12}>
          <Card title="客户增长趋势" bodyStyle={{ padding: 12 }}>
            {customerGrowthData.length === 0 ? (
              <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="暂无数据" style={{ padding: '80px 0' }} />
            ) : (
              <Line {...customerGrowthConfig} height={280} />
            )}
          </Card>
        </Col>
        <Col span={12}>
          <Card
            title="逾期应收合同"
            extra={<Tag color="red">{stats.overdue_contract_count} 个</Tag>}
            bodyStyle={{ padding: '12px 20px' }}
          >
            {overdueContracts.length === 0 ? (
              <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="暂无逾期合同" />
            ) : (
              overdueContracts.map((c: any) => (
                <div
                  key={c.id}
                  style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    padding: '12px 0',
                    borderBottom: '1px solid #f0f0f0',
                  }}
                >
                  <div>
                    <div style={{ fontWeight: 500, fontSize: 14 }}>{c.customer_name}</div>
                    <div style={{ fontSize: 12, color: '#8c8c8c', marginTop: 2 }}>
                      {c.contract_no} · 到期 {c.end_date}
                    </div>
                  </div>
                  <div style={{ color: '#ff4d4f', fontWeight: 600, fontSize: 14 }}>
                    {formatAmount(c.receivable_amount)}
                  </div>
                </div>
              ))
            )}
          </Card>
        </Col>
      </Row>
    </div>
  )
}

export default Dashboard

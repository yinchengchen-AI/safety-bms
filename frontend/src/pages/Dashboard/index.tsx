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
  icon: React.ReactNode
  color: 'blue' | 'green' | 'amber' | 'violet' | 'cyan' | 'rose'
  suffix?: string
  formatter?: (v: number | string) => string
}

const colorStyles: Record<KPICardProps['color'], { bg: string; text: string; border: string; bottom: string }> = {
  blue:   { bg: '#eff6ff', text: '#2563eb', border: '#bfdbfe', bottom: 'linear-gradient(90deg,#2563eb,#60a5fa)' },
  green:  { bg: '#f0fdf4', text: '#16a34a', border: '#bbf7d0', bottom: 'linear-gradient(90deg,#16a34a,#4ade80)' },
  amber:  { bg: '#fffbeb', text: '#d97706', border: '#fde68a', bottom: 'linear-gradient(90deg,#d97706,#fbbf24)' },
  violet: { bg: '#f5f3ff', text: '#7c3aed', border: '#ddd6fe', bottom: 'linear-gradient(90deg,#7c3aed,#a78bfa)' },
  cyan:   { bg: '#ecfeff', text: '#0891b2', border: '#cffafe', bottom: 'linear-gradient(90deg,#0891b2,#22d3ee)' },
  rose:   { bg: '#fff1f2', text: '#e11d48', border: '#fecdd3', bottom: 'linear-gradient(90deg,#e11d48,#fb7185)' },
}

const KPICard: React.FC<KPICardProps> = ({
  title,
  value,
  icon,
  color,
  suffix,
  formatter,
}) => {
  const theme = colorStyles[color]
  const display = formatter ? formatter(value as number) : String(value)
  return (
    <div
      style={{
        position: 'relative',
        background: '#fff',
        borderRadius: 16,
        border: '1px solid #f1f5f9',
        padding: '22px 22px 26px',
        boxShadow: '0 1px 2px rgba(0,0,0,0.02), 0 4px 16px rgba(0,0,0,0.03)',
        transition: 'transform 0.2s ease, box-shadow 0.2s ease',
        cursor: 'default',
        overflow: 'hidden',
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.transform = 'translateY(-3px)'
        e.currentTarget.style.boxShadow = '0 8px 24px rgba(0,0,0,0.06)'
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.transform = 'translateY(0)'
        e.currentTarget.style.boxShadow = '0 1px 2px rgba(0,0,0,0.02), 0 4px 16px rgba(0,0,0,0.03)'
      }}
    >
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between' }}>
        <div>
          <div style={{ fontSize: 13, fontWeight: 500, color: '#64748b', letterSpacing: 0.2 }}>{title}</div>
          <div
            style={{
              marginTop: 10,
              fontSize: 28,
              fontWeight: 700,
              color: '#0f172a',
              fontFamily: '"SF Pro Display", "Segoe UI", "PingFang SC", sans-serif',
              fontVariantNumeric: 'tabular-nums',
              letterSpacing: -0.5,
              lineHeight: 1.1,
            }}
          >
            {display}
            {suffix && (
              <span style={{ fontSize: 14, fontWeight: 500, color: '#94a3b8', marginLeft: 4 }}>{suffix}</span>
            )}
          </div>
        </div>
        <div
          style={{
            width: 44,
            height: 44,
            borderRadius: 12,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            background: theme.bg,
            border: `1px solid ${theme.border}`,
            color: theme.text,
            fontSize: 20,
            flexShrink: 0,
          }}
        >
          {icon}
        </div>
      </div>

      <div
        style={{
          position: 'absolute',
          left: 0,
          right: 0,
          bottom: 0,
          height: 3,
          background: theme.bottom,
          opacity: 0.9,
        }}
      />
    </div>
  )
}

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
            icon={<FileTextOutlined />}
            color="blue"
            formatter={(v) => formatAmount(Number(v))}
          />
        </Col>
        <Col span={4}>
          <KPICard
            title="本月收款金额"
            value={stats.monthly_payment_amount || 0}
            icon={<DollarOutlined />}
            color="green"
            formatter={(v) => formatAmount(Number(v))}
          />
        </Col>
        <Col span={4}>
          <KPICard
            title="总应收余额"
            value={stats.total_receivable || 0}
            icon={<RiseOutlined />}
            color="amber"
            formatter={(v) => formatAmount(Number(v))}
          />
        </Col>
        <Col span={4}>
          <KPICard
            title="本月新增客户"
            value={customerGrowthData.reduce((sum: number, d: any) => sum + d['新增客户数'], 0)}
            icon={<UserOutlined />}
            color="violet"
            suffix="个"
          />
        </Col>
        <Col span={4}>
          <KPICard
            title="本月新增工单"
            value={(stats as any).monthly_new_service_orders || 0}
            icon={<ToolOutlined />}
            color="cyan"
            suffix="个"
          />
        </Col>
        <Col span={4}>
          <KPICard
            title="逾期合同数"
            value={stats.overdue_contract_count || 0}
            icon={<ExclamationCircleOutlined />}
            color="rose"
            suffix="个"
          />
        </Col>
      </Row>

      {/* 财务趋势 + 业绩排行 */}
      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        <Col span={16}>
          <Card title="月度开票/收款趋势" bodyStyle={{ padding: 12 }}>
            <Line {...trendConfig} height={300} />
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
            <Pie {...pieConfig} height={260} />
          </Card>
        </Col>
        <Col span={8}>
          <Card title="合同金额按服务类型" bodyStyle={{ padding: 12 }}>
            <Column {...amountByServiceConfig} height={260} />
          </Card>
        </Col>
        <Col span={8}>
          <Card title="服务工单状态分布" bodyStyle={{ padding: 12 }}>
            <Column {...serviceBarConfig} height={260} />
          </Card>
        </Col>
      </Row>

      {/* 客户增长趋势 + 逾期合同 */}
      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        <Col span={12}>
          <Card title="客户增长趋势" bodyStyle={{ padding: 12 }}>
            <Line {...customerGrowthConfig} height={280} />
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

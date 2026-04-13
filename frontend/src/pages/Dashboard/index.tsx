import React from 'react'
import { Row, Col, Card, Statistic, Spin, Tag } from 'antd'
import { FileTextOutlined, DollarOutlined, ExclamationCircleOutlined, RiseOutlined } from '@ant-design/icons'
import { Line, Pie, Column } from '@ant-design/charts'
import { useGetDashboardStatsQuery } from '@/store/api/dashboardApi'
import { formatAmount, ContractStatusLabels, ServiceOrderStatusLabels } from '@/utils/constants'

const Dashboard: React.FC = () => {
  const { data: stats, isLoading } = useGetDashboardStatsQuery()

  if (isLoading) return <div style={{ textAlign: 'center', padding: 80 }}><Spin size="large" /></div>
  if (!stats) return null

  // 月度趋势折线图数据
  const invoiceTrend = (stats.monthly_invoice_trend || []).map((d) => ({
    month: String(d.month),
    value: Number(d.total || 0),
    category: '开票金额' as const,
  }))
  const paymentTrend = (stats.monthly_payment_trend || []).map((d) => ({
    month: String(d.month),
    value: Number(d.total || 0),
    category: '收款金额' as const,
  }))
  const trendData = [...invoiceTrend, ...paymentTrend]

  // 合同状态分布饼图
  const contractPieData = (stats.contract_status_distribution || []).map((d) => ({
    type: ContractStatusLabels[d.status as keyof typeof ContractStatusLabels] || d.status,
    value: Number(d.count),
  }))

  // 服务工单状态分布柱状图
  const serviceBarData = (stats.service_status_distribution || []).map((d) => ({
    status: ServiceOrderStatusLabels[d.status as keyof typeof ServiceOrderStatusLabels] || d.status,
    count: Number(d.count),
  }))

  return (
    <div>
      {/* 顶部统计卡片 */}
      <Row gutter={[16, 16]}>
        <Col span={6}>
          <Card>
            <Statistic
              title="本月开票金额"
              value={stats.monthly_invoice_amount || 0}
              precision={2}
              prefix={<FileTextOutlined />}
              formatter={(v) => formatAmount(Number(v))}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="本月收款金额"
              value={stats.monthly_payment_amount || 0}
              precision={2}
              prefix={<DollarOutlined />}
              formatter={(v) => formatAmount(Number(v))}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="总应收余额"
              value={stats.total_receivable || 0}
              precision={2}
              prefix={<RiseOutlined />}
              valueStyle={{ color: stats.total_receivable > 0 ? '#cf1322' : '#3f8600' }}
              formatter={(v) => formatAmount(Number(v))}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="逾期合同数"
              value={stats.overdue_contract_count || 0}
              prefix={<ExclamationCircleOutlined />}
              valueStyle={{ color: stats.overdue_contract_count > 0 ? '#cf1322' : '#3f8600' }}
              suffix="个"
            />
          </Card>
        </Col>
      </Row>

      {/* 折线图：月度开票/收款趋势 */}
      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        <Col span={16}>
          <Card title="月度开票/收款趋势">
            <Line
              data={trendData}
              xField="month"
              yField="value"
              colorField="category"
              height={280}
              point={{ shapeField: 'circle', sizeField: 4 }}
              axis={{ y: { labelFormatter: (v: number) => `¥${(v / 10000).toFixed(1)}万` } }}
              legend={{ position: 'top-right' }}
              tooltip={{ title: 'month', items: [{ field: 'value', name: '金额', valueFormatter: (v: number) => formatAmount(v) }] }}
            />
          </Card>
        </Col>

        {/* 饼图：合同状态分布 */}
        <Col span={8}>
          <Card title="合同状态分布">
            <Pie
              data={contractPieData}
              angleField="value"
              colorField="type"
              height={280}
              innerRadius={0.5}
              label={{ text: 'type', style: { fontSize: 12 } }}
              legend={{ position: 'bottom' }}
              tooltip={{ items: [{ field: 'value', name: '数量' }] }}
            />
          </Card>
        </Col>
      </Row>

      {/* 柱状图：服务工单状态分布 */}
      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        <Col span={12}>
          <Card title="服务工单状态分布">
            <Column
              data={serviceBarData}
              xField="status"
              yField="count"
              height={240}
              label={{ position: 'inside' }}
              tooltip={{ items: [{ field: 'count', name: '数量' }] }}
              style={{ fill: '#1890ff' }}
            />
          </Card>
        </Col>

        {/* 逾期合同列表 */}
        <Col span={12}>
          <Card title="逾期应收合同" extra={<Tag color="red">{stats.overdue_contract_count} 个</Tag>}>
            {(stats.overdue_contracts || []).slice(0, 5).map((c) => (
              <div key={c.id} style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 0', borderBottom: '1px solid #f0f0f0' }}>
                <div>
                  <div style={{ fontWeight: 500 }}>{c.customer_name}</div>
                  <div style={{ fontSize: 12, color: '#8c8c8c' }}>{c.contract_no} · 到期 {c.end_date}</div>
                </div>
                <div style={{ color: '#ff4d4f', fontWeight: 600 }}>{formatAmount(c.receivable_amount)}</div>
              </div>
            ))}
          </Card>
        </Col>
      </Row>
    </div>
  )
}

export default Dashboard

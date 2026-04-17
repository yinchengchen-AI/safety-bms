import React, { useMemo } from 'react'
import { Row, Col, Spin, Empty, Tag } from 'antd'
import {
  FileTextOutlined,
  DollarOutlined,
  ExclamationCircleOutlined,
  RiseOutlined,
  UserOutlined,
  ToolOutlined,
  TrophyOutlined,
  WarningFilled,
} from '@ant-design/icons'
import { Line, Pie, Column, Area } from '@ant-design/charts'
import { useGetDashboardStatsQuery } from '@/store/api/dashboardApi'
import {
  formatAmount,
  ContractStatusLabels,
  ServiceOrderStatusLabels,
  ServiceTypeLabels,
} from '@/utils/constants'

// ─── Industrial Dashboard ───
// Aesthetic: precision industrial / control-room dark UI

const industrialStyles = `
  @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600;700&family=Noto+Sans+SC:wght@400;500;700&display=swap');

  .industrial-dashboard {
    --bg-deep: #0b0d10;
    --bg-panel: rgba(16, 20, 28, 0.85);
    --border: rgba(148, 163, 184, 0.12);
    --text-primary: #f1f5f9;
    --text-secondary: #94a3b8;
    --accent-cyan: #06b6d4;
    --accent-amber: #f59e0b;
    --accent-rose: #f43f5e;
    --accent-emerald: #10b981;
    --accent-violet: #8b5cf6;
    --glow-cyan: rgba(6, 182, 212, 0.25);
    --glow-amber: rgba(245, 158, 11, 0.25);
    --glow-rose: rgba(244, 63, 94, 0.25);
    font-family: 'Noto Sans SC', sans-serif;
    margin: -24px;
    padding: 24px;
    min-height: calc(100vh - 64px);
    background:
      radial-gradient(1200px 600px at 10% -10%, rgba(6,182,212,0.08), transparent),
      radial-gradient(1000px 500px at 110% 10%, rgba(245,158,11,0.06), transparent),
      linear-gradient(180deg, #0b0d10 0%, #0f1217 100%);
    color: var(--text-primary);
  }

  .industrial-dashboard .panel {
    background: var(--bg-panel);
    border: 1px solid var(--border);
    border-radius: 16px;
    backdrop-filter: blur(12px);
    box-shadow:
      0 1px 0 rgba(255,255,255,0.04) inset,
      0 8px 24px rgba(0,0,0,0.35);
    transition: transform 0.2s ease, box-shadow 0.2s ease;
  }
  .industrial-dashboard .panel:hover {
    transform: translateY(-2px);
    box-shadow:
      0 1px 0 rgba(255,255,255,0.06) inset,
      0 12px 32px rgba(0,0,0,0.45);
  }

  .industrial-dashboard .kpi-value {
    font-family: 'JetBrains Mono', monospace;
    font-variant-numeric: tabular-nums;
  }

  .industrial-dashboard .glow-cyan { box-shadow: 0 0 24px var(--glow-cyan); }
  .industrial-dashboard .glow-amber { box-shadow: 0 0 24px var(--glow-amber); }
  .industrial-dashboard .glow-rose { box-shadow: 0 0 24px var(--glow-rose); }

  .industrial-dashboard .divider-h {
    height: 1px;
    background: linear-gradient(90deg, transparent, rgba(148,163,184,0.18), transparent);
    border: none;
  }

  .industrial-dashboard .rank-1 { background: linear-gradient(135deg, #f59e0b, #fbbf24); color: #0b0d10; }
  .industrial-dashboard .rank-2 { background: linear-gradient(135deg, #94a3b8, #cbd5e1); color: #0b0d10; }
  .industrial-dashboard .rank-3 { background: linear-gradient(135deg, #b45309, #d97706); color: #fff; }

  .industrial-dashboard .chart-container .g2-tooltip {
    background: rgba(11, 13, 16, 0.95) !important;
    border: 1px solid rgba(148, 163, 184, 0.2) !important;
    border-radius: 8px !important;
    color: #f1f5f9 !important;
    box-shadow: 0 8px 24px rgba(0,0,0,0.4) !important;
  }
`

interface KPICardProps {
  title: string
  value: number | string
  icon: React.ReactNode
  color: 'cyan' | 'emerald' | 'amber' | 'violet' | 'rose' | 'slate'
  suffix?: string
  formatter?: (v: number | string) => string
  glow?: boolean
}

const colorMap: Record<KPICardProps['color'], { accent: string; gradient: string; glowVar: string }> = {
  cyan:    { accent: '#06b6d4', gradient: 'linear-gradient(135deg, rgba(6,182,212,0.18), rgba(6,182,212,0.04))', glowVar: 'rgba(6,182,212,0.22)' },
  emerald: { accent: '#10b981', gradient: 'linear-gradient(135deg, rgba(16,185,129,0.18), rgba(16,185,129,0.04))', glowVar: 'rgba(16,185,129,0.22)' },
  amber:   { accent: '#f59e0b', gradient: 'linear-gradient(135deg, rgba(245,158,11,0.18), rgba(245,158,11,0.04))', glowVar: 'rgba(245,158,11,0.22)' },
  violet:  { accent: '#8b5cf6', gradient: 'linear-gradient(135deg, rgba(139,92,246,0.18), rgba(139,92,246,0.04))', glowVar: 'rgba(139,92,246,0.22)' },
  rose:    { accent: '#f43f5e', gradient: 'linear-gradient(135deg, rgba(244,63,94,0.18), rgba(244,63,94,0.04))', glowVar: 'rgba(244,63,94,0.22)' },
  slate:   { accent: '#94a3b8', gradient: 'linear-gradient(135deg, rgba(148,163,184,0.14), rgba(148,163,184,0.03))', glowVar: 'rgba(148,163,184,0.18)' },
}

const KPICard: React.FC<KPICardProps> = ({
  title,
  value,
  icon,
  color,
  suffix,
  formatter,
  glow,
}) => {
  const theme = colorMap[color]
  const display = formatter ? formatter(value as number) : String(value)
  return (
    <div
      className="panel"
      style={{
        padding: '20px 22px',
        background: `linear-gradient(135deg, rgba(16,20,28,0.9), rgba(16,20,28,0.75)), ${theme.gradient}`,
        borderLeft: `3px solid ${theme.accent}`,
        boxShadow: glow ? `0 0 28px ${theme.glowVar}` : undefined,
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div style={{ color: 'var(--text-secondary)', fontSize: 13, fontWeight: 500, letterSpacing: 0.3 }}>
          {title}
        </div>
        <div style={{ color: theme.accent, fontSize: 20, opacity: 0.9 }}>{icon}</div>
      </div>
      <div style={{ marginTop: 10, display: 'flex', alignItems: 'baseline', gap: 6 }}>
        <span className="kpi-value" style={{ fontSize: 26, fontWeight: 700, color: 'var(--text-primary)' }}>
          {display}
        </span>
        {suffix && (
          <span style={{ fontSize: 13, color: 'var(--text-secondary)', fontWeight: 500 }}>{suffix}</span>
        )}
      </div>
    </div>
  )
}

const SectionTitle: React.FC<{ children: React.ReactNode; accent?: string }> = ({ children, accent = '#06b6d4' }) => (
  <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 14 }}>
    <div style={{ width: 4, height: 18, borderRadius: 2, background: accent }} />
    <h3 style={{ margin: 0, fontSize: 16, fontWeight: 700, color: 'var(--text-primary)', letterSpacing: 0.3 }}>
      {children}
    </h3>
  </div>
)

const Dashboard: React.FC = () => {
  const { data: stats, isLoading } = useGetDashboardStatsQuery()

  const {
    trendData,
    contractPieData,
    serviceBarData,
    customerGrowthData,
    contractAmountByServiceData,
    topPerformers,
    overdueContracts,
    monthlyNewCustomers,
  } = useMemo(() => {
    if (!stats) {
      return {
        trendData: [],
        contractPieData: [],
        serviceBarData: [],
        customerGrowthData: [],
        contractAmountByServiceData: [],
        topPerformers: [],
        overdueContracts: [],
        monthlyNewCustomers: 0,
      }
    }
    const invoiceTrend = (stats.monthly_invoice_trend || []).map((d: any) => ({
      月份: `${d.month}月`,
      金额: Number(d.total || 0),
      类型: '开票金额',
    }))
    const paymentTrend = (stats.monthly_payment_trend || []).map((d: any) => ({
      月份: `${d.month}月`,
      金额: Number(d.total || 0),
      类型: '收款金额',
    }))
    const customerGrowth = ((stats as any).customer_growth_trend || []).map((d: any) => ({
      月份: `${d.month}月`,
      新增客户数: Number(d.count),
    }))
    return {
      trendData: [...invoiceTrend, ...paymentTrend],
      contractPieData: (stats.contract_status_distribution || []).map((d: any) => ({
        状态: ContractStatusLabels[d.status as keyof typeof ContractStatusLabels] || d.status,
        数量: Number(d.count),
      })),
      serviceBarData: (stats.service_status_distribution || []).map((d: any) => ({
        状态: ServiceOrderStatusLabels[d.status as keyof typeof ServiceOrderStatusLabels] || d.status,
        数量: Number(d.count),
      })),
      customerGrowthData: customerGrowth,
      contractAmountByServiceData: ((stats as any).contract_amount_by_service_type || []).map((d: any) => ({
        服务类型: ServiceTypeLabels[d.service_type as keyof typeof ServiceTypeLabels] || d.service_type,
        金额: Number(d.total_amount),
      })),
      topPerformers: (stats as any).top_performers || [],
      overdueContracts: (stats.overdue_contracts || []).slice(0, 5),
      monthlyNewCustomers: customerGrowth.reduce((sum: number, d: any) => sum + d.新增客户数, 0),
    }
  }, [stats])

  const baseChartTheme = {
    background: 'transparent',
  }

  const trendConfig = {
    ...baseChartTheme,
    data: trendData,
    xField: '月份',
    yField: '金额',
    seriesField: '类型',
    colorField: '类型',
    smooth: true,
    color: ['#06b6d4', '#10b981'],
    legend: {
      position: 'top-right' as const,
      itemName: { style: { fill: '#94a3b8', fontSize: 12 } },
    },
    axis: {
      x: { labelFill: '#94a3b8', gridStroke: 'rgba(148,163,184,0.10)', title: { text: '月份', fill: '#94a3b8' } },
      y: { labelFill: '#94a3b8', gridStroke: 'rgba(148,163,184,0.10)', title: { text: '金额', fill: '#94a3b8' } },
    },
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
    ...baseChartTheme,
    data: contractPieData,
    angleField: '数量',
    colorField: '状态',
    innerRadius: 0.55,
    legend: {
      color: {
        position: 'right' as const,
        layout: { justifyContent: 'center' },
        itemName: { style: { fill: '#94a3b8', fontSize: 12 } },
      },
    },
    axis: false,
    label: {
      text: (d: any) => `${d['状态']}\n${d['数量']}`,
      style: { fontSize: 11, fill: '#e2e8f0', fontWeight: 500 },
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
    ...baseChartTheme,
    data: serviceBarData,
    xField: '状态',
    yField: '数量',
    color: '#06b6d4',
    axis: {
      x: { labelFill: '#94a3b8', gridStroke: 'rgba(148,163,184,0.10)', title: { text: '状态', fill: '#94a3b8' } },
      y: { labelFill: '#94a3b8', gridStroke: 'rgba(148,163,184,0.10)', title: { text: '数量（个）', fill: '#94a3b8' } },
    },
    label: {
      text: (d: any) => `${d['数量']}`,
      style: { fill: '#fff', fontWeight: 600 },
    },
    tooltip: {
      items: [
        (d: any) => ({
          name: '工单数量',
          value: `${d['数量']}个`,
        }),
      ],
    },
    style: { radiusTopLeft: 4, radiusTopRight: 4, maxWidth: 28 },
  }

  const amountByServiceConfig = {
    ...baseChartTheme,
    data: contractAmountByServiceData,
    xField: '服务类型',
    yField: '金额',
    color: '#8b5cf6',
    axis: {
      x: {
        labelFill: '#94a3b8',
        gridStroke: 'rgba(148,163,184,0.10)',
        title: { text: '服务类型', fill: '#94a3b8' },
        labelAutoRotate: true,
      },
      y: {
        labelFill: '#94a3b8',
        gridStroke: 'rgba(148,163,184,0.10)',
        title: { text: '金额（万）', fill: '#94a3b8' },
        labelFormatter: (v: number) => `¥${(v / 10000).toFixed(1)}万`,
      },
    },
    label: {
      text: (d: any) => `¥${(d['金额'] / 10000).toFixed(1)}万`,
      style: { fill: '#fff', fontWeight: 600 },
    },
    tooltip: {
      items: [
        (d: any) => ({
          name: '合同金额',
          value: formatAmount(d['金额']),
        }),
      ],
    },
    style: { radiusTopLeft: 4, radiusTopRight: 4, maxWidth: 28 },
  }

  const customerGrowthConfig = {
    ...baseChartTheme,
    data: customerGrowthData,
    xField: '月份',
    yField: '新增客户数',
    smooth: true,
    color: '#f59e0b',
    areaStyle: { fill: 'rgba(245, 158, 11, 0.18)' },
    axis: {
      x: { labelFill: '#94a3b8', gridStroke: 'rgba(148,163,184,0.10)', title: { text: '月份', fill: '#94a3b8' } },
      y: { labelFill: '#94a3b8', gridStroke: 'rgba(148,163,184,0.10)', title: { text: '新增客户数（个）', fill: '#94a3b8' } },
    },
    tooltip: {
      items: [
        (d: any) => ({
          name: '新增客户数',
          value: `${d['新增客户数']} 个`,
        }),
      ],
    },
  }

  if (isLoading) {
    return (
      <div className="industrial-dashboard" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: '60vh' }}>
        <style>{industrialStyles}</style>
        <Spin size="large" style={{ color: '#06b6d4' }} />
      </div>
    )
  }
  if (!stats) return null

  return (
    <div className="industrial-dashboard">
      <style>{industrialStyles}</style>

      {/* KPI 卡片 */}
      <Row gutter={[16, 16]}>
        <Col xs={24} sm={12} md={8} lg={4}>
          <KPICard
            title="本月开票金额"
            value={stats.monthly_invoice_amount || 0}
            icon={<FileTextOutlined />}
            color="cyan"
            formatter={(v) => formatAmount(Number(v))}
          />
        </Col>
        <Col xs={24} sm={12} md={8} lg={4}>
          <KPICard
            title="本月收款金额"
            value={stats.monthly_payment_amount || 0}
            icon={<DollarOutlined />}
            color="emerald"
            formatter={(v) => formatAmount(Number(v))}
          />
        </Col>
        <Col xs={24} sm={12} md={8} lg={4}>
          <KPICard
            title="总应收余额"
            value={stats.total_receivable || 0}
            icon={<RiseOutlined />}
            color="amber"
            formatter={(v) => formatAmount(Number(v))}
          />
        </Col>
        <Col xs={24} sm={12} md={8} lg={4}>
          <KPICard
            title="本月新增客户"
            value={monthlyNewCustomers}
            icon={<UserOutlined />}
            color="violet"
            suffix="个"
          />
        </Col>
        <Col xs={24} sm={12} md={8} lg={4}>
          <KPICard
            title="本月新增工单"
            value={(stats as any).monthly_new_service_orders || 0}
            icon={<ToolOutlined />}
            color="slate"
            suffix="个"
          />
        </Col>
        <Col xs={24} sm={12} md={8} lg={4}>
          <KPICard
            title="逾期合同数"
            value={stats.overdue_contract_count || 0}
            icon={<ExclamationCircleOutlined />}
            color="rose"
            suffix="个"
            glow={(stats.overdue_contract_count || 0) > 0}
          />
        </Col>
      </Row>

      {/* 财务趋势 + 业绩排行 */}
      <Row gutter={[16, 16]} style={{ marginTop: 20 }}>
        <Col xs={24} lg={16}>
          <div className="panel" style={{ padding: 18 }}>
            <SectionTitle accent="#06b6d4">月度开票 / 收款趋势</SectionTitle>
            <div className="chart-container">
              <Line {...trendConfig} height={300} />
            </div>
          </div>
        </Col>
        <Col xs={24} lg={8}>
          <div className="panel" style={{ padding: '18px 20px', height: '100%' }}>
            <SectionTitle accent="#f59e0b">
              <TrophyOutlined style={{ marginRight: 8 }} />
              员工业绩排行（前5名）
            </SectionTitle>
            {topPerformers.length === 0 && (
              <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="暂无数据" style={{ marginTop: 40 }} />
            )}
            {topPerformers.map((p: any, index: number) => {
              const rankClass = index < 3 ? `rank-${index + 1}` : ''
              const bg = index >= 3 ? 'rgba(148,163,184,0.15)' : undefined
              const color = index >= 3 ? '#94a3b8' : undefined
              return (
                <div
                  key={p.user_id}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    padding: '13px 0',
                    borderBottom: '1px solid rgba(148,163,184,0.10)',
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                    <div
                      className={rankClass}
                      style={{
                        width: 26,
                        height: 26,
                        borderRadius: '50%',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        fontWeight: 700,
                        fontSize: 12,
                        background: bg,
                        color,
                      }}
                    >
                      {index + 1}
                    </div>
                    <div style={{ fontWeight: 500, fontSize: 14, color: 'var(--text-primary)' }}>
                      {p.full_name || '-'}
                    </div>
                  </div>
                  <div className="kpi-value" style={{ color: '#f59e0b', fontWeight: 600, fontSize: 15 }}>
                    {formatAmount(p.total_amount)}
                  </div>
                </div>
              )
            })}
          </div>
        </Col>
      </Row>

      {/* 合同状态 + 服务类型金额 + 服务工单状态 */}
      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        <Col xs={24} md={12} lg={8}>
          <div className="panel" style={{ padding: 18 }}>
            <SectionTitle accent="#8b5cf6">合同状态分布</SectionTitle>
            <div className="chart-container">
              <Pie {...pieConfig} height={260} />
            </div>
          </div>
        </Col>
        <Col xs={24} md={12} lg={8}>
          <div className="panel" style={{ padding: 18 }}>
            <SectionTitle accent="#f59e0b">合同金额按服务类型</SectionTitle>
            <div className="chart-container">
              <Column {...amountByServiceConfig} height={260} />
            </div>
          </div>
        </Col>
        <Col xs={24} md={12} lg={8}>
          <div className="panel" style={{ padding: 18 }}>
            <SectionTitle accent="#06b6d4">服务工单状态分布</SectionTitle>
            <div className="chart-container">
              <Column {...serviceBarConfig} height={260} />
            </div>
          </div>
        </Col>
      </Row>

      {/* 客户增长趋势 + 逾期合同 */}
      <Row gutter={[16, 16]} style={{ marginTop: 16, paddingBottom: 8 }}>
        <Col xs={24} lg={12}>
          <div className="panel" style={{ padding: 18 }}>
            <SectionTitle accent="#10b981">客户增长趋势</SectionTitle>
            <div className="chart-container">
              <Area {...customerGrowthConfig} height={280} />
            </div>
          </div>
        </Col>
        <Col xs={24} lg={12}>
          <div
            className="panel"
            style={{
              padding: '18px 20px',
              borderLeft: (stats.overdue_contract_count || 0) > 0 ? '3px solid #f43f5e' : undefined,
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 14 }}>
              <SectionTitle accent="#f43f5e">逾期应收合同</SectionTitle>
              <Tag
                style={{
                  background: (stats.overdue_contract_count || 0) > 0 ? 'rgba(244,63,94,0.15)' : 'rgba(148,163,184,0.15)',
                  borderColor: (stats.overdue_contract_count || 0) > 0 ? 'rgba(244,63,94,0.35)' : 'rgba(148,163,184,0.25)',
                  color: (stats.overdue_contract_count || 0) > 0 ? '#f43f5e' : '#94a3b8',
                  fontWeight: 600,
                }}
              >
                {(stats.overdue_contract_count || 0) > 0 ? (
                  <>
                    <WarningFilled style={{ marginRight: 4 }} />
                    {stats.overdue_contract_count} 个
                  </>
                ) : (
                  <>{stats.overdue_contract_count} 个</>
                )}
              </Tag>
            </div>
            {overdueContracts.length === 0 ? (
              <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="暂无逾期合同" style={{ marginTop: 40 }} />
            ) : (
              overdueContracts.map((c: any) => (
                <div
                  key={c.id}
                  style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    padding: '12px 0',
                    borderBottom: '1px solid rgba(148,163,184,0.10)',
                  }}
                >
                  <div>
                    <div style={{ fontWeight: 500, fontSize: 14, color: 'var(--text-primary)' }}>
                      {c.customer_name}
                    </div>
                    <div style={{ fontSize: 12, color: 'var(--text-secondary)', marginTop: 3 }}>
                      {c.contract_no} · 到期 {c.end_date}
                    </div>
                  </div>
                  <div className="kpi-value" style={{ color: '#f43f5e', fontWeight: 600, fontSize: 15 }}>
                    {formatAmount(c.receivable_amount)}
                  </div>
                </div>
              ))
            )}
          </div>
        </Col>
      </Row>
    </div>
  )
}

export default Dashboard

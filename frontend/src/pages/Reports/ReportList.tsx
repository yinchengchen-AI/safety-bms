import React from 'react'
import { useNavigate } from 'react-router-dom'
import { Card, Row, Col, Typography } from 'antd'
import {
  FileTextOutlined,
  ToolOutlined,
  TeamOutlined,
  InboxOutlined,
  DollarOutlined,
} from '@ant-design/icons'
import { useListReportsQuery } from '@/store/api/reportsApi'

const { Title, Text } = Typography

const reportIcons: Record<string, React.ReactNode> = {
  'contract-execution': <FileTextOutlined />,
  'service-order-completion': <ToolOutlined />,
  'customer-payment-analysis': <TeamOutlined />,
  'invoice-detail': <InboxOutlined />,
  'payment-detail': <DollarOutlined />,
  'customer-ledger-summary': <TeamOutlined />,
}

const ReportList: React.FC = () => {
  const navigate = useNavigate()
  const { data: reports, isLoading } = useListReportsQuery()

  return (
    <div>
      <Title level={4}>报表中心</Title>
      <Text type="secondary">选择预置报表，设定参数后查询并导出 Excel</Text>
      <Row gutter={[16, 16]} style={{ marginTop: 24 }}>
        {reports?.map((report) => (
          <Col xs={24} sm={12} lg={8} key={report.id}>
            <Card
              hoverable
              loading={isLoading}
              onClick={() => navigate(`/reports/${report.id}`)}
            >
              <Card.Meta
                avatar={reportIcons[report.id] || <FileTextOutlined />}
                title={report.name}
                description={report.description}
              />
            </Card>
          </Col>
        ))}
      </Row>
    </div>
  )
}

export default ReportList

import React, { useEffect, useMemo, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import {
  Button,
  Card,
  Col,
  DatePicker,
  Form,
  Row,
  Select,
  Space,
  Table,
  Typography,
  message,
} from 'antd'
import { ArrowLeftOutlined, DownloadOutlined, SearchOutlined } from '@ant-design/icons'
import dayjs, { Dayjs } from 'dayjs'

import { useLazyGetReportDataQuery, useListReportsQuery, getReportExportUrl } from '@/store/api/reportsApi'
import { useListServiceTypesQuery } from '@/store/api/serviceTypesApi'
import { downloadExport } from '@/utils/export'
import {
  ContractStatusLabels,
  CustomerStatusLabels,
  formatAmount,
  InvoiceStatusLabels,
  InvoiceTypeLabels,
  PaymentMethodLabels,
  ServiceOrderStatusLabels,
} from '@/utils/constants'

const { Title } = Typography
const { RangePicker } = DatePicker

const ReportViewer: React.FC = () => {
  const { reportId } = useParams<{ reportId: string }>()
  const navigate = useNavigate()
  const [form] = Form.useForm()
  const { data: reports } = useListReportsQuery()
  const { data: serviceTypesData } = useListServiceTypesQuery({ page_size: 100 })
  const [trigger, { data, isFetching }] = useLazyGetReportDataQuery()
  const [currentPage, setCurrentPage] = useState(1)
  const [pageSize, setPageSize] = useState(20)

  const reportMeta = useMemo(() => reports?.find((r) => r.id === reportId), [reports, reportId])

  const serviceTypeMap = useMemo(() => {
    const map = new Map<number, string>()
    ;(serviceTypesData?.items || []).forEach((st) => map.set(st.id, st.name))
    return map
  }, [serviceTypesData])

  const serviceTypeOptions = useMemo(() => {
    return (serviceTypesData?.items || []).map((st) => ({
      label: st.name,
      value: st.id,
    }))
  }, [serviceTypesData])

  const [range, setRange] = useState<[Dayjs | null, Dayjs | null] | null>([dayjs().startOf('year'), dayjs().endOf('month')])

  const buildParams = (page = currentPage, size = pageSize) => {
    const values = form.getFieldsValue()
    return {
      reportId: reportId!,
      page,
      page_size: size,
      date_from: range?.[0] ? range[0].format('YYYY-MM-DD') : undefined,
      date_to: range?.[1] ? range[1].format('YYYY-MM-DD') : undefined,
      service_type: values.service_type,
      status: values.status,
      payment_method: values.payment_method,
    }
  }

  const handleSearch = (page = 1, size = pageSize) => {
    if (!reportId) return
    setCurrentPage(page)
    setPageSize(size)
    trigger(buildParams(page, size))
  }

  useEffect(() => {
    if (reportId) {
      handleSearch(1, 20)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [reportId])

  const handleExport = async () => {
    if (!reportId) return
    try {
      const url = getReportExportUrl(buildParams(1, 10000))
      await downloadExport(url, `${reportMeta?.name || reportId}.xlsx`)
      message.success('导出成功')
    } catch (err: any) {
      message.error(err.message || '导出失败')
    }
  }

  const columns = useMemo(() => {
    switch (reportId) {
      case 'contract-execution':
        return [
          { title: '合同编号', dataIndex: 'contract_no', key: 'contract_no' },
          { title: '合同标题', dataIndex: 'contract_title', key: 'contract_title' },
          { title: '客户名称', dataIndex: 'customer_name', key: 'customer_name' },
          { title: '签订日期', dataIndex: 'sign_date', key: 'sign_date' },
          { title: '签约额', dataIndex: 'total_amount', key: 'total_amount', render: (v: number) => formatAmount(v), align: 'right' as const },
          { title: '已开票', dataIndex: 'invoiced_amount', key: 'invoiced_amount', render: (v: number) => formatAmount(v), align: 'right' as const },
          { title: '已收款', dataIndex: 'received_amount', key: 'received_amount', render: (v: number) => formatAmount(v), align: 'right' as const },
          { title: '应收余额', dataIndex: 'receivable_balance', key: 'receivable_balance', render: (v: number) => formatAmount(v), align: 'right' as const },
          { title: '状态', dataIndex: 'status', key: 'status', render: (v: string) => ContractStatusLabels[v] || v },
          { title: '服务类型', dataIndex: 'service_type', key: 'service_type', render: (v: number) => serviceTypeMap.get(v) || v },
        ]
      case 'service-order-completion':
        return [
          { title: '订单编号', dataIndex: 'order_no', key: 'order_no' },
          { title: '标题', dataIndex: 'title', key: 'title' },
          { title: '客户名称', dataIndex: 'customer_name', key: 'customer_name' },
          { title: '关联合同', dataIndex: 'contract_no', key: 'contract_no' },
          { title: '计划开始', dataIndex: 'planned_start', key: 'planned_start' },
          { title: '计划结束', dataIndex: 'planned_end', key: 'planned_end' },
          { title: '实际开始', dataIndex: 'actual_start', key: 'actual_start' },
          { title: '实际结束', dataIndex: 'actual_end', key: 'actual_end' },
          { title: '状态', dataIndex: 'status', key: 'status', render: (v: string) => ServiceOrderStatusLabels[v] || v },
          { title: '是否按期', dataIndex: 'on_time', key: 'on_time', render: (v: boolean | null) => (v === true ? '是' : v === false ? '否' : '-') },
          { title: '负责人', dataIndex: 'assignee_name', key: 'assignee_name' },
        ]
      case 'customer-payment-analysis':
        return [
          { title: '客户名称', dataIndex: 'customer_name', key: 'customer_name' },
          { title: '合同数量', dataIndex: 'contract_count', key: 'contract_count', align: 'center' as const },
          { title: '合同总额', dataIndex: 'total_contract_amount', key: 'total_contract_amount', render: (v: number) => formatAmount(v), align: 'right' as const },
          { title: '开票总额', dataIndex: 'total_invoiced_amount', key: 'total_invoiced_amount', render: (v: number) => formatAmount(v), align: 'right' as const },
          { title: '收款总额', dataIndex: 'total_received_amount', key: 'total_received_amount', render: (v: number) => formatAmount(v), align: 'right' as const },
          { title: '回款率', dataIndex: 'collection_rate', key: 'collection_rate', render: (v: number) => `${v}%`, align: 'right' as const },
        ]
      case 'invoice-detail':
        return [
          { title: '发票编号', dataIndex: 'invoice_no', key: 'invoice_no' },
          { title: '关联合同', dataIndex: 'contract_no', key: 'contract_no' },
          { title: '客户名称', dataIndex: 'customer_name', key: 'customer_name' },
          { title: '发票类型', dataIndex: 'invoice_type', key: 'invoice_type', render: (v: string) => InvoiceTypeLabels[v] || v },
          { title: '金额', dataIndex: 'amount', key: 'amount', render: (v: number) => formatAmount(v), align: 'right' as const },
          { title: '状态', dataIndex: 'status', key: 'status', render: (v: string) => InvoiceStatusLabels[v] || v },
          { title: '开票日期', dataIndex: 'invoice_date', key: 'invoice_date' },
          { title: '申请人', dataIndex: 'applied_by_name', key: 'applied_by_name' },
        ]
      case 'payment-detail':
        return [
          { title: '收款编号', dataIndex: 'payment_no', key: 'payment_no' },
          { title: '关联合同', dataIndex: 'contract_no', key: 'contract_no' },
          { title: '客户名称', dataIndex: 'customer_name', key: 'customer_name' },
          { title: '付款方式', dataIndex: 'payment_method', key: 'payment_method', render: (v: string) => PaymentMethodLabels[v] || v },
          { title: '金额', dataIndex: 'amount', key: 'amount', render: (v: number) => formatAmount(v), align: 'right' as const },
          { title: '收款日期', dataIndex: 'payment_date', key: 'payment_date' },
          { title: '录入人', dataIndex: 'created_by_name', key: 'created_by_name' },
        ]
      case 'customer-ledger-summary':
        return [
          { title: '客户名称', dataIndex: 'customer_name', key: 'customer_name' },
          { title: '行业', dataIndex: 'industry', key: 'industry' },
          { title: '联系人', dataIndex: 'contact_name', key: 'contact_name' },
          { title: '联系电话', dataIndex: 'contact_phone', key: 'contact_phone' },
          { title: '合同数量', dataIndex: 'contract_count', key: 'contract_count', align: 'center' as const },
          { title: '合同总额', dataIndex: 'total_contract_amount', key: 'total_contract_amount', render: (v: number) => formatAmount(v), align: 'right' as const },
          { title: '开票总额', dataIndex: 'total_invoiced_amount', key: 'total_invoiced_amount', render: (v: number) => formatAmount(v), align: 'right' as const },
          { title: '收款总额', dataIndex: 'total_received_amount', key: 'total_received_amount', render: (v: number) => formatAmount(v), align: 'right' as const },
          { title: '状态', dataIndex: 'status', key: 'status', render: (v: string) => CustomerStatusLabels[v] || v },
        ]
      default:
        return []
    }
  }, [reportId])

  const showServiceTypeFilter = reportId === 'contract-execution' || reportId === 'service-order-completion'
  const showStatusFilter = reportId === 'contract-execution' || reportId === 'service-order-completion' || reportId === 'invoice-detail' || reportId === 'customer-ledger-summary'
  const showPaymentMethodFilter = reportId === 'payment-detail'

  const statusOptions = useMemo(() => {
    if (reportId === 'contract-execution') return Object.entries(ContractStatusLabels).map(([k, v]) => ({ label: v, value: k }))
    if (reportId === 'service-order-completion') return Object.entries(ServiceOrderStatusLabels).map(([k, v]) => ({ label: v, value: k }))
    if (reportId === 'invoice-detail') return Object.entries(InvoiceStatusLabels).map(([k, v]) => ({ label: v, value: k }))
    if (reportId === 'customer-ledger-summary') return Object.entries(CustomerStatusLabels).map(([k, v]) => ({ label: v, value: k }))
    return []
  }, [reportId])

  return (
    <div>
      <Space style={{ marginBottom: 16 }}>
        <Button icon={<ArrowLeftOutlined />} onClick={() => navigate('/reports')}>
          返回报表列表
        </Button>
        <Title level={4} style={{ margin: 0 }}>
          {reportMeta?.name || reportId}
        </Title>
      </Space>

      <Card style={{ marginBottom: 16 }}>
        <Form form={form} layout="inline">
          <Form.Item label="日期范围">
            <RangePicker value={range} onChange={(vals) => setRange(vals as [Dayjs | null, Dayjs | null] | null)} />
          </Form.Item>
          {showServiceTypeFilter && (
            <Form.Item name="service_type" label="服务类型">
              <Select allowClear placeholder="请选择" options={serviceTypeOptions} style={{ width: 160 }} />
            </Form.Item>
          )}
          {showStatusFilter && (
            <Form.Item name="status" label="状态">
              <Select allowClear placeholder="请选择" options={statusOptions} style={{ width: 140 }} />
            </Form.Item>
          )}
          {showPaymentMethodFilter && (
            <Form.Item name="payment_method" label="付款方式">
              <Select
                allowClear
                placeholder="请选择"
                options={Object.entries(PaymentMethodLabels).map(([k, v]) => ({ label: v, value: k }))}
                style={{ width: 140 }}
              />
            </Form.Item>
          )}
          <Form.Item>
            <Button type="primary" icon={<SearchOutlined />} onClick={() => handleSearch(1, pageSize)} loading={isFetching}>
              查询
            </Button>
          </Form.Item>
          <Form.Item>
            <Button icon={<DownloadOutlined />} onClick={handleExport} disabled={!data || data.total === 0}>
              导出 Excel
            </Button>
          </Form.Item>
        </Form>
      </Card>

      <Table
        columns={columns}
        dataSource={data?.items || []}
        rowKey={(record, index) => `${reportId}-${index}`}
        loading={isFetching}
        pagination={{
          current: currentPage,
          pageSize: pageSize,
          total: data?.total || 0,
          showSizeChanger: true,
          showTotal: (total) => `共 ${total} 条`,
          onChange: (page, size) => handleSearch(page, size || 20),
        }}
        scroll={{ x: 'max-content' }}
      />
    </div>
  )
}

export default ReportViewer

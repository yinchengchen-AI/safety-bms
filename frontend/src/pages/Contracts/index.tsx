import React, { useState, useMemo } from 'react'
import { Table, Button, Input, Select, Tag, Space, message, Drawer, Form, InputNumber, DatePicker, Descriptions } from 'antd'
import { PlusOutlined } from '@ant-design/icons'
import { useListContractsQuery, useCreateContractMutation, useUpdateContractStatusMutation, useGetContractQuery } from '@/store/api/contractsApi'
import { useListCustomersQuery } from '@/store/api/customersApi'
import { ContractStatusLabels, ServiceTypeLabels, PaymentPlanLabels, formatAmount } from '@/utils/constants'
import type { Contract, ContractStatus, ServiceType, PaymentPlan } from '@/types'
import dayjs from 'dayjs'
import type { Dayjs } from 'dayjs'

interface ContractFormValues {
  contract_no: string
  title: string
  customer_id: number
  service_type: ServiceType
  total_amount: number
  payment_plan?: PaymentPlan
  sign_date?: Dayjs
  start_date?: Dayjs
  end_date?: Dayjs
  remark?: string
}

const statusColors: Record<ContractStatus, string> = {
  draft: 'default', review: 'processing', active: 'success', completed: 'green', terminated: 'error',
}

const Contracts: React.FC = () => {
  const [page, setPage] = useState(1)
  const [keyword, setKeyword] = useState('')
  const [status, setStatus] = useState<ContractStatus | undefined>()
  const [createOpen, setCreateOpen] = useState(false)
  const [selectedId, setSelectedId] = useState<number | null>(null)
  const [form] = Form.useForm()

  const { data, isLoading } = useListContractsQuery({ page, page_size: 20, keyword, status })
  const { data: customersData } = useListCustomersQuery({ page: 1, page_size: 200 })
  const [createContract, { isLoading: creating }] = useCreateContractMutation()
  const [updateStatus] = useUpdateContractStatusMutation()

  const handleCreate = async (values: ContractFormValues) => {
    const payload = {
      ...values,
      sign_date: values.sign_date ? dayjs(values.sign_date).format('YYYY-MM-DD') : undefined,
      start_date: values.start_date ? dayjs(values.start_date).format('YYYY-MM-DD') : undefined,
      end_date: values.end_date ? dayjs(values.end_date).format('YYYY-MM-DD') : undefined,
    }
    try {
      await createContract(payload).unwrap()
      message.success('合同创建成功')
      setCreateOpen(false)
      form.resetFields()
    } catch (err: any) {
      message.error(err?.data?.detail || '创建失败')
    }
  }

  const columns = useMemo(() => [
    { title: '合同编号', dataIndex: 'contract_no', key: 'contract_no', render: (no: string, r: Contract) => (
      <Button type="link" onClick={() => setSelectedId(r.id)}>{no}</Button>
    )},
    { title: '合同名称', dataIndex: 'title', key: 'title', ellipsis: true },
    { title: '客户', dataIndex: 'customer_name', key: 'customer_name' },
    { title: '服务类型', dataIndex: 'service_type', key: 'service_type', render: (s: ServiceType) => ServiceTypeLabels[s] },
    { title: '合同金额', dataIndex: 'total_amount', key: 'total_amount', render: formatAmount },
    { title: '状态', dataIndex: 'status', key: 'status', render: (s: ContractStatus) => (
      <Tag color={statusColors[s]}>{ContractStatusLabels[s]}</Tag>
    )},
    { title: '签订日期', dataIndex: 'sign_date', key: 'sign_date' },
    { title: '操作', key: 'action', render: (_: any, r: Contract) => (
      <Space>
        {r.status === 'draft' && (
          <Button size="small" onClick={() => updateStatus({ id: r.id, status: 'review' })}>提交审核</Button>
        )}
        {r.status === 'review' && (
          <Button size="small" type="primary" onClick={() => updateStatus({ id: r.id, status: 'active' })}>审核通过</Button>
        )}
      </Space>
    )},
  ], [updateStatus])

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 16 }}>
        <Space>
          <Input.Search placeholder="搜索合同编号/名称" onSearch={setKeyword} style={{ width: 240 }} allowClear />
          <Select placeholder="合同状态" allowClear style={{ width: 120 }} onChange={setStatus}
            options={Object.entries(ContractStatusLabels).map(([v, l]) => ({ value: v, label: l }))} />
        </Space>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => setCreateOpen(true)}>新建合同</Button>
      </div>

      <Table rowKey="id" columns={columns} dataSource={data?.items} loading={isLoading}
        pagination={{ current: page, pageSize: 20, total: data?.total, onChange: setPage, showTotal: (t) => `共 ${t} 条` }} />

      <Drawer title="新建合同" open={createOpen} onClose={() => setCreateOpen(false)} width={560} footer={
        <Space style={{ float: 'right' }}>
          <Button onClick={() => setCreateOpen(false)}>取消</Button>
          <Button type="primary" loading={creating} onClick={() => form.submit()}>创建</Button>
        </Space>
      }>
        <Form form={form} layout="vertical" onFinish={handleCreate}>
          <Form.Item name="contract_no" label="合同编号" rules={[{ required: true }]}><Input /></Form.Item>
          <Form.Item name="title" label="合同名称" rules={[{ required: true }]}><Input /></Form.Item>
          <Form.Item name="customer_id" label="客户" rules={[{ required: true }]}>
            <Select showSearch optionFilterProp="label"
              options={customersData?.items.map(c => ({ value: c.id, label: c.name })) || []} />
          </Form.Item>
          <Form.Item name="service_type" label="服务类型" rules={[{ required: true }]}>
            <Select options={Object.entries(ServiceTypeLabels).map(([v, l]) => ({ value: v, label: l }))} />
          </Form.Item>
          <Form.Item name="total_amount" label="合同金额(元)" rules={[{ required: true }]}>
            <InputNumber style={{ width: '100%' }} min={0} precision={2} />
          </Form.Item>
          <Form.Item name="payment_plan" label="付款方式" initialValue="once">
            <Select options={Object.entries(PaymentPlanLabels).map(([v, l]) => ({ value: v, label: l }))} />
          </Form.Item>
          <Form.Item name="sign_date" label="签订日期"><DatePicker style={{ width: '100%' }} /></Form.Item>
          <Form.Item name="start_date" label="服务开始日期"><DatePicker style={{ width: '100%' }} /></Form.Item>
          <Form.Item name="end_date" label="服务结束日期"><DatePicker style={{ width: '100%' }} /></Form.Item>
          <Form.Item name="remark" label="备注"><Input.TextArea rows={3} /></Form.Item>
        </Form>
      </Drawer>

      {selectedId && <ContractDetail id={selectedId} onClose={() => setSelectedId(null)} />}
    </div>
  )
}

const ContractDetail: React.FC<{ id: number; onClose: () => void }> = ({ id, onClose }) => {
  const { data } = useGetContractQuery(id)
  if (!data) return null
  return (
    <Drawer title="合同详情" open width={680} onClose={onClose}>
      <Descriptions column={2} bordered size="small">
        <Descriptions.Item label="合同编号">{data.contract_no}</Descriptions.Item>
        <Descriptions.Item label="状态"><Tag>{ContractStatusLabels[data.status]}</Tag></Descriptions.Item>
        <Descriptions.Item label="合同名称" span={2}>{data.title}</Descriptions.Item>
        <Descriptions.Item label="客户">{data.customer_name}</Descriptions.Item>
        <Descriptions.Item label="服务类型">{ServiceTypeLabels[data.service_type]}</Descriptions.Item>
        <Descriptions.Item label="合同金额">{formatAmount(data.total_amount)}</Descriptions.Item>
        <Descriptions.Item label="付款方式">{PaymentPlanLabels[data.payment_plan]}</Descriptions.Item>
        <Descriptions.Item label="已开票金额">{formatAmount(data.invoiced_amount || 0)}</Descriptions.Item>
        <Descriptions.Item label="已收款金额">{formatAmount(data.received_amount || 0)}</Descriptions.Item>
        <Descriptions.Item label="签订日期">{data.sign_date}</Descriptions.Item>
        <Descriptions.Item label="服务期">{data.start_date} ~ {data.end_date}</Descriptions.Item>
        <Descriptions.Item label="备注" span={2}>{data.remark}</Descriptions.Item>
      </Descriptions>
    </Drawer>
  )
}

export default Contracts

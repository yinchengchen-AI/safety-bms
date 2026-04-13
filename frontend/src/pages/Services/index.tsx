import React, { useState, useMemo } from 'react'
import { Table, Button, Input, Select, Tag, Space, message, Drawer, Form, DatePicker, Descriptions } from 'antd'
import { PlusOutlined } from '@ant-design/icons'
import { useListServiceOrdersQuery, useCreateServiceOrderMutation, useUpdateServiceStatusMutation, useGetServiceOrderQuery } from '@/store/api/servicesApi'
import { useListContractsQuery } from '@/store/api/contractsApi'
import { ServiceTypeLabels, ServiceOrderStatusLabels } from '@/utils/constants'
import type { ServiceOrder, ServiceOrderStatus, ServiceType } from '@/types'
import dayjs from 'dayjs'
import type { Dayjs } from 'dayjs'

interface ServiceFormValues {
  order_no: string
  contract_id: number
  service_type: ServiceType
  title: string
  planned_start?: Dayjs
  planned_end?: Dayjs
  remark?: string
}

const statusColors: Record<ServiceOrderStatus, string> = {
  pending: 'default', in_progress: 'processing', completed: 'success', accepted: 'green',
}

const Services: React.FC = () => {
  const [page, setPage] = useState(1)
  const [keyword, setKeyword] = useState('')
  const [status, setStatus] = useState<ServiceOrderStatus | undefined>()
  const [createOpen, setCreateOpen] = useState(false)
  const [selectedId, setSelectedId] = useState<number | null>(null)
  const [form] = Form.useForm()

  const { data, isLoading } = useListServiceOrdersQuery({ page, page_size: 20, keyword, status })
  const { data: contractsData } = useListContractsQuery({ page: 1, page_size: 200, status: 'active' })
  const [createServiceOrder, { isLoading: creating }] = useCreateServiceOrderMutation()
  const [updateStatus] = useUpdateServiceStatusMutation()

  const handleCreate = async (values: ServiceFormValues) => {
    const payload = {
      ...values,
      planned_start: values.planned_start ? dayjs(values.planned_start).format('YYYY-MM-DD') : undefined,
      planned_end: values.planned_end ? dayjs(values.planned_end).format('YYYY-MM-DD') : undefined,
    }
    try {
      await createServiceOrder(payload).unwrap()
      message.success('服务工单创建成功')
      setCreateOpen(false)
      form.resetFields()
    } catch (err: any) {
      message.error(err?.data?.detail || '创建失败')
    }
  }

  const columns = useMemo(() => [
    { title: '工单编号', dataIndex: 'order_no', key: 'order_no', render: (no: string, r: ServiceOrder) => (
      <Button type="link" onClick={() => setSelectedId(r.id)}>{no}</Button>
    )},
    { title: '服务类型', dataIndex: 'service_type', key: 'service_type', render: (s: string) => ServiceTypeLabels[s as keyof typeof ServiceTypeLabels] },
    { title: '客户', dataIndex: 'customer_name', key: 'customer_name' },
    { title: '负责人', dataIndex: 'assignee_name', key: 'assignee_name' },
    { title: '状态', dataIndex: 'status', key: 'status', render: (s: ServiceOrderStatus) => (
      <Tag color={statusColors[s]}>{ServiceOrderStatusLabels[s]}</Tag>
    )},
    { title: '计划开始', dataIndex: 'planned_start', key: 'planned_start' },
    { title: '计划结束', dataIndex: 'planned_end', key: 'planned_end' },
    { title: '操作', key: 'action', render: (_: any, r: ServiceOrder) => (
      <Space>
        {r.status === 'pending' && (
          <Button size="small" type="primary" onClick={() => updateStatus({ id: r.id, status: 'in_progress' })}>开始服务</Button>
        )}
        {r.status === 'in_progress' && (
          <Button size="small" onClick={() => updateStatus({ id: r.id, status: 'completed' })}>完成</Button>
        )}
      </Space>
    )},
  ], [updateStatus])

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 16 }}>
        <Space>
          <Input.Search placeholder="搜索工单编号" onSearch={setKeyword} style={{ width: 240 }} allowClear />
          <Select placeholder="工单状态" allowClear style={{ width: 120 }} onChange={setStatus}
            options={Object.entries(ServiceOrderStatusLabels).map(([v, l]) => ({ value: v, label: l }))} />
        </Space>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => setCreateOpen(true)}>新建工单</Button>
      </div>

      <Table rowKey="id" columns={columns} dataSource={data?.items} loading={isLoading}
        pagination={{ current: page, pageSize: 20, total: data?.total, onChange: setPage, showTotal: (t) => `共 ${t} 条` }} />

      <Drawer title="新建服务工单" open={createOpen} onClose={() => setCreateOpen(false)} width={480} footer={
        <Space style={{ float: 'right' }}>
          <Button onClick={() => setCreateOpen(false)}>取消</Button>
          <Button type="primary" loading={creating} onClick={() => form.submit()}>创建</Button>
        </Space>
      }>
        <Form form={form} layout="vertical" onFinish={handleCreate}>
          <Form.Item name="order_no" label="工单编号" rules={[{ required: true }]}><Input /></Form.Item>
          <Form.Item name="contract_id" label="关联合同" rules={[{ required: true }]}>
            <Select showSearch optionFilterProp="label"
              options={contractsData?.items.map(c => ({ value: c.id, label: `${c.contract_no} - ${c.title}` })) || []} />
          </Form.Item>
          <Form.Item name="service_type" label="服务类型" rules={[{ required: true }]}>
            <Select options={Object.entries(ServiceTypeLabels).map(([v, l]) => ({ value: v, label: l }))} />
          </Form.Item>
          <Form.Item name="title" label="工单标题" rules={[{ required: true }]}><Input /></Form.Item>
          <Form.Item name="planned_start" label="计划开始日期"><DatePicker style={{ width: '100%' }} /></Form.Item>
          <Form.Item name="planned_end" label="计划结束日期"><DatePicker style={{ width: '100%' }} /></Form.Item>
          <Form.Item name="remark" label="备注"><Input.TextArea rows={3} /></Form.Item>
        </Form>
      </Drawer>

      {selectedId && <ServiceDetail id={selectedId} onClose={() => setSelectedId(null)} />}
    </div>
  )
}

const ServiceDetail: React.FC<{ id: number; onClose: () => void }> = ({ id, onClose }) => {
  const { data } = useGetServiceOrderQuery(id)
  if (!data) return null
  return (
    <Drawer title="工单详情" open width={600} onClose={onClose}>
      <Descriptions column={2} bordered size="small">
        <Descriptions.Item label="工单编号">{data.order_no}</Descriptions.Item>
        <Descriptions.Item label="状态"><Tag color={statusColors[data.status]}>{ServiceOrderStatusLabels[data.status]}</Tag></Descriptions.Item>
        <Descriptions.Item label="工单标题" span={2}>{data.title}</Descriptions.Item>
        <Descriptions.Item label="服务类型">{ServiceTypeLabels[data.service_type as keyof typeof ServiceTypeLabels]}</Descriptions.Item>
        <Descriptions.Item label="负责人">{data.assignee_name}</Descriptions.Item>
        <Descriptions.Item label="计划开始">{data.planned_start}</Descriptions.Item>
        <Descriptions.Item label="计划结束">{data.planned_end}</Descriptions.Item>
        <Descriptions.Item label="实际开始">{data.actual_start}</Descriptions.Item>
        <Descriptions.Item label="实际结束">{data.actual_end}</Descriptions.Item>
        <Descriptions.Item label="备注" span={2}>{data.remark}</Descriptions.Item>
      </Descriptions>
    </Drawer>
  )
}

export default Services

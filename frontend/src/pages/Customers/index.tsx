import React, { useState, useMemo } from 'react'
import { Table, Button, Input, Select, Tag, Space, Popconfirm, message, Drawer, Form, Descriptions } from 'antd'
import { PlusOutlined } from '@ant-design/icons'
import { useListCustomersQuery, useCreateCustomerMutation, useDeleteCustomerMutation, useGetCustomerQuery } from '@/store/api/customersApi'
import { CustomerStatusLabels } from '@/utils/constants'
import type { CustomerListItem, CustomerStatus } from '@/types'

interface CustomerFormValues {
  name: string
  credit_code?: string
  industry?: string
  scale?: string
  address?: string
  status?: CustomerStatus
  remark?: string
}

const statusColors: Record<CustomerStatus, string> = {
  prospect: 'blue',
  signed: 'green',
  churned: 'red',
}

const Customers: React.FC = () => {
  const [page, setPage] = useState(1)
  const [keyword, setKeyword] = useState('')
  const [status, setStatus] = useState<CustomerStatus | undefined>()
  const [createOpen, setCreateOpen] = useState(false)
  const [selectedId, setSelectedId] = useState<number | null>(null)
  const [form] = Form.useForm()

  const { data, isLoading } = useListCustomersQuery({ page, page_size: 20, keyword, status })
  const [createCustomer, { isLoading: creating }] = useCreateCustomerMutation()
  const [deleteCustomer] = useDeleteCustomerMutation()

  const handleCreate = async (values: CustomerFormValues) => {
    try {
      await createCustomer(values).unwrap()
      message.success('客户创建成功')
      setCreateOpen(false)
      form.resetFields()
    } catch (err: any) {
      message.error(err?.data?.detail || '创建失败')
    }
  }

  const columns = useMemo(() => [
    { title: '公司名称', dataIndex: 'name', key: 'name', render: (name: string, r: CustomerListItem) => (
      <Button type="link" onClick={() => setSelectedId(r.id)}>{name}</Button>
    )},
    { title: '行业', dataIndex: 'industry', key: 'industry' },
    { title: '统一社会信用代码', dataIndex: 'credit_code', key: 'credit_code' },
    { title: '状态', dataIndex: 'status', key: 'status', render: (s: CustomerStatus) => (
      <Tag color={statusColors[s]}>{CustomerStatusLabels[s]}</Tag>
    )},
    { title: '创建时间', dataIndex: 'created_at', key: 'created_at', render: (d: string) => d?.slice(0, 10) },
    { title: '操作', key: 'action', render: (_: any, r: CustomerListItem) => (
      <Popconfirm title="确认删除该客户？" onConfirm={() => deleteCustomer(r.id)}>
        <Button type="link" danger size="small">删除</Button>
      </Popconfirm>
    )},
  ], [])

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 16 }}>
        <Space>
          <Input.Search placeholder="搜索公司名称" onSearch={setKeyword} style={{ width: 240 }} allowClear />
          <Select
            placeholder="客户状态"
            allowClear
            style={{ width: 120 }}
            onChange={setStatus}
            options={Object.entries(CustomerStatusLabels).map(([v, l]) => ({ value: v, label: l }))}
          />
        </Space>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => setCreateOpen(true)}>新建客户</Button>
      </div>

      <Table
        rowKey="id"
        columns={columns}
        dataSource={data?.items}
        loading={isLoading}
        pagination={{ current: page, pageSize: 20, total: data?.total, onChange: setPage, showTotal: (t) => `共 ${t} 条` }}
      />

      {/* 新建客户 Drawer */}
      <Drawer title="新建客户" open={createOpen} onClose={() => setCreateOpen(false)} width={480} footer={
        <Space style={{ float: 'right' }}>
          <Button onClick={() => setCreateOpen(false)}>取消</Button>
          <Button type="primary" loading={creating} onClick={() => form.submit()}>创建</Button>
        </Space>
      }>
        <Form form={form} layout="vertical" onFinish={handleCreate}>
          <Form.Item name="name" label="公司名称" rules={[{ required: true }]}><Input /></Form.Item>
          <Form.Item name="credit_code" label="统一社会信用代码"><Input /></Form.Item>
          <Form.Item name="industry" label="行业"><Input /></Form.Item>
          <Form.Item name="scale" label="企业规模">
            <Select options={[
              { value: '小型', label: '小型' },
              { value: '中型', label: '中型' },
              { value: '大型', label: '大型' },
            ]} />
          </Form.Item>
          <Form.Item name="address" label="地址"><Input /></Form.Item>
          <Form.Item name="status" label="状态" initialValue="prospect">
            <Select options={Object.entries(CustomerStatusLabels).map(([v, l]) => ({ value: v, label: l }))} />
          </Form.Item>
          <Form.Item name="remark" label="备注"><Input.TextArea rows={3} /></Form.Item>
        </Form>
      </Drawer>

      {/* 客户详情 Drawer */}
      {selectedId && (
        <CustomerDetail id={selectedId} onClose={() => setSelectedId(null)} />
      )}
    </div>
  )
}

const CustomerDetail: React.FC<{ id: number; onClose: () => void }> = ({ id, onClose }) => {
  const { data } = useGetCustomerQuery(id)
  return (
    <Drawer title="客户详情" open width={600} onClose={onClose}>
      {data && (
        <Descriptions column={2} bordered size="small">
          <Descriptions.Item label="公司名称" span={2}>{data.name}</Descriptions.Item>
          <Descriptions.Item label="统一社会信用代码">{data.credit_code}</Descriptions.Item>
          <Descriptions.Item label="行业">{data.industry}</Descriptions.Item>
          <Descriptions.Item label="规模">{data.scale}</Descriptions.Item>
          <Descriptions.Item label="状态"><Tag color={statusColors[data.status]}>{CustomerStatusLabels[data.status]}</Tag></Descriptions.Item>
          <Descriptions.Item label="地址" span={2}>{data.address}</Descriptions.Item>
          <Descriptions.Item label="网站" span={2}>{data.website}</Descriptions.Item>
          <Descriptions.Item label="备注" span={2}>{data.remark}</Descriptions.Item>
        </Descriptions>
      )}
    </Drawer>
  )
}

export default Customers

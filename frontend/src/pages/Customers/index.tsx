import React, { useState, useMemo } from 'react'
import { Table, Button, Input, Select, Tag, Space, Popconfirm, message, Drawer, Form, Descriptions, Cascader } from 'antd'
import { PlusOutlined } from '@ant-design/icons'
import { useListCustomersQuery, useCreateCustomerMutation, useDeleteCustomerMutation, useGetCustomerQuery } from '@/store/api/customersApi'
import { CustomerStatusLabels, formatDate } from '@/utils/constants'
import { hangzhouRegionOptions, getFullAddress } from '@/utils/hangzhouRegions'
import type { CustomerListItem, CustomerStatus } from '@/types'

interface CustomerFormValues {
  name: string
  credit_code?: string
  industry?: string
  scale?: string
  region?: string[]
  province?: string
  city?: string
  district?: string
  street?: string
  address?: string
  contact_name?: string
  contact_phone?: string
  status?: CustomerStatus
  remark?: string
}

const statusColors: Record<CustomerStatus, string> = {
  prospect: 'blue',
  signed: 'green',
  churned: 'red',
}

const industryOptions = [
  { value: '制造业', label: '制造业' },
  { value: '建筑业', label: '建筑业' },
  { value: '批发和零售业', label: '批发和零售业' },
  { value: '交通运输、仓储和邮政业', label: '交通运输、仓储和邮政业' },
  { value: '住宿和餐饮业', label: '住宿和餐饮业' },
  { value: '信息传输、软件和信息技术服务业', label: '信息传输、软件和信息技术服务业' },
  { value: '金融业', label: '金融业' },
  { value: '房地产业', label: '房地产业' },
  { value: '租赁和商务服务业', label: '租赁和商务服务业' },
  { value: '科学研究和技术服务业', label: '科学研究和技术服务业' },
  { value: '水利、环境和公共设施管理业', label: '水利、环境和公共设施管理业' },
  { value: '居民服务、修理和其他服务业', label: '居民服务、修理和其他服务业' },
  { value: '教育', label: '教育' },
  { value: '卫生和社会工作', label: '卫生和社会工作' },
  { value: '文化、体育和娱乐业', label: '文化、体育和娱乐业' },
  { value: '公共管理、社会保障和社会组织', label: '公共管理、社会保障和社会组织' },
  { value: '采矿业', label: '采矿业' },
  { value: '电力、热力、燃气及水生产和供应业', label: '电力、热力、燃气及水生产和供应业' },
  { value: '农、林、牧、渔业', label: '农、林、牧、渔业' },
]

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
    const payload = {
      ...values,
      province: values.region?.[0],
      city: values.region?.[1],
      district: values.region?.[2],
      street: values.region?.[3],
    }
    delete (payload as any).region
    try {
      await createCustomer(payload).unwrap()
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
    { title: '创建时间', dataIndex: 'created_at', key: 'created_at', render: (d: string) => formatDate(d) },
    { title: '操作', key: 'action', render: (_: any, r: CustomerListItem) => (
      <Popconfirm title="确认删除该客户？" onConfirm={() => deleteCustomer(r.id)}>
        <Button type="link" danger size="small">删除</Button>
      </Popconfirm>
    )},
  ], [deleteCustomer])

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
      <Drawer title="新建客户" open={createOpen} onClose={() => setCreateOpen(false)} width={520} footer={
        <Space style={{ float: 'right' }}>
          <Button onClick={() => setCreateOpen(false)}>取消</Button>
          <Button type="primary" loading={creating} onClick={() => form.submit()}>创建</Button>
        </Space>
      }>
        <Form form={form} layout="vertical" onFinish={handleCreate}>
          <Form.Item name="name" label="公司名称" rules={[{ required: true }]}><Input /></Form.Item>
          <Form.Item name="credit_code" label="统一社会信用代码"><Input /></Form.Item>
          <Form.Item name="industry" label="行业">
            <Select options={industryOptions} allowClear showSearch placeholder="请选择行业" />
          </Form.Item>
          <Form.Item name="scale" label="企业规模">
            <Select options={[
              { value: '微型', label: '微型' },
              { value: '小型', label: '小型' },
              { value: '中型', label: '中型' },
              { value: '大型', label: '大型' },
            ]} allowClear placeholder="请选择企业规模" />
          </Form.Item>
          <Form.Item name="region" label="属地">
            <Cascader
              options={hangzhouRegionOptions}
              placeholder="请选择属地"
              changeOnSelect={false}
              onChange={(value) => {
                if (Array.isArray(value) && value.length === 4) {
                  form.setFieldsValue({ address: getFullAddress(value as string[]) })
                }
              }}
              style={{ width: '100%' }}
            />
          </Form.Item>
          <Form.Item name="address" label="地址"><Input placeholder="选择属地后自动填充，可手动修改" /></Form.Item>
          <Form.Item name="contact_name" label="联系人"><Input /></Form.Item>
          <Form.Item name="contact_phone" label="联系方式"><Input /></Form.Item>
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
          <Descriptions.Item label="属地" span={2}>{[data.province, data.city, data.district, data.street].filter(Boolean).join('')}</Descriptions.Item>
          <Descriptions.Item label="地址" span={2}>{data.address}</Descriptions.Item>
          <Descriptions.Item label="联系人">{data.contact_name}</Descriptions.Item>
          <Descriptions.Item label="联系方式">{data.contact_phone}</Descriptions.Item>
          <Descriptions.Item label="网站" span={2}>{data.website}</Descriptions.Item>
          <Descriptions.Item label="备注" span={2}>{data.remark}</Descriptions.Item>
        </Descriptions>
      )}
    </Drawer>
  )
}

export default Customers

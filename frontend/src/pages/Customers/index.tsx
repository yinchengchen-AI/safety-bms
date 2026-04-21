import React, { useState, useMemo } from 'react'
import {
  Table, Button, Input, Select, Tag, Space, Popconfirm, message, Drawer, Form, Descriptions,
  Cascader, Modal, List, Timeline, Switch, DatePicker, Divider, Empty, Tabs,
} from 'antd'
import { PlusOutlined, EditOutlined, DeleteOutlined, UploadOutlined } from '@ant-design/icons'
import {
  useListCustomersQuery, useCreateCustomerMutation, useDeleteCustomerMutation,
  useGetCustomerQuery, useUpdateCustomerMutation, useAddContactMutation,
  useAddFollowUpMutation, useListFollowUpsQuery, useImportCustomersMutation,
} from '@/store/api/customersApi'
import { useListContractsQuery } from '@/store/api/contractsApi'
import { useListServiceOrdersQuery } from '@/store/api/servicesApi'
import { useListInvoicesQuery } from '@/store/api/invoicesApi'
import { useListPaymentsQuery } from '@/store/api/paymentsApi'
import { CustomerStatusLabels, formatDate, formatDateTime, ContractStatusLabels, ServiceOrderStatusLabels, InvoiceStatusLabels, InvoiceTypeLabels, PaymentMethodLabels, formatAmount } from '@/utils/constants'
import { hangzhouRegionOptions, getFullAddress } from '@/utils/hangzhouRegions'
import type { CustomerListItem, CustomerStatus } from '@/types'
import dayjs from 'dayjs'
import type { Dayjs } from 'dayjs'

interface CustomerFormValues {
  name: string
  credit_code?: string
  industry?: string
  scale?: string
  region?: string[]
  address?: string
  contact_name?: string
  contact_phone?: string
  status?: CustomerStatus
  remark?: string
}

interface ContactFormValues {
  name: string
  position?: string
  phone?: string
  email?: string
  is_primary?: boolean
}

interface FollowUpFormValues {
  content: string
  follow_up_at: Dayjs
  next_follow_up_at?: Dayjs
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
  const [editOpen, setEditOpen] = useState(false)
  const [editingId, setEditingId] = useState<number | null>(null)
  const [selectedId, setSelectedId] = useState<number | null>(null)
  const [form] = Form.useForm()
  const [editForm] = Form.useForm()

  const { data, isLoading } = useListCustomersQuery({ page, page_size: 20, keyword, status })
  const [createCustomer, { isLoading: creating }] = useCreateCustomerMutation()
  const [updateCustomer, { isLoading: updating }] = useUpdateCustomerMutation()
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

  const handleEditOpen = React.useCallback((record: CustomerListItem) => {
    setEditingId(record.id)
    const region = [record.province, record.city, record.district, record.street].filter(Boolean) as string[]
    editForm.setFieldsValue({
      name: record.name,
      credit_code: record.credit_code,
      industry: record.industry,
      scale: record.scale,
      region: region.length > 0 ? region : undefined,
      address: record.address,
      contact_name: record.contact_name,
      contact_phone: record.contact_phone,
      status: record.status,
      remark: record.remark,
    })
    setEditOpen(true)
  }, [editForm])

  const handleEdit = async (values: CustomerFormValues) => {
    if (!editingId) return
    const payload = {
      ...values,
      province: values.region?.[0],
      city: values.region?.[1],
      district: values.region?.[2],
      street: values.region?.[3],
    }
    delete (payload as any).region
    try {
      await updateCustomer({ id: editingId, data: payload }).unwrap()
      message.success('客户更新成功')
      setEditOpen(false)
      setEditingId(null)
      editForm.resetFields()
    } catch (err: any) {
      message.error(err?.data?.detail || '更新失败')
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
      <Space>
        <Button type="link" size="small" icon={<EditOutlined />} onClick={() => handleEditOpen(r)}>编辑</Button>
        <Popconfirm title="确认删除该客户？" onConfirm={() => deleteCustomer(r.id)}>
          <Button type="link" danger size="small" icon={<DeleteOutlined />}>删除</Button>
        </Popconfirm>
      </Space>
    )},
  ], [deleteCustomer, handleEditOpen])

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
      <Drawer title="新建客户" open={createOpen} onClose={() => setCreateOpen(false)} width={640} footer={
        <Space style={{ float: 'right' }}>
          <Button onClick={() => setCreateOpen(false)}>取消</Button>
          <Button type="primary" loading={creating} onClick={() => form.submit()}>创建</Button>
        </Space>
      }>
        <CustomerForm form={form} onFinish={handleCreate} />
      </Drawer>

      {/* 编辑客户 Drawer */}
      <Drawer title="编辑客户" open={editOpen} onClose={() => { setEditOpen(false); setEditingId(null) }} width={640} footer={
        <Space style={{ float: 'right' }}>
          <Button onClick={() => { setEditOpen(false); setEditingId(null) }}>取消</Button>
          <Button type="primary" loading={updating} onClick={() => editForm.submit()}>保存</Button>
        </Space>
      }>
        <CustomerForm form={editForm} onFinish={handleEdit} />
      </Drawer>

      {/* 客户详情 Drawer */}
      {selectedId && (
        <CustomerDetail id={selectedId} onClose={() => setSelectedId(null)} />
      )}
    </div>
  )
}

const CustomerForm: React.FC<{ form: any; onFinish: (values: CustomerFormValues) => void }> = ({ form, onFinish }) => {
  return (
    <Form form={form} layout="vertical" onFinish={onFinish}>
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
  )
}

const CustomerDetail: React.FC<{ id: number; onClose: () => void }> = ({ id, onClose }) => {
  const { data, isLoading } = useGetCustomerQuery(id)
  const { data: followUps, isLoading: followUpsLoading } = useListFollowUpsQuery(id)
  const [addContact, { isLoading: addingContact }] = useAddContactMutation()
  const [addFollowUp, { isLoading: addingFollowUp }] = useAddFollowUpMutation()

  const [contactModalOpen, setContactModalOpen] = useState(false)
  const [followUpModalOpen, setFollowUpModalOpen] = useState(false)
  const [contactForm] = Form.useForm()
  const [followUpForm] = Form.useForm()

  const handleAddContact = async (values: ContactFormValues) => {
    const payload = {
      ...values,
      is_primary: values.is_primary ?? false,
    }
    try {
      await addContact({ customerId: id, data: payload }).unwrap()
      message.success('联系人添加成功')
      setContactModalOpen(false)
      contactForm.resetFields()
    } catch (err: any) {
      message.error(err?.data?.detail || '添加失败')
    }
  }

  const handleAddFollowUp = async (values: FollowUpFormValues) => {
    const payload = {
      content: values.content,
      follow_up_at: values.follow_up_at.format('YYYY-MM-DD HH:mm:ss'),
      next_follow_up_at: values.next_follow_up_at ? values.next_follow_up_at.format('YYYY-MM-DD HH:mm:ss') : undefined,
    }
    try {
      await addFollowUp({ customerId: id, data: payload }).unwrap()
      message.success('跟进记录添加成功')
      setFollowUpModalOpen(false)
      followUpForm.resetFields()
    } catch (err: any) {
      message.error(err?.data?.detail || '添加失败')
    }
  }

  // 关联数据查询
  const { data: contractsData, isLoading: contractsLoading } = useListContractsQuery({ customer_id: id, page_size: 10 })
  const { data: servicesData, isLoading: servicesLoading } = useListServiceOrdersQuery({ customer_id: id, page_size: 10 })
  const { data: invoicesData, isLoading: invoicesLoading } = useListInvoicesQuery({ customer_id: id, page_size: 10 })
  const { data: paymentsData, isLoading: paymentsLoading } = useListPaymentsQuery({ customer_id: id, page_size: 10 })

  const contractColumns = useMemo(() => [
    { title: '合同编号', dataIndex: 'contract_no', key: 'contract_no' },
    { title: '标题', dataIndex: 'title', key: 'title' },
    { title: '金额', dataIndex: 'total_amount', key: 'total_amount', render: (v: number) => formatAmount(v) },
    { title: '状态', dataIndex: 'status', key: 'status', render: (s: string) => <Tag>{ContractStatusLabels[s] || s}</Tag> },
    { title: '签订日期', dataIndex: 'sign_date', key: 'sign_date', render: (d: string) => formatDate(d) },
  ], [])

  const serviceColumns = useMemo(() => [
    { title: '工单编号', dataIndex: 'order_no', key: 'order_no' },
    { title: '标题', dataIndex: 'title', key: 'title' },
    { title: '服务类型', dataIndex: 'service_type_name', key: 'service_type_name' },
    { title: '负责人', dataIndex: 'assignee_name', key: 'assignee_name' },
    { title: '状态', dataIndex: 'status', key: 'status', render: (s: string) => <Tag>{ServiceOrderStatusLabels[s] || s}</Tag> },
    { title: '计划开始', dataIndex: 'planned_start', key: 'planned_start', render: (d: string) => formatDate(d) },
  ], [])

  const invoiceColumns = useMemo(() => [
    { title: '发票编号', dataIndex: 'invoice_no', key: 'invoice_no' },
    { title: '类型', dataIndex: 'invoice_type', key: 'invoice_type', render: (t: string) => InvoiceTypeLabels[t] || t },
    { title: '金额', dataIndex: 'amount', key: 'amount', render: (v: number) => formatAmount(v) },
    { title: '状态', dataIndex: 'status', key: 'status', render: (s: string) => <Tag>{InvoiceStatusLabels[s] || s}</Tag> },
    { title: '开票日期', dataIndex: 'invoice_date', key: 'invoice_date', render: (d: string) => formatDate(d) },
  ], [])

  const paymentColumns = useMemo(() => [
    { title: '收款编号', dataIndex: 'payment_no', key: 'payment_no' },
    { title: '金额', dataIndex: 'amount', key: 'amount', render: (v: number) => formatAmount(v) },
    { title: '方式', dataIndex: 'payment_method', key: 'payment_method', render: (m: string) => PaymentMethodLabels[m] || m },
    { title: '收款日期', dataIndex: 'payment_date', key: 'payment_date', render: (d: string) => formatDate(d) },
  ], [])

  const detailTabItems = useMemo(() => [
    {
      key: 'contacts',
      label: '联系人',
      children: (
        <div>
          <div style={{ marginBottom: 12 }}>
            <Button type="dashed" icon={<PlusOutlined />} size="small" onClick={() => setContactModalOpen(true)}>
              添加联系人
            </Button>
          </div>
          {data?.contacts && data.contacts.length > 0 ? (
            <List
              size="small"
              bordered
              dataSource={data.contacts}
              renderItem={(item) => (
                <List.Item>
                  <Space>
                    <span style={{ fontWeight: 700 }}>{item.name}</span>
                    {item.is_primary && <Tag color="blue">主联系人</Tag>}
                    {item.position && <span style={{ color: '#666' }}>{item.position}</span>}
                    {item.phone && <span>电话：{item.phone}</span>}
                    {item.email && <span>邮箱：{item.email}</span>}
                  </Space>
                </List.Item>
              )}
            />
          ) : (
            <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="暂无联系人" />
          )}
        </div>
      ),
    },
    {
      key: 'followUps',
      label: '跟进记录',
      children: (
        <div>
          <div style={{ marginBottom: 12 }}>
            <Button type="dashed" icon={<PlusOutlined />} size="small" onClick={() => setFollowUpModalOpen(true)}>
              添加跟进记录
            </Button>
          </div>
          {followUpsLoading ? (
            <div style={{ textAlign: 'center', padding: 24 }}>加载中...</div>
          ) : followUps && followUps.length > 0 ? (
            <Timeline
              items={followUps.map((f) => ({
                children: (
                  <div>
                    <div style={{ fontWeight: 500 }}>{formatDateTime(f.follow_up_at)}</div>
                    <div style={{ marginTop: 4 }}>{f.content}</div>
                    {f.next_follow_up_at && (
                      <div style={{ color: '#999', fontSize: 12, marginTop: 4 }}>
                        下次跟进：{formatDateTime(f.next_follow_up_at)}
                      </div>
                    )}
                  </div>
                ),
              }))}
            />
          ) : (
            <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="暂无跟进记录" />
          )}
        </div>
      ),
    },
    {
      key: 'contracts',
      label: `合同 (${contractsData?.total ?? 0})`,
      children: (
        <Table
          rowKey="id"
          columns={contractColumns}
          dataSource={contractsData?.items}
          loading={contractsLoading}
          pagination={false}
          size="small"
          locale={{ emptyText: '暂无合同' }}
        />
      ),
    },
    {
      key: 'services',
      label: `服务工单 (${servicesData?.total ?? 0})`,
      children: (
        <Table
          rowKey="id"
          columns={serviceColumns}
          dataSource={servicesData?.items}
          loading={servicesLoading}
          pagination={false}
          size="small"
          locale={{ emptyText: '暂无服务工单' }}
        />
      ),
    },
    {
      key: 'invoices',
      label: `发票 (${invoicesData?.total ?? 0})`,
      children: (
        <Table
          rowKey="id"
          columns={invoiceColumns}
          dataSource={invoicesData?.items}
          loading={invoicesLoading}
          pagination={false}
          size="small"
          locale={{ emptyText: '暂无发票' }}
        />
      ),
    },
    {
      key: 'payments',
      label: `收款 (${paymentsData?.total ?? 0})`,
      children: (
        <Table
          rowKey="id"
          columns={paymentColumns}
          dataSource={paymentsData?.items}
          loading={paymentsLoading}
          pagination={false}
          size="small"
          locale={{ emptyText: '暂无收款' }}
        />
      ),
    },
  ], [data, followUps, followUpsLoading, contractsData, contractsLoading, servicesData, servicesLoading, invoicesData, invoicesLoading, paymentsData, paymentsLoading, contractColumns, serviceColumns, invoiceColumns, paymentColumns])

  return (
    <Drawer title="客户详情" open width={800} onClose={onClose} loading={isLoading}>
      {data && (
        <div>
          {/* 基本信息 */}
          <Descriptions column={2} bordered size="small">
            <Descriptions.Item label="公司名称" span={2}>{data.name}</Descriptions.Item>
            <Descriptions.Item label="统一社会信用代码">{data.credit_code}</Descriptions.Item>
            <Descriptions.Item label="行业">{data.industry}</Descriptions.Item>
            <Descriptions.Item label="规模">{data.scale}</Descriptions.Item>
            <Descriptions.Item label="状态"><Tag color={statusColors[data.status]}>{CustomerStatusLabels[data.status]}</Tag></Descriptions.Item>
            <Descriptions.Item label="网站" span={2}>{data.website}</Descriptions.Item>
            <Descriptions.Item label="属地" span={2}>{[data.province, data.city, data.district, data.street].filter(Boolean).join('')}</Descriptions.Item>
            <Descriptions.Item label="地址" span={2}>{data.address}</Descriptions.Item>
            <Descriptions.Item label="联系人">{data.contact_name}</Descriptions.Item>
            <Descriptions.Item label="联系方式">{data.contact_phone}</Descriptions.Item>
            <Descriptions.Item label="备注" span={2}>{data.remark}</Descriptions.Item>
          </Descriptions>

          <Tabs items={detailTabItems} style={{ marginTop: 16 }} />
        </div>
      )}

      {/* 添加联系人 Modal */}
      <Modal
        title="添加联系人"
        open={contactModalOpen}
        onCancel={() => { setContactModalOpen(false); contactForm.resetFields() }}
        onOk={() => contactForm.submit()}
        confirmLoading={addingContact}
      >
        <Form form={contactForm} layout="vertical" onFinish={handleAddContact}>
          <Form.Item name="name" label="姓名" rules={[{ required: true }]}><Input /></Form.Item>
          <Form.Item name="position" label="职位"><Input /></Form.Item>
          <Form.Item name="phone" label="电话"><Input /></Form.Item>
          <Form.Item name="email" label="邮箱"><Input /></Form.Item>
          <Form.Item name="is_primary" label="主联系人" valuePropName="checked">
            <Switch checkedChildren="是" unCheckedChildren="否" />
          </Form.Item>
        </Form>
      </Modal>

      {/* 添加跟进记录 Modal */}
      <Modal
        title="添加跟进记录"
        open={followUpModalOpen}
        onCancel={() => { setFollowUpModalOpen(false); followUpForm.resetFields() }}
        onOk={() => followUpForm.submit()}
        confirmLoading={addingFollowUp}
      >
        <Form form={followUpForm} layout="vertical" onFinish={handleAddFollowUp}>
          <Form.Item name="content" label="跟进内容" rules={[{ required: true }]}>
            <Input.TextArea rows={3} placeholder="请输入跟进内容" />
          </Form.Item>
          <Form.Item name="follow_up_at" label="跟进时间" rules={[{ required: true }]} initialValue={dayjs()}>
            <DatePicker showTime style={{ width: '100%' }} placeholder="请选择跟进时间" />
          </Form.Item>
          <Form.Item name="next_follow_up_at" label="下次跟进时间">
            <DatePicker showTime style={{ width: '100%' }} placeholder="请选择下次跟进时间" />
          </Form.Item>
        </Form>
      </Modal>
    </Drawer>
  )
}

export default Customers

import React, { useState, useMemo, useEffect } from 'react'
import { Table, Button, Input, Select, Space, Popconfirm, message, Drawer, Form, InputNumber, Alert, Tabs, DatePicker } from 'antd'
import { PlusOutlined, ExclamationCircleOutlined } from '@ant-design/icons'
import { PermissionButton } from '@/components/auth/PermissionButton'
import { useListPaymentsQuery, useCreatePaymentMutation, useUpdatePaymentMutation, useDeletePaymentMutation, useListOverdueContractsQuery, useGetContractReceivableQuery } from '@/store/api/paymentsApi'
import { useListContractsQuery } from '@/store/api/contractsApi'
import { PaymentMethodLabels, formatAmount, generateBizNo } from '@/utils/constants'
import { downloadExport } from '@/utils/export'
import type { Payment, PaymentMethod } from '@/types'
import dayjs from 'dayjs'

const Payments: React.FC = () => {
  const [page, setPage] = useState(1)
  const [activeTab, setActiveTab] = useState('list')
  const [createOpen, setCreateOpen] = useState(false)
  const [editOpen, setEditOpen] = useState(false)
  const [editingId, setEditingId] = useState<number | null>(null)
  const [contractId, setContractId] = useState<number | undefined>()
  const [form] = Form.useForm()
  const [editForm] = Form.useForm()

  useEffect(() => {
    if (createOpen) {
      form.setFieldsValue({ payment_no: generateBizNo('SK') })
    }
  }, [createOpen, form])

  const { data, isLoading } = useListPaymentsQuery({ page, page_size: 20 })
  const { data: overdueData } = useListOverdueContractsQuery()
  const { data: contractsData } = useListContractsQuery({ page: 1, page_size: 200, status: 'active' })
  const { data: receivableData } = useGetContractReceivableQuery(contractId ?? 0, { skip: !contractId })
  const [createPayment, { isLoading: creating }] = useCreatePaymentMutation()
  const [updatePayment, { isLoading: updating }] = useUpdatePaymentMutation()
  const [deletePayment] = useDeletePaymentMutation()

  const handleExport = async () => {
    try {
      await downloadExport('/api/v1/payments/export', `payments_${dayjs().format('YYYYMMDD_HHmmss')}.xlsx`)
    } catch (err: any) {
      message.error(err.message || '导出失败')
    }
  }

  const handleCreate = async (values: any) => {
    if (receivableData && values.amount > receivableData.receivable_amount) {
      message.error('收款金额不能超过合同应收余额')
      return
    }
    const payload = {
      ...values,
      contract_id: contractId,
      payment_date: values.payment_date ? dayjs(values.payment_date).format('YYYY-MM-DD') : undefined,
    }
    try {
      await createPayment(payload).unwrap()
      message.success('收款记录创建成功')
      setCreateOpen(false)
      form.resetFields()
      setContractId(undefined)
    } catch (err: any) {
      message.error(err?.data?.detail || '创建失败')
    }
  }

  const handleEdit = (record: Payment) => {
    setEditingId(record.id)
    setContractId(record.contract_id)
    editForm.setFieldsValue({
      amount: record.amount,
      payment_method: record.payment_method,
      payment_date: record.payment_date ? dayjs(record.payment_date) : undefined,
      bank_account: record.bank_account,
      transaction_ref: record.transaction_ref,
      remark: record.remark,
    })
    setEditOpen(true)
  }

  const handleUpdate = async (values: any) => {
    if (!editingId) return
    const payload = {
      ...values,
      contract_id: contractId,
      payment_date: values.payment_date ? dayjs(values.payment_date).format('YYYY-MM-DD') : undefined,
    }
    try {
      await updatePayment({ id: editingId, data: payload }).unwrap()
      message.success('收款记录更新成功')
      setEditOpen(false)
      editForm.resetFields()
      setEditingId(null)
      setContractId(undefined)
    } catch (err: any) {
      message.error(err?.data?.detail || '更新失败')
    }
  }

  const columns = useMemo(() => [
    { title: '客户', dataIndex: 'customer_name', key: 'customer_name' },
    { title: '合同编号', dataIndex: 'contract_no', key: 'contract_no' },
    { title: '收款金额', dataIndex: 'amount', key: 'amount', render: formatAmount },
    { title: '收款方式', dataIndex: 'payment_method', key: 'payment_method', render: (m: PaymentMethod) => PaymentMethodLabels[m] },
    { title: '收款日期', dataIndex: 'payment_date', key: 'payment_date' },
    { title: '备注', dataIndex: 'remark', key: 'remark', ellipsis: true },
    { title: '操作', key: 'action', render: (_: any, r: Payment) => (
      <Space>
        <PermissionButton permission="payment:update" type="link" size="small" onClick={() => handleEdit(r)}>编辑</PermissionButton>
        <Popconfirm title="确认删除？" onConfirm={() => deletePayment(r.id)}>
          <PermissionButton permission="payment:delete" type="link" danger size="small">删除</PermissionButton>
        </Popconfirm>
      </Space>
    )},
  ], [deletePayment, handleEdit])

  const overdueColumns = useMemo(() => [
    { title: '合同编号', dataIndex: 'contract_no', key: 'contract_no' },
    { title: '客户', dataIndex: 'customer_name', key: 'customer_name' },
    { title: '合同总额', dataIndex: 'total_amount', key: 'total_amount', render: formatAmount },
    { title: '已收款', dataIndex: 'received_amount', key: 'received_amount', render: formatAmount },
    { title: '应收余额', dataIndex: 'receivable_amount', key: 'receivable_amount', render: (v: number) => <span style={{ color: '#ff4d4f', fontWeight: 600 }}>{formatAmount(v)}</span> },
    { title: '到期日', dataIndex: 'end_date', key: 'end_date' },
  ], [])

  return (
    <div>
      <Tabs activeKey={activeTab} onChange={setActiveTab} tabBarExtraContent={
        <Space>
          <PermissionButton permission="payment:export" onClick={handleExport}>导出</PermissionButton>
          <PermissionButton permission="payment:create" type="primary" icon={<PlusOutlined />} onClick={() => setCreateOpen(true)}>新建收款</PermissionButton>
        </Space>
      } items={[
        {
          key: 'list', label: '收款记录',
          children: (
            <Table rowKey="id" columns={columns} dataSource={data?.items} loading={isLoading}
              pagination={{ current: page, pageSize: 20, total: data?.total, onChange: setPage, showTotal: (t) => `共 ${t} 条` }} />
          ),
        },
        {
          key: 'overdue', label: <><ExclamationCircleOutlined style={{ color: '#ff4d4f' }} /> 逾期应收 {overdueData?.length ? `(${overdueData.length})` : ''}</>,
          children: (
            <Table rowKey="id" columns={overdueColumns} dataSource={overdueData || []} />
          ),
        },
      ]} />

      <Drawer title="新建收款记录" open={createOpen} onClose={() => { setCreateOpen(false); setContractId(undefined) }} width={640} footer={
        <Space style={{ float: 'right' }}>
          <Button onClick={() => { setCreateOpen(false); setContractId(undefined) }}>取消</Button>
          <Button type="primary" loading={creating} onClick={() => form.submit()}>创建</Button>
        </Space>
      }>
        {receivableData && (
          <Alert
            style={{ marginBottom: 16 }}
            type={receivableData.receivable_amount > 0 ? 'warning' : 'success'}
            message={`应收余额: ${formatAmount(receivableData.receivable_amount)}`}
            description={`合同总额: ${formatAmount(receivableData.total_amount)}  已收: ${formatAmount(receivableData.received_amount)}`}
          />
        )}
        <Form form={form} layout="vertical" onFinish={handleCreate}>
          <Form.Item name="payment_no" label="收款编号" rules={[{ required: true }]}><Input disabled /></Form.Item>
          <Form.Item name="contract_id" label="关联合同" rules={[{ required: true }]}>
            <Select showSearch optionFilterProp="label" onChange={(v) => setContractId(v)}
              options={contractsData?.items.map(c => ({ value: c.id, label: `${c.contract_no} - ${c.title}` })) || []} />
          </Form.Item>
          <Form.Item name="amount" label="收款金额(元)" rules={[{ required: true }, { type: 'number', min: 0.01, message: '收款金额必须大于0' }]}>
            <InputNumber style={{ width: '100%' }} min={0.01} precision={2} />
          </Form.Item>
          <Form.Item name="payment_method" label="收款方式" rules={[{ required: true }]} initialValue="bank_transfer">
            <Select options={Object.entries(PaymentMethodLabels).map(([v, l]) => ({ value: v, label: l }))} />
          </Form.Item>
          <Form.Item name="payment_date" label="收款日期" rules={[{ required: true }]}><DatePicker style={{ width: '100%' }} /></Form.Item>
          <Form.Item name="bank_account" label="收款银行账号"><Input /></Form.Item>
          <Form.Item name="transaction_ref" label="交易流水号/支票号"><Input /></Form.Item>
          <Form.Item name="remark" label="备注"><Input.TextArea rows={3} /></Form.Item>
        </Form>
      </Drawer>

      <Drawer title="编辑收款记录" open={editOpen} onClose={() => { setEditOpen(false); setEditingId(null); setContractId(undefined) }} width={640} footer={
        <Space style={{ float: 'right' }}>
          <Button onClick={() => { setEditOpen(false); setEditingId(null); setContractId(undefined) }}>取消</Button>
          <Button type="primary" loading={updating} onClick={() => editForm.submit()}>保存</Button>
        </Space>
      }>
        {receivableData && (
          <Alert
            style={{ marginBottom: 16 }}
            type={receivableData.receivable_amount > 0 ? 'warning' : 'success'}
            message={`应收余额: ${formatAmount(receivableData.receivable_amount)}`}
            description={`合同总额: ${formatAmount(receivableData.total_amount)}  已收: ${formatAmount(receivableData.received_amount)}`}
          />
        )}
        <Form form={editForm} layout="vertical" onFinish={handleUpdate}>
          <Form.Item name="contract_id" label="关联合同" rules={[{ required: true }]}>
            <Select showSearch optionFilterProp="label" onChange={(v) => setContractId(v)}
              options={contractsData?.items.map(c => ({ value: c.id, label: `${c.contract_no} - ${c.title}` })) || []} />
          </Form.Item>
          <Form.Item name="amount" label="收款金额(元)" rules={[{ required: true }, { type: 'number', min: 0.01, message: '收款金额必须大于0' }]}>
            <InputNumber style={{ width: '100%' }} min={0.01} precision={2} />
          </Form.Item>
          <Form.Item name="payment_method" label="收款方式" rules={[{ required: true }]}>
            <Select options={Object.entries(PaymentMethodLabels).map(([v, l]) => ({ value: v, label: l }))} />
          </Form.Item>
          <Form.Item name="payment_date" label="收款日期" rules={[{ required: true }]}><DatePicker style={{ width: '100%' }} /></Form.Item>
          <Form.Item name="bank_account" label="收款银行账号"><Input /></Form.Item>
          <Form.Item name="transaction_ref" label="交易流水号/支票号"><Input /></Form.Item>
          <Form.Item name="remark" label="备注"><Input.TextArea rows={3} /></Form.Item>
        </Form>
      </Drawer>
    </div>
  )
}

export default Payments

import React, { useState, useEffect } from 'react'
import { Table, Button, Input, Select, Tag, Space, Popconfirm, message, Drawer, Form, InputNumber, Alert, DatePicker } from 'antd'
import { PlusOutlined } from '@ant-design/icons'
import { PermissionButton } from '@/components/auth/PermissionButton'
import { useListInvoicesQuery, useCreateInvoiceMutation, useUpdateInvoiceMutation, useDeleteInvoiceMutation } from '@/store/api/invoicesApi'
import { useListContractsQuery } from '@/store/api/contractsApi'
import { InvoiceStatusLabels, InvoiceTypeLabels, formatAmount, generateBizNo } from '@/utils/constants'
import { downloadExport } from '@/utils/export'
import type { Invoice, InvoiceStatus } from '@/types'
import dayjs from 'dayjs'

const statusColors: Record<InvoiceStatus, string> = {
  applying: 'default', issued: 'success', sent: 'processing',
}

const Invoices: React.FC = () => {
  const [page, setPage] = useState(1)
  const [keyword, setKeyword] = useState('')
  const [status, setStatus] = useState<InvoiceStatus | undefined>()
  const [createOpen, setCreateOpen] = useState(false)
  const [editOpen, setEditOpen] = useState(false)
  const [editingId, setEditingId] = useState<number | null>(null)
  const [contractId, setContractId] = useState<number | undefined>()
  const [form] = Form.useForm()
  const [editForm] = Form.useForm()

  useEffect(() => {
    if (createOpen) {
      form.setFieldsValue({ invoice_no: generateBizNo('FP') })
    }
  }, [createOpen, form])

  const { data, isLoading } = useListInvoicesQuery({ page, page_size: 20, keyword, status })
  const { data: contractsData } = useListContractsQuery({ page: 1, page_size: 200, status: 'active' })
  const [createInvoice, { isLoading: creating, error: createError }] = useCreateInvoiceMutation()
  const [updateInvoice, { isLoading: updating }] = useUpdateInvoiceMutation()
  const [deleteInvoice] = useDeleteInvoiceMutation()

  const selectedContract = contractsData?.items.find(c => c.id === contractId)

  const handleCreate = async (values: any) => {
    if (selectedContract) {
      const available = selectedContract.total_amount - (selectedContract.invoiced_amount || 0)
      if (values.amount > available) {
        message.error('开票金额不能超过合同可开票余额')
        return
      }
    }
    const payload = {
      ...values,
      contract_id: contractId,
      invoice_date: values.invoice_date ? dayjs(values.invoice_date).format('YYYY-MM-DD') : undefined,
    }
    try {
      await createInvoice(payload).unwrap()
      message.success('开票申请提交成功')
      setCreateOpen(false)
      form.resetFields()
      setContractId(undefined)
    } catch (err: any) {
      message.error(err?.data?.detail || '创建失败')
    }
  }

  const handleEdit = (record: Invoice) => {
    setEditingId(record.id)
    setContractId(record.contract_id)
    editForm.setFieldsValue({
      contract_id: record.contract_id,
      invoice_no: record.invoice_no,
      invoice_type: record.invoice_type,
      amount: record.amount,
      tax_rate: record.tax_rate,
      invoice_date: record.invoice_date ? dayjs(record.invoice_date) : undefined,
      remark: record.remark,
    })
    setEditOpen(true)
  }

  const handleUpdate = async (values: any) => {
    if (!editingId) return
    const payload = {
      ...values,
      contract_id: contractId,
      invoice_date: values.invoice_date ? dayjs(values.invoice_date).format('YYYY-MM-DD') : undefined,
    }
    try {
      await updateInvoice({ id: editingId, data: payload }).unwrap()
      message.success('发票更新成功')
      setEditOpen(false)
      editForm.resetFields()
      setEditingId(null)
      setContractId(undefined)
    } catch (err: any) {
      message.error(err?.data?.detail || '更新失败')
    }
  }

  const handleExport = async () => {
    const params = new URLSearchParams()
    if (keyword) params.append('keyword', keyword)
    if (status) params.append('status', status)
    if (contractId) params.append('contract_id', String(contractId))
    try {
      await downloadExport(`/api/v1/invoices/export?${params.toString()}`, `invoices_${dayjs().format('YYYYMMDD_HHmmss')}.xlsx`)
    } catch (err: any) {
      message.error(err.message || '导出失败')
    }
  }

  const columns = [
    { title: '发票编号', dataIndex: 'invoice_no', key: 'invoice_no' },
    { title: '客户', dataIndex: 'customer_name', key: 'customer_name' },
    { title: '发票类型', dataIndex: 'invoice_type', key: 'invoice_type', render: (t: string) => InvoiceTypeLabels[t as keyof typeof InvoiceTypeLabels] },
    { title: '金额', dataIndex: 'amount', key: 'amount', render: formatAmount },
    { title: '税率', dataIndex: 'tax_rate', key: 'tax_rate', render: (r?: number | string) => r !== undefined && r !== null ? `${(Number(r) * 100).toFixed(0)}%` : '-' },
    { title: '状态', dataIndex: 'status', key: 'status', render: (s: InvoiceStatus) => (
      <Tag color={statusColors[s]}>{InvoiceStatusLabels[s]}</Tag>
    )},
    { title: '开票日期', dataIndex: 'invoice_date', key: 'invoice_date' },
    { title: '操作', key: 'action', render: (_: any, r: Invoice) => (
      <Space>
        <PermissionButton permission="invoice:update" type="link" size="small" onClick={() => handleEdit(r)}>编辑</PermissionButton>
        <Popconfirm title="确认删除？" onConfirm={() => deleteInvoice(r.id)}>
          <PermissionButton permission="invoice:delete" type="link" danger size="small">删除</PermissionButton>
        </Popconfirm>
      </Space>
    )},
  ]

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 16 }}>
        <Space>
          <Input.Search placeholder="搜索发票编号" onSearch={setKeyword} style={{ width: 240 }} allowClear />
          <Select placeholder="发票状态" allowClear style={{ width: 120 }} onChange={setStatus}
            options={Object.entries(InvoiceStatusLabels).map(([v, l]) => ({ value: v, label: l }))} />
        </Space>
        <Space>
          <PermissionButton permission="invoice:export" onClick={handleExport}>导出</PermissionButton>
          <PermissionButton permission="invoice:create" type="primary" icon={<PlusOutlined />} onClick={() => setCreateOpen(true)}>新建开票</PermissionButton>
        </Space>
      </div>

      <Table rowKey="id" columns={columns} dataSource={data?.items} loading={isLoading}
        pagination={{ current: page, pageSize: 20, total: data?.total, onChange: setPage, showTotal: (t) => `共 ${t} 条` }} />

      <Drawer title="新建开票申请" open={createOpen} onClose={() => { setCreateOpen(false); setContractId(undefined) }} width={480} footer={
        <Space style={{ float: 'right' }}>
          <Button onClick={() => { setCreateOpen(false); setContractId(undefined) }}>取消</Button>
          <Button type="primary" loading={creating} onClick={() => form.submit()}>提交</Button>
        </Space>
      }>
        {selectedContract && (
          <Alert
            style={{ marginBottom: 16 }}
            type="info"
            message={`合同总额: ${formatAmount(selectedContract.total_amount)}`}
            description={`已开票: ${formatAmount(selectedContract.invoiced_amount || 0)}  可开票余额: ${formatAmount(selectedContract.total_amount - (selectedContract.invoiced_amount || 0))}`}
          />
        )}
        {createError && <Alert type="error" message={(createError as any)?.data?.detail} style={{ marginBottom: 16 }} />}
        <Form form={form} layout="vertical" onFinish={handleCreate}>
          <Form.Item name="contract_id" label="关联合同" rules={[{ required: true }]}>
            <Select showSearch optionFilterProp="label" onChange={(v) => setContractId(v)}
              options={contractsData?.items.map(c => ({ value: c.id, label: `${c.contract_no} - ${c.title}` })) || []} />
          </Form.Item>
          <Form.Item name="invoice_no" label="发票编号" rules={[{ required: true }]}><Input disabled /></Form.Item>
          <Form.Item name="invoice_type" label="发票类型" rules={[{ required: true }]} initialValue="special">
            <Select options={Object.entries(InvoiceTypeLabels).map(([v, l]) => ({ value: v, label: l }))} />
          </Form.Item>
          <Form.Item name="amount" label="开票金额(元)" rules={[{ required: true }, { type: 'number', min: 0.01, message: '开票金额必须大于0' }]}>
            <InputNumber style={{ width: '100%' }} min={0.01} precision={2} />
          </Form.Item>
          <Form.Item name="tax_rate" label="税率" initialValue={0.06}>
            <Select options={[
              { value: 0.01, label: '1%' },
              { value: 0.03, label: '3%' },
              { value: 0.06, label: '6%' },
              { value: 0.09, label: '9%' },
              { value: 0.13, label: '13%' },
            ]} />
          </Form.Item>
          <Form.Item name="invoice_date" label="开票日期"><DatePicker style={{ width: '100%' }} /></Form.Item>
          <Form.Item name="remark" label="备注"><Input.TextArea rows={3} /></Form.Item>
        </Form>
      </Drawer>

      <Drawer title="编辑开票申请" open={editOpen} onClose={() => { setEditOpen(false); setEditingId(null); setContractId(undefined) }} width={480} footer={
        <Space style={{ float: 'right' }}>
          <Button onClick={() => { setEditOpen(false); setEditingId(null); setContractId(undefined) }}>取消</Button>
          <Button type="primary" loading={updating} onClick={() => editForm.submit()}>保存</Button>
        </Space>
      }>
        <Form form={editForm} layout="vertical" onFinish={handleUpdate}>
          <Form.Item name="contract_id" label="关联合同" rules={[{ required: true }]}>
            <Select showSearch optionFilterProp="label" onChange={(v) => setContractId(v)}
              options={contractsData?.items.map(c => ({ value: c.id, label: `${c.contract_no} - ${c.title}` })) || []} />
          </Form.Item>
          <Form.Item name="invoice_no" label="发票编号" rules={[{ required: true }]}><Input /></Form.Item>
          <Form.Item name="invoice_type" label="发票类型" rules={[{ required: true }]}>
            <Select options={Object.entries(InvoiceTypeLabels).map(([v, l]) => ({ value: v, label: l }))} />
          </Form.Item>
          <Form.Item name="amount" label="开票金额(元)" rules={[{ required: true }, { type: 'number', min: 0.01, message: '开票金额必须大于0' }]}>
            <InputNumber style={{ width: '100%' }} min={0.01} precision={2} />
          </Form.Item>
          <Form.Item name="tax_rate" label="税率">
            <Select options={[
              { value: 0.01, label: '1%' },
              { value: 0.03, label: '3%' },
              { value: 0.06, label: '6%' },
              { value: 0.09, label: '9%' },
              { value: 0.13, label: '13%' },
            ]} />
          </Form.Item>
          <Form.Item name="invoice_date" label="开票日期"><DatePicker style={{ width: '100%' }} /></Form.Item>
          <Form.Item name="remark" label="备注"><Input.TextArea rows={3} /></Form.Item>
        </Form>
      </Drawer>
    </div>
  )
}

export default Invoices

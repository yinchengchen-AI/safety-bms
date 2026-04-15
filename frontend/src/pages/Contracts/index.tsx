import React, { useState, useEffect } from 'react'
import { Table, Button, Input, Select, Tag, Space, Popconfirm, message, Drawer, Form, InputNumber, DatePicker, Descriptions } from 'antd'
import { PermissionButton } from '@/components/auth/PermissionButton'
import { PlusOutlined, FileTextOutlined, FilePdfOutlined, PrinterOutlined, FormOutlined } from '@ant-design/icons'
import {
  useListContractsQuery, useCreateContractMutation, useUpdateContractMutation, useDeleteContractMutation,
  useUpdateContractStatusMutation, useGetContractQuery,
  useGenerateContractDraftMutation, useLazyGetContractPdfUrlQuery,
} from '@/store/api/contractsApi'
import { useListContractTemplatesQuery } from '@/store/api/contractTemplatesApi'
import { useListCustomersQuery } from '@/store/api/customersApi'
import { ContractStatusLabels, ServiceTypeLabels, PaymentPlanLabels, formatAmount, generateBizNo } from '@/utils/constants'
import { downloadExport } from '@/utils/export'
import ContractSignModal from '@/components/ContractSignModal'
import { selectCurrentUser } from '@/store/slices/authSlice'
import type { Contract, ContractStatus, ServiceType, PaymentPlan } from '@/types'
import dayjs from 'dayjs'
import type { Dayjs } from 'dayjs'
import { useSelector } from 'react-redux'

interface ContractFormValues {
  contract_no: string
  title: string
  customer_id: number
  service_type: ServiceType
  total_amount: number
  payment_plan?: PaymentPlan
  template_id?: number
  sign_date?: Dayjs
  start_date?: Dayjs
  end_date?: Dayjs
  remark?: string
}

const statusColors: Record<ContractStatus, string> = {
  draft: 'default', review: 'processing', active: 'success', signed: 'purple', completed: 'green', terminated: 'error',
}

const Contracts: React.FC = () => {
  const [page, setPage] = useState(1)
  const [keyword, setKeyword] = useState('')
  const [status, setStatus] = useState<ContractStatus | undefined>()
  const [createOpen, setCreateOpen] = useState(false)
  const [editOpen, setEditOpen] = useState(false)
  const [editingId, setEditingId] = useState<number | null>(null)
  const [selectedId, setSelectedId] = useState<number | null>(null)
  const [signModalOpen, setSignModalOpen] = useState(false)
  const [signingContractId, setSigningContractId] = useState<number | null>(null)
  const [signingContract, setSigningContract] = useState<Contract | null>(null)
  const currentUser = useSelector(selectCurrentUser)
  const [form] = Form.useForm()
  const [editForm] = Form.useForm()
  const [triggerPdfUrl] = useLazyGetContractPdfUrlQuery()
  const [generateDraft, { isLoading: generatingDraft }] = useGenerateContractDraftMutation()

  const openPdfPreview = async (id: number) => {
    try {
      const res = await triggerPdfUrl(id).unwrap()
      if (res.url) {
        window.open(res.url, '_blank')
      } else {
        message.error('获取PDF链接失败')
      }
    } catch (err: any) {
      message.error(err?.data?.detail || '获取PDF失败')
    }
  }

  const handlePrintPdf = async (id: number) => {
    try {
      const res = await triggerPdfUrl(id).unwrap()
      if (res.url) {
        const printWindow = window.open(res.url, '_blank')
        if (printWindow) {
          printWindow.onload = () => {
            printWindow.print()
          }
        }
      } else {
        message.error('获取PDF链接失败')
      }
    } catch (err: any) {
      message.error(err?.data?.detail || '获取PDF失败')
    }
  }

  const handleGenerateDraft = async (id: number) => {
    try {
      await generateDraft(id).unwrap()
      message.success('合同草稿生成成功')
    } catch (err: any) {
      message.error(err?.data?.detail || '生成草稿失败')
    }
  }

  const handleOpenSign = (record: Contract) => {
    setSigningContractId(record.id)
    setSigningContract(record)
    setSignModalOpen(true)
  }

  useEffect(() => {
    if (createOpen) {
      form.setFieldsValue({ contract_no: generateBizNo('HT') })
    }
  }, [createOpen, form])

  const { data, isLoading } = useListContractsQuery({ page, page_size: 20, keyword, status })
  const { data: customersData } = useListCustomersQuery({ page: 1, page_size: 200 })
  const { data: templatesData } = useListContractTemplatesQuery({ page: 1, page_size: 200 })
  const [createContract, { isLoading: creating }] = useCreateContractMutation()
  const [updateContract, { isLoading: updating }] = useUpdateContractMutation()
  const [deleteContract] = useDeleteContractMutation()
  const [updateStatus] = useUpdateContractStatusMutation()

  const getTemplateOptions = (serviceType?: ServiceType) => {
    if (!templatesData?.items) return []
    return templatesData.items
      .filter((t) => !serviceType || t.service_type === serviceType)
      .map((t) => ({ value: t.id, label: t.name }))
  }

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

  const handleEdit = (record: Contract) => {
    setEditingId(record.id)
    editForm.setFieldsValue({
      contract_no: record.contract_no,
      title: record.title,
      customer_id: record.customer_id,
      service_type: record.service_type,
      total_amount: record.total_amount,
      payment_plan: record.payment_plan,
      template_id: record.template_id,
      sign_date: record.sign_date ? dayjs(record.sign_date) : undefined,
      start_date: record.start_date ? dayjs(record.start_date) : undefined,
      end_date: record.end_date ? dayjs(record.end_date) : undefined,
      remark: record.remark,
    })
    setEditOpen(true)
  }

  const handleUpdate = async (values: ContractFormValues) => {
    if (!editingId) return
    const payload = {
      ...values,
      sign_date: values.sign_date ? dayjs(values.sign_date).format('YYYY-MM-DD') : undefined,
      start_date: values.start_date ? dayjs(values.start_date).format('YYYY-MM-DD') : undefined,
      end_date: values.end_date ? dayjs(values.end_date).format('YYYY-MM-DD') : undefined,
    }
    try {
      await updateContract({ id: editingId, data: payload }).unwrap()
      message.success('合同更新成功')
      setEditOpen(false)
      editForm.resetFields()
      setEditingId(null)
    } catch (err: any) {
      message.error(err?.data?.detail || '更新失败')
    }
  }

  const handleExport = async () => {
    const params = new URLSearchParams()
    if (keyword) params.append('keyword', keyword)
    if (status) params.append('status', status)
    try {
      await downloadExport(`/api/v1/contracts/export?${params.toString()}`, `contracts_${dayjs().format('YYYYMMDD_HHmmss')}.xlsx`)
    } catch (err: any) {
      message.error(err.message || '导出失败')
    }
  }

  const columns = [
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
    { title: '操作', key: 'action', width: 280, render: (_: any, r: Contract) => (
      <Space wrap>
        {r.status === 'draft' && (
          <PermissionButton permission="contract:update" type="link" size="small" onClick={() => handleEdit(r)}>编辑</PermissionButton>
        )}
        {r.status === 'draft' && (
          <Popconfirm title="确认删除？" onConfirm={() => deleteContract(r.id)}>
            <PermissionButton permission="contract:delete" type="link" danger size="small">删除</PermissionButton>
          </Popconfirm>
        )}
        {r.status === 'draft' && (
          <PermissionButton permission="contract:update" size="small" onClick={() => {
            updateStatus({ id: r.id, status: 'review' }).unwrap()
              .then(() => message.success('已提交审核，标准合同草稿已生成'))
              .catch((err: any) => message.error(err?.data?.detail || '提交审核失败'))
          }}>提交审核</PermissionButton>
        )}
        {r.status === 'review' && (
          <>
            <PermissionButton permission="contract:update" size="small" type="primary" onClick={() => updateStatus({ id: r.id, status: 'active' })}>审核通过</PermissionButton>
            <PermissionButton permission="contract:update" size="small" onClick={() => updateStatus({ id: r.id, status: 'draft' })}>审核驳回</PermissionButton>
          </>
        )}
        {r.status === 'draft' && r.template_id && (
          <PermissionButton permission="contract:update" size="small" icon={<FileTextOutlined />} onClick={() => handleGenerateDraft(r.id)} loading={generatingDraft}>生成草稿</PermissionButton>
        )}
        {r.status === 'active' && r.draft_doc_url && (
          <PermissionButton permission="contract:sign" size="small" type="primary" icon={<FormOutlined />} onClick={() => handleOpenSign(r)}>发起签订</PermissionButton>
        )}
        {r.status === 'signed' && r.final_pdf_url && (
          <>
            <PermissionButton permission="contract:read" size="small" icon={<FilePdfOutlined />} onClick={() => openPdfPreview(r.id)}>下载PDF</PermissionButton>
            <PermissionButton permission="contract:read" size="small" icon={<PrinterOutlined />} onClick={() => handlePrintPdf(r.id)}>打印</PermissionButton>
          </>
        )}
      </Space>
    )},
  ]

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 16 }}>
        <Space>
          <Input.Search placeholder="搜索合同编号/名称" onSearch={setKeyword} style={{ width: 240 }} allowClear />
          <Select placeholder="合同状态" allowClear style={{ width: 120 }} onChange={setStatus}
            options={Object.entries(ContractStatusLabels).map(([v, l]) => ({ value: v, label: l }))} />
        </Space>
        <Space>
          <PermissionButton permission="contract:export" onClick={handleExport}>导出</PermissionButton>
          <PermissionButton permission="contract:create" type="primary" icon={<PlusOutlined />} onClick={() => setCreateOpen(true)}>新建合同</PermissionButton>
        </Space>
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
          <Form.Item name="contract_no" label="合同编号" rules={[{ required: true }]}><Input disabled /></Form.Item>
          <Form.Item name="title" label="合同名称" rules={[{ required: true }]}><Input /></Form.Item>
          <Form.Item name="customer_id" label="客户" rules={[{ required: true }]}>
            <Select showSearch optionFilterProp="label"
              options={customersData?.items.map(c => ({ value: c.id, label: c.name })) || []} />
          </Form.Item>
          <Form.Item name="service_type" label="服务类型" rules={[{ required: true }]}>
            <Select options={Object.entries(ServiceTypeLabels).map(([v, l]) => ({ value: v, label: l }))}
              onChange={() => form.setFieldsValue({ template_id: undefined })} />
          </Form.Item>
          <Form.Item shouldUpdate={(prev, cur) => prev.service_type !== cur.service_type} noStyle>
            {({ getFieldValue }) => (
              <Form.Item name="template_id" label="合同模板">
                <Select allowClear showSearch optionFilterProp="label"
                  options={getTemplateOptions(getFieldValue('service_type'))} />
              </Form.Item>
            )}
          </Form.Item>
          <Form.Item name="total_amount" label="合同金额(元)" rules={[{ required: true }]}>
            <InputNumber style={{ width: '100%' }} min={0} precision={2} />
          </Form.Item>
          <Form.Item name="payment_plan" label="付款方式" initialValue="once">
            <Select options={Object.entries(PaymentPlanLabels).map(([v, l]) => ({ value: v, label: l }))} />
          </Form.Item>
          <Form.Item name="sign_date" label="签订日期"><DatePicker style={{ width: '100%' }} /></Form.Item>
          <Form.Item name="start_date" label="服务开始日期" rules={[{ validator: (_, value) => {
            if (!value) return Promise.resolve()
            const end = form.getFieldValue('end_date')
            if (end && dayjs(value).isAfter(end, 'day')) {
              return Promise.reject(new Error('开始日期不能晚于结束日期'))
            }
            return Promise.resolve()
          }}]}><DatePicker style={{ width: '100%' }} /></Form.Item>
          <Form.Item name="end_date" label="服务结束日期" rules={[{ validator: (_, value) => {
            if (!value) return Promise.resolve()
            const start = form.getFieldValue('start_date')
            if (start && dayjs(value).isBefore(start, 'day')) {
              return Promise.reject(new Error('结束日期不能早于开始日期'))
            }
            return Promise.resolve()
          }}]}><DatePicker style={{ width: '100%' }} /></Form.Item>
          <Form.Item name="remark" label="备注"><Input.TextArea rows={3} /></Form.Item>
        </Form>
      </Drawer>

      <Drawer title="编辑合同" open={editOpen} onClose={() => { setEditOpen(false); setEditingId(null) }} width={560} footer={
        <Space style={{ float: 'right' }}>
          <Button onClick={() => { setEditOpen(false); setEditingId(null) }}>取消</Button>
          <Button type="primary" loading={updating} onClick={() => editForm.submit()}>保存</Button>
        </Space>
      }>
        <Form form={editForm} layout="vertical" onFinish={handleUpdate}>
          <Form.Item name="contract_no" label="合同编号" rules={[{ required: true }]}><Input /></Form.Item>
          <Form.Item name="title" label="合同名称" rules={[{ required: true }]}><Input /></Form.Item>
          <Form.Item name="customer_id" label="客户" rules={[{ required: true }]}>
            <Select showSearch optionFilterProp="label"
              options={customersData?.items.map(c => ({ value: c.id, label: c.name })) || []} />
          </Form.Item>
          <Form.Item name="service_type" label="服务类型" rules={[{ required: true }]}>
            <Select options={Object.entries(ServiceTypeLabels).map(([v, l]) => ({ value: v, label: l }))}
              onChange={() => editForm.setFieldsValue({ template_id: undefined })} />
          </Form.Item>
          <Form.Item shouldUpdate={(prev, cur) => prev.service_type !== cur.service_type} noStyle>
            {({ getFieldValue }) => (
              <Form.Item name="template_id" label="合同模板">
                <Select allowClear showSearch optionFilterProp="label"
                  options={getTemplateOptions(getFieldValue('service_type'))} />
              </Form.Item>
            )}
          </Form.Item>
          <Form.Item name="total_amount" label="合同金额(元)" rules={[{ required: true }]}>
            <InputNumber style={{ width: '100%' }} min={0} precision={2} />
          </Form.Item>
          <Form.Item name="payment_plan" label="付款方式">
            <Select options={Object.entries(PaymentPlanLabels).map(([v, l]) => ({ value: v, label: l }))} />
          </Form.Item>
          <Form.Item name="sign_date" label="签订日期"><DatePicker style={{ width: '100%' }} /></Form.Item>
          <Form.Item name="start_date" label="服务开始日期" rules={[{ validator: (_, value) => {
            if (!value) return Promise.resolve()
            const end = editForm.getFieldValue('end_date')
            if (end && dayjs(value).isAfter(end, 'day')) {
              return Promise.reject(new Error('开始日期不能晚于结束日期'))
            }
            return Promise.resolve()
          }}]}><DatePicker style={{ width: '100%' }} /></Form.Item>
          <Form.Item name="end_date" label="服务结束日期" rules={[{ validator: (_, value) => {
            if (!value) return Promise.resolve()
            const start = editForm.getFieldValue('start_date')
            if (start && dayjs(value).isBefore(start, 'day')) {
              return Promise.reject(new Error('结束日期不能早于开始日期'))
            }
            return Promise.resolve()
          }}]}><DatePicker style={{ width: '100%' }} /></Form.Item>
          <Form.Item name="remark" label="备注"><Input.TextArea rows={3} /></Form.Item>
        </Form>
      </Drawer>

      {selectedId && <ContractDetail
        id={selectedId}
        onClose={() => setSelectedId(null)}
        onGenerateDraft={handleGenerateDraft}
        onOpenSign={handleOpenSign}
        onOpenPdf={openPdfPreview}
        onPrintPdf={handlePrintPdf}
        generatingDraft={generatingDraft}
      />}

      {signingContractId && (
        <ContractSignModal
          contractId={signingContractId}
          open={signModalOpen}
          onClose={() => { setSignModalOpen(false); setSigningContractId(null); setSigningContract(null) }}
          onOpenPdf={openPdfPreview}
          partyANameDefault={currentUser?.full_name || currentUser?.username || ''}
          partyBNameDefault={signingContract?.customer_name || ''}
        />
      )}
    </div>
  )
}

const ContractDetail: React.FC<{
  id: number
  onClose: () => void
  onGenerateDraft: (id: number) => void
  onOpenSign: (record: Contract) => void
  onOpenPdf: (id: number) => void
  onPrintPdf: (id: number) => void
  generatingDraft: boolean
}> = ({ id, onClose, onGenerateDraft, onOpenSign, onOpenPdf, onPrintPdf, generatingDraft }) => {
  const { data } = useGetContractQuery(id)
  const [updateStatus] = useUpdateContractStatusMutation()
  if (!data) return null

  return (
    <Drawer title="合同详情" open width={680} onClose={onClose}
      extra={
        <Space>
          {data.status === 'review' && (
            <>
              <PermissionButton permission="contract:update" type="primary" icon={<FormOutlined />} onClick={() => updateStatus({ id: data.id, status: 'active' })}>审核通过</PermissionButton>
              <PermissionButton permission="contract:update" onClick={() => updateStatus({ id: data.id, status: 'draft' })}>审核驳回</PermissionButton>
            </>
          )}
          {data.status === 'active' && data.draft_doc_url && (
            <PermissionButton permission="contract:sign" type="primary" icon={<FormOutlined />} onClick={() => onOpenSign(data)}>发起签订</PermissionButton>
          )}
          {data.status === 'draft' && data.template_id && (
            <PermissionButton permission="contract:update" icon={<FileTextOutlined />} onClick={() => onGenerateDraft(data.id)} loading={generatingDraft}>生成草稿</PermissionButton>
          )}
          {data.status === 'signed' && data.final_pdf_url && (
            <>
              <PermissionButton permission="contract:read" icon={<FilePdfOutlined />} onClick={() => onOpenPdf(data.id)}>下载PDF</PermissionButton>
              <PermissionButton permission="contract:read" icon={<PrinterOutlined />} onClick={() => onPrintPdf(data.id)}>打印</PermissionButton>
            </>
          )}
        </Space>
      }
    >
      <Descriptions column={2} bordered size="small">
        <Descriptions.Item label="合同编号">{data.contract_no}</Descriptions.Item>
        <Descriptions.Item label="状态"><Tag color={statusColors[data.status]}>{ContractStatusLabels[data.status]}</Tag></Descriptions.Item>
        <Descriptions.Item label="合同名称" span={2}>{data.title}</Descriptions.Item>
        <Descriptions.Item label="客户">{data.customer_name}</Descriptions.Item>
        <Descriptions.Item label="服务类型">{ServiceTypeLabels[data.service_type]}</Descriptions.Item>
        <Descriptions.Item label="合同金额">{formatAmount(data.total_amount)}</Descriptions.Item>
        <Descriptions.Item label="付款方式">{PaymentPlanLabels[data.payment_plan]}</Descriptions.Item>
        <Descriptions.Item label="已开票金额">{formatAmount(data.invoiced_amount || 0)}</Descriptions.Item>
        <Descriptions.Item label="已收款金额">{formatAmount(data.received_amount || 0)}</Descriptions.Item>
        <Descriptions.Item label="签订日期">{data.sign_date || '-'}</Descriptions.Item>
        <Descriptions.Item label="服务期">{data.start_date || '-'} ~ {data.end_date || '-'}</Descriptions.Item>
        {data.signed_at && (
          <Descriptions.Item label="签订时间" span={2}>{data.signed_at}</Descriptions.Item>
        )}
        <Descriptions.Item label="备注" span={2}>{data.remark}</Descriptions.Item>
        {data.standard_doc_url ? (
          <Descriptions.Item label="标准合同草稿" span={2}>
            <Button type="link" onClick={() => window.open(data.standard_doc_url, '_blank')}>下载标准合同草稿</Button>
          </Descriptions.Item>
        ) : (
          <Descriptions.Item label="标准合同草稿" span={2}>
            <span style={{ color: '#999' }}>尚未生成标准合同草稿（提交审核后自动生成）</span>
          </Descriptions.Item>
        )}
      </Descriptions>
    </Drawer>
  )
}

export default Contracts

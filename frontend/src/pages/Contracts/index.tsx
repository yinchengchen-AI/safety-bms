import React, { useState, useEffect } from 'react'
import { Table, Button, Input, Select, Tag, Space, Popconfirm, message, Drawer, Form, InputNumber, DatePicker, Descriptions, Divider, Modal, Upload } from 'antd'
import { PermissionButton } from '@/components/auth/PermissionButton'
import { PlusOutlined, FileTextOutlined, UploadOutlined, DeleteOutlined, StopOutlined } from '@ant-design/icons'
import {
  useListContractsQuery, useCreateContractMutation, useUpdateContractMutation, useDeleteContractMutation,
  useUpdateContractStatusMutation, useGetContractQuery,
  useGenerateContractDraftMutation,
  useUploadContractAttachmentFileMutation,
  useUploadContractAttachmentMutation,
  useDeleteContractAttachmentMutation,
} from '@/store/api/contractsApi'
import { useListContractTemplatesQuery } from '@/store/api/contractTemplatesApi'
import { useListCustomersQuery } from '@/store/api/customersApi'
import { ContractStatusLabels, PaymentPlanLabels, formatAmount, formatDateTime, generateBizNo } from '@/utils/constants'
import { downloadExport } from '@/utils/export'
import type { Contract, ContractStatus, PaymentPlan, ContractAttachment } from '@/types'
import dayjs from 'dayjs'
import type { Dayjs } from 'dayjs'
import { useListServiceTypesQuery } from '@/store/api/serviceTypesApi'

interface ContractFormValues {
  contract_no: string
  title: string
  customer_id: number
  service_type: number
  total_amount: number
  payment_plan?: PaymentPlan
  template_id?: number
  sign_date?: Dayjs
  start_date?: Dayjs
  end_date?: Dayjs
  remark?: string
}

const statusColors: Record<ContractStatus, string> = {
  draft: 'default',
  signed: 'purple',
  executing: 'blue',
  completed: 'green',
  terminated: 'error',
}

const Contracts: React.FC = () => {
  const [page, setPage] = useState(1)
  const [keyword, setKeyword] = useState('')
  const [status, setStatus] = useState<ContractStatus | undefined>()
  const [createOpen, setCreateOpen] = useState(false)
  const [editOpen, setEditOpen] = useState(false)
  const [editingId, setEditingId] = useState<number | null>(null)
  const [selectedId, setSelectedId] = useState<number | null>(null)
  const [uploadOpen, setUploadOpen] = useState(false)
  const [uploadingContractId, setUploadingContractId] = useState<number | null>(null)
  const [uploadFile, setUploadFile] = useState<File | null>(null)
  const [form] = Form.useForm()
  const [editForm] = Form.useForm()
  const [generateDraft, { isLoading: generatingDraft }] = useGenerateContractDraftMutation()
  const [uploadContractAttachmentFile] = useUploadContractAttachmentFileMutation()
  const [uploadContractAttachment] = useUploadContractAttachmentMutation()
  const { data: serviceTypesData } = useListServiceTypesQuery({ page_size: 200 })

  const serviceTypeMap = React.useMemo(() => {
    const map = new Map<number, string>()
    serviceTypesData?.items?.forEach((st) => map.set(st.id, st.name))
    return map
  }, [serviceTypesData])

  const serviceTypeOptions = React.useMemo(() => {
    return serviceTypesData?.items?.map((st) => ({ value: st.id, label: st.name })) || []
  }, [serviceTypesData])

  const handleGenerateDraft = async (id: number) => {
    try {
      await generateDraft(id).unwrap()
      message.success('合同草稿生成成功')
    } catch (err: any) {
      message.error(err?.data?.detail || '生成草稿失败')
    }
  }

  const handleOpenUpload = (record: Contract) => {
    setUploadingContractId(record.id)
    setUploadFile(null)
    setUploadOpen(true)
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

  const getTemplateOptions = (serviceType?: number) => {
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
    { title: '服务类型', dataIndex: 'service_type', key: 'service_type', render: (s: number) => serviceTypeMap.get(s) || s },
    { title: '合同金额', dataIndex: 'total_amount', key: 'total_amount', render: formatAmount },
    { title: '状态', dataIndex: 'status', key: 'status', render: (s: ContractStatus) => (
      <Tag color={statusColors[s]}>{ContractStatusLabels[s]}</Tag>
    )},
    { title: '签订日期', dataIndex: 'sign_date', key: 'sign_date' },
    { title: '操作', key: 'action', width: 320, render: (_: any, r: Contract) => (
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
          <PermissionButton permission="contract:update" size="small" icon={<FileTextOutlined />} onClick={() => handleGenerateDraft(r.id)} loading={generatingDraft}>生成草稿</PermissionButton>
        )}
        {r.status === 'draft' && (
          <PermissionButton permission="contract:update" size="small" icon={<UploadOutlined />} onClick={() => handleOpenUpload(r)}>上传已签附件</PermissionButton>
        )}
        {r.status === 'draft' && (
          <Popconfirm title="确认终止合同？" onConfirm={() => updateStatus({ id: r.id, status: 'terminated' })}>
            <PermissionButton permission="contract:update" size="small" danger icon={<StopOutlined />}>终止</PermissionButton>
          </Popconfirm>
        )}
        {r.status === 'signed' && (
          <>
            <PermissionButton permission="contract:update" size="small" type="primary" onClick={() => updateStatus({ id: r.id, status: 'executing' })}>开始履行</PermissionButton>
            <Popconfirm title="确认终止合同？" onConfirm={() => updateStatus({ id: r.id, status: 'terminated' })}>
              <PermissionButton permission="contract:update" size="small" danger icon={<StopOutlined />}>终止</PermissionButton>
            </Popconfirm>
          </>
        )}
        {r.status === 'executing' && (
          <>
            <PermissionButton permission="contract:update" size="small" type="primary" onClick={() => updateStatus({ id: r.id, status: 'completed' })}>标记完成</PermissionButton>
            <Popconfirm title="确认终止合同？" onConfirm={() => updateStatus({ id: r.id, status: 'terminated' })}>
              <PermissionButton permission="contract:update" size="small" danger icon={<StopOutlined />}>终止</PermissionButton>
            </Popconfirm>
          </>
        )}
        {(r.status === 'completed' || r.status === 'terminated') && (
          <Button type="link" size="small" onClick={() => setSelectedId(r.id)}>查看详情</Button>
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

      <Drawer title="新建合同" open={createOpen} onClose={() => setCreateOpen(false)} width={640} footer={
        <Space style={{ float: 'right' }}>
          <Button onClick={() => setCreateOpen(false)}>取消</Button>
          <Button type="primary" loading={creating} onClick={() => form.submit()}>创建</Button>
        </Space>
      }>
        <Form form={form} layout="vertical" onFinish={handleCreate}>
          <Divider orientation="left">基本信息</Divider>
          <Form.Item name="contract_no" label="合同编号" rules={[{ required: true }]}><Input disabled /></Form.Item>
          <Form.Item name="title" label="合同名称" rules={[{ required: true }]}><Input /></Form.Item>
          <Form.Item name="customer_id" label="客户" rules={[{ required: true }]}>
            <Select showSearch optionFilterProp="label"
              options={customersData?.items.map(c => ({ value: c.id, label: c.name })) || []} />
          </Form.Item>
          <Form.Item name="service_type" label="服务类型" rules={[{ required: true }]}>
            <Select options={serviceTypeOptions}
              onChange={() => form.setFieldsValue({ template_id: undefined })} />
          </Form.Item>
          <Form.Item shouldUpdate={(prev, cur) => prev.service_type !== cur.service_type} noStyle>
            {({ getFieldValue }) => (
              <Form.Item name="template_id" label="合同模板">
                <Select allowClear showSearch optionFilterProp="label"
                  options={getTemplateOptions(getFieldValue('service_type') as number)} />
              </Form.Item>
            )}
          </Form.Item>
          <Divider orientation="left">商务信息</Divider>
          <Form.Item name="total_amount" label="合同金额(元)" rules={[{ required: true }]}>
            <InputNumber style={{ width: '100%' }} min={0} precision={2} />
          </Form.Item>
          <Form.Item name="payment_plan" label="付款方式" initialValue="once">
            <Select options={Object.entries(PaymentPlanLabels).map(([v, l]) => ({ value: v, label: l }))} />
          </Form.Item>
          <Divider orientation="left">履约信息</Divider>
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
          <Divider orientation="left">补充信息</Divider>
          <Form.Item name="remark" label="备注"><Input.TextArea rows={3} /></Form.Item>
        </Form>
      </Drawer>

      <Drawer title="编辑合同" open={editOpen} onClose={() => { setEditOpen(false); setEditingId(null) }} width={640} footer={
        <Space style={{ float: 'right' }}>
          <Button onClick={() => { setEditOpen(false); setEditingId(null) }}>取消</Button>
          <Button type="primary" loading={updating} onClick={() => editForm.submit()}>保存</Button>
        </Space>
      }>
        <Form form={editForm} layout="vertical" onFinish={handleUpdate}>
          <Divider orientation="left">基本信息</Divider>
          <Form.Item name="contract_no" label="合同编号" rules={[{ required: true }]}><Input /></Form.Item>
          <Form.Item name="title" label="合同名称" rules={[{ required: true }]}><Input /></Form.Item>
          <Form.Item name="customer_id" label="客户" rules={[{ required: true }]}>
            <Select showSearch optionFilterProp="label"
              options={customersData?.items.map(c => ({ value: c.id, label: c.name })) || []} />
          </Form.Item>
          <Form.Item name="service_type" label="服务类型" rules={[{ required: true }]}>
            <Select options={serviceTypeOptions}
              onChange={() => editForm.setFieldsValue({ template_id: undefined })} />
          </Form.Item>
          <Form.Item shouldUpdate={(prev, cur) => prev.service_type !== cur.service_type} noStyle>
            {({ getFieldValue }) => (
              <Form.Item name="template_id" label="合同模板">
                <Select allowClear showSearch optionFilterProp="label"
                  options={getTemplateOptions(getFieldValue('service_type') as number)} />
              </Form.Item>
            )}
          </Form.Item>
          <Divider orientation="left">商务信息</Divider>
          <Form.Item name="total_amount" label="合同金额(元)" rules={[{ required: true }]}>
            <InputNumber style={{ width: '100%' }} min={0} precision={2} />
          </Form.Item>
          <Form.Item name="payment_plan" label="付款方式">
            <Select options={Object.entries(PaymentPlanLabels).map(([v, l]) => ({ value: v, label: l }))} />
          </Form.Item>
          <Divider orientation="left">履约信息</Divider>
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
          <Divider orientation="left">补充信息</Divider>
          <Form.Item name="remark" label="备注"><Input.TextArea rows={3} /></Form.Item>
        </Form>
      </Drawer>

      {selectedId && <ContractDetail
        id={selectedId}
        onClose={() => setSelectedId(null)}
        onGenerateDraft={handleGenerateDraft}
        onOpenUpload={handleOpenUpload}
        generatingDraft={generatingDraft}
      />}

      <Modal
        title="上传已签合同附件"
        open={uploadOpen}
        onCancel={() => { setUploadOpen(false); setUploadingContractId(null); setUploadFile(null) }}
        onOk={async () => {
          if (!uploadFile || !uploadingContractId) return
          try {
            const uploadResult = await uploadContractAttachmentFile({ id: uploadingContractId, file: uploadFile }).unwrap()
            await uploadContractAttachment({
              id: uploadingContractId,
              data: {
                file_name: uploadResult.file_name,
                file_url: uploadResult.file_url,
                file_type: 'signed',
              }
            }).unwrap()
            message.success('已签合同上传成功，合同已更新为已签订')
            setUploadOpen(false)
            setUploadingContractId(null)
            setUploadFile(null)
          } catch (err: any) {
            message.error(err?.data?.detail || '上传失败')
          }
        }}
        okButtonProps={{ disabled: !uploadFile }}
      >
        <Upload
          beforeUpload={(file) => { setUploadFile(file); return false }}
          onRemove={() => setUploadFile(null)}
          fileList={uploadFile ? [{ uid: '-1', name: uploadFile.name, status: 'done' }] : []}
        >
          <Button icon={<UploadOutlined />}>选择文件</Button>
        </Upload>
      </Modal>
    </div>
  )
}

const ContractDetail: React.FC<{
  id: number
  onClose: () => void
  onGenerateDraft: (id: number) => void
  onOpenUpload: (record: Contract) => void
  generatingDraft: boolean
}> = ({ id, onClose, onGenerateDraft, onOpenUpload, generatingDraft }) => {
  const { data } = useGetContractQuery(id)
  const [updateStatus] = useUpdateContractStatusMutation()
  const [deleteAttachment] = useDeleteContractAttachmentMutation()
  const { data: serviceTypesData } = useListServiceTypesQuery({ page_size: 200 })
  const serviceTypeMap = React.useMemo(() => {
    const map = new Map<number, string>()
    serviceTypesData?.items?.forEach((st) => map.set(st.id, st.name))
    return map
  }, [serviceTypesData])

  if (!data) return null

  const draftAttachments = (data.attachments || []).filter((a: ContractAttachment) => a.file_type === 'draft')
  const signedAttachments = (data.attachments || []).filter((a: ContractAttachment) => a.file_type === 'signed')
  const latestDraft = draftAttachments[draftAttachments.length - 1]

  return (
    <Drawer title="合同详情" open width={720} onClose={onClose}
      extra={
        <Space>
          {data.status === 'draft' && (
            <PermissionButton permission="contract:update" icon={<FileTextOutlined />} onClick={() => onGenerateDraft(data.id)} loading={generatingDraft}>生成草稿</PermissionButton>
          )}
          {data.status === 'draft' && (
            <PermissionButton permission="contract:update" icon={<UploadOutlined />} onClick={() => onOpenUpload(data)}>上传已签附件</PermissionButton>
          )}
          {data.status === 'signed' && (
            <PermissionButton permission="contract:update" type="primary" onClick={() => updateStatus({ id: data.id, status: 'executing' })}>开始履行</PermissionButton>
          )}
          {data.status === 'executing' && (
            <PermissionButton permission="contract:update" type="primary" onClick={() => updateStatus({ id: data.id, status: 'completed' })}>标记完成</PermissionButton>
          )}
          {(data.status === 'draft' || data.status === 'signed' || data.status === 'executing') && (
            <Popconfirm title="确认终止合同？" onConfirm={() => updateStatus({ id: data.id, status: 'terminated' })}>
              <PermissionButton permission="contract:update" danger>终止</PermissionButton>
            </Popconfirm>
          )}
        </Space>
      }
    >
      <Descriptions column={2} bordered size="small">
        <Descriptions.Item label="合同编号">{data.contract_no}</Descriptions.Item>
        <Descriptions.Item label="状态"><Tag color={statusColors[data.status]}>{ContractStatusLabels[data.status]}</Tag></Descriptions.Item>
        <Descriptions.Item label="合同名称" span={2}>{data.title}</Descriptions.Item>
        <Descriptions.Item label="客户">{data.customer_name}</Descriptions.Item>
        <Descriptions.Item label="服务类型">{serviceTypeMap.get(data.service_type) || data.service_type}</Descriptions.Item>
        <Descriptions.Item label="合同金额">{formatAmount(data.total_amount)}</Descriptions.Item>
        <Descriptions.Item label="付款方式">{PaymentPlanLabels[data.payment_plan]}</Descriptions.Item>
        <Descriptions.Item label="已开票金额">{formatAmount(data.invoiced_amount || 0)}</Descriptions.Item>
        <Descriptions.Item label="已收款金额">{formatAmount(data.received_amount || 0)}</Descriptions.Item>
        <Descriptions.Item label="签订日期">{data.sign_date || '-'}</Descriptions.Item>
        <Descriptions.Item label="服务期">{data.start_date || '-'} ~ {data.end_date || '-'}</Descriptions.Item>
        {data.signed_at && (
          <Descriptions.Item label="签订时间" span={2}>{formatDateTime(data.signed_at)}</Descriptions.Item>
        )}
        <Descriptions.Item label="备注" span={2}>{data.remark}</Descriptions.Item>
      </Descriptions>

      <Divider orientation="left">文件资料</Divider>
      <Descriptions column={1} bordered size="small">
        <Descriptions.Item label="合同草稿">
          {latestDraft ? (
            <Space>
              <Button type="link" onClick={() => window.open(latestDraft.file_url, '_blank')}>下载草稿</Button>
              <span style={{ color: '#999', fontSize: 12 }}>生成于 {formatDateTime(latestDraft.uploaded_at)}</span>
            </Space>
          ) : '未生成'}
        </Descriptions.Item>
        <Descriptions.Item label="已签附件">
          {signedAttachments.length > 0 ? (
            <Space direction="vertical" style={{ width: '100%' }}>
              {signedAttachments.map((att: ContractAttachment) => (
                <Space key={att.id}>
                  <Button type="link" onClick={() => window.open(att.file_url, '_blank')}>{att.file_name}</Button>
                  <span style={{ color: '#999', fontSize: 12 }}>上传于 {formatDateTime(att.uploaded_at)}</span>
                  {data.status === 'draft' && (
                    <Popconfirm title="确认删除？" onConfirm={async () => {
                      try {
                        await deleteAttachment({ id: data.id, attachmentId: att.id }).unwrap()
                        message.success('删除成功')
                      } catch (err: any) {
                        message.error(err?.data?.detail || '删除失败')
                      }
                    }}>
                      <Button type="link" danger size="small" icon={<DeleteOutlined />}>删除</Button>
                    </Popconfirm>
                  )}
                </Space>
              ))}
            </Space>
          ) : '未上传'}
        </Descriptions.Item>
      </Descriptions>
    </Drawer>
  )
}

export default Contracts

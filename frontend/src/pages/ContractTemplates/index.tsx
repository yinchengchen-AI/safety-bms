import React, { useState, useMemo } from 'react'
import { Table, Button, Space, Select, Input, message, Modal, Form, Upload, Tag } from 'antd'
import { PlusOutlined, UploadOutlined, DeleteOutlined, EyeOutlined } from '@ant-design/icons'
import { PermissionButton } from '@/components/auth/PermissionButton'
import { useListContractTemplatesQuery, useCreateContractTemplateMutation, useUploadContractTemplateFileMutation, useDeleteContractTemplateMutation, useLazyGetTemplateDownloadUrlQuery } from '@/store/api/contractTemplatesApi'
import { useListServiceTypesQuery } from '@/store/api/serviceTypesApi'
import type { ContractTemplate } from '@/types'

const ContractTemplates: React.FC = () => {
  const [page, setPage] = useState(1)
  const [serviceType, setServiceType] = useState<number | undefined>()
  const [createOpen, setCreateOpen] = useState(false)
  const [createFile, setCreateFile] = useState<File | null>(null)
  const [previewOpen, setPreviewOpen] = useState(false)
  const [previewUrl, setPreviewUrl] = useState<string | null>(null)
  const [form] = Form.useForm()

  const { data, isLoading } = useListContractTemplatesQuery({ page, page_size: 20, service_type: serviceType })
  const [createTemplate, { isLoading: creating }] = useCreateContractTemplateMutation()
  const [uploadTemplateFile, { isLoading: uploading }] = useUploadContractTemplateFileMutation()
  const [deleteTemplate] = useDeleteContractTemplateMutation()
  const [getDownloadUrl, { isFetching: previewLoading }] = useLazyGetTemplateDownloadUrlQuery()
  const { data: serviceTypesData } = useListServiceTypesQuery({ page_size: 200 })

  const serviceTypeMap = useMemo(() => {
    const map = new Map<number, string>()
    serviceTypesData?.items?.forEach((st) => map.set(st.id, st.name))
    return map
  }, [serviceTypesData])

  const serviceTypeOptions = useMemo(() => {
    return serviceTypesData?.items?.map((st) => ({ value: st.id, label: st.name })) || []
  }, [serviceTypesData])

  const handleCreate = async (values: { name: string; service_type: number }) => {
    try {
      const result = await createTemplate({ ...values, is_default: false }).unwrap()
      if (createFile && result.id) {
        await uploadTemplateFile({ id: result.id, file: createFile }).unwrap()
      }
      message.success('模板创建成功')
      setCreateOpen(false)
      form.resetFields()
      setCreateFile(null)
    } catch (err: any) {
      message.error(err?.data?.detail || '创建失败')
    }
  }

  const handleDelete = async (id: number) => {
    try {
      await deleteTemplate(id).unwrap()
      message.success('删除成功')
    } catch (err: any) {
      message.error(err?.data?.detail || '删除失败')
    }
  }

  const handlePreview = async (id: number) => {
    try {
      const result = await getDownloadUrl(id).unwrap()
      setPreviewUrl(result.url)
      setPreviewOpen(true)
    } catch (err: any) {
      message.error(err?.data?.detail || '获取预览链接失败')
    }
  }

  const columns = [
    { title: '模板名称', dataIndex: 'name', key: 'name' },
    { title: '服务类型', dataIndex: 'service_type', key: 'service_type', render: (s: number) => serviceTypeMap.get(s) || s },
    { title: '默认模板', dataIndex: 'is_default', key: 'is_default', render: (v: boolean) => v ? <Tag color="blue">是</Tag> : <Tag>否</Tag> },
    { title: '文件', dataIndex: 'file_url', key: 'file_url', render: (v: string | undefined) => v ? <Tag color="success">已上传</Tag> : <Tag color="warning">未上传</Tag> },
    { title: '创建时间', dataIndex: 'created_at', key: 'created_at' },
    {
      title: '操作',
      key: 'action',
      render: (_: any, r: ContractTemplate) => (
        <Space>
          {r.file_url && (
            <PermissionButton permission="contract:read" size="small" icon={<EyeOutlined />} onClick={() => handlePreview(r.id)}>预览</PermissionButton>
          )}
          {!r.file_url && (
            <Upload
              beforeUpload={(file) => {
                uploadTemplateFile({ id: r.id, file }).unwrap().then(() => message.success('上传成功')).catch(() => message.error('上传失败'))
                return false
              }}
              showUploadList={false}
              accept=".docx"
            >
              <PermissionButton permission="contract:update" size="small" icon={<UploadOutlined />}>上传</PermissionButton>
            </Upload>
          )}
          <PermissionButton permission="contract:delete" danger size="small" icon={<DeleteOutlined />} onClick={() => handleDelete(r.id)}>删除</PermissionButton>
        </Space>
      ),
    },
  ]

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 16 }}>
        <Space>
          <Select
            placeholder="服务类型"
            allowClear
            style={{ width: 160 }}
            onChange={(v) => setServiceType(v)}
            options={serviceTypeOptions}
          />
        </Space>
        <PermissionButton permission="contract:create" type="primary" icon={<PlusOutlined />} onClick={() => setCreateOpen(true)}>新建模板</PermissionButton>
      </div>

      <Table
        rowKey="id"
        columns={columns}
        dataSource={data?.items}
        loading={isLoading}
        pagination={{ current: page, pageSize: 20, total: data?.total, onChange: setPage, showTotal: (t) => `共 ${t} 条` }}
      />

      <Modal
        title="新建合同模板"
        open={createOpen}
        onCancel={() => { setCreateOpen(false); form.resetFields(); setCreateFile(null) }}
        onOk={() => form.submit()}
        confirmLoading={creating || uploading}
      >
        <Form form={form} layout="vertical" onFinish={handleCreate}>
          <Form.Item name="name" label="模板名称" rules={[{ required: true }]}>
            <Input placeholder="例如：安全评价合同模板" />
          </Form.Item>
          <Form.Item name="service_type" label="服务类型" rules={[{ required: true }]}>
            <Select
              options={serviceTypeOptions}
              placeholder="请选择服务类型"
            />
          </Form.Item>
          <Form.Item label="模板文件 (.docx)">
            <Upload
              beforeUpload={(file) => { setCreateFile(file); return false }}
              maxCount={1}
              accept=".docx"
            >
              <Button icon={<UploadOutlined />}>选择文件</Button>
            </Upload>
            {createFile && <div style={{ marginTop: 8, color: '#52c41a' }}>已选择: {createFile.name}</div>}
          </Form.Item>
        </Form>
      </Modal>

      <Modal
        title="模板预览"
        open={previewOpen}
        onCancel={() => { setPreviewOpen(false); setPreviewUrl(null) }}
        footer={null}
        width={900}
      >
        {previewLoading ? (
          <div style={{ textAlign: 'center', padding: 40 }}>加载中...</div>
        ) : previewUrl ? (
          <iframe src={previewUrl} style={{ width: '100%', height: 600, border: 'none' }} />
        ) : null}
      </Modal>
    </div>
  )
}

export default ContractTemplates

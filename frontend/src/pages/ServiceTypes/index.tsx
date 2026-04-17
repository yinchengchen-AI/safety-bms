import React, { useState } from 'react'
import { Table, Button, Space, Input, Select, Tag, message, Drawer, Form, Popconfirm } from 'antd'
import { PlusOutlined } from '@ant-design/icons'
import { PermissionButton } from '@/components/auth/PermissionButton'
import {
  useListServiceTypesQuery,
  useCreateServiceTypeMutation,
  useUpdateServiceTypeMutation,
  useDeleteServiceTypeMutation,
} from '@/store/api/serviceTypesApi'
import type { ServiceTypeItem } from '@/store/api/serviceTypesApi'
import { formatDateTime } from '@/utils/constants'

const ServiceTypes: React.FC = () => {
  const [page, setPage] = useState(1)
  const [keyword, setKeyword] = useState('')
  const [isActive, setIsActive] = useState<boolean | undefined>(undefined)
  const [drawerOpen, setDrawerOpen] = useState(false)
  const [editingId, setEditingId] = useState<number | null>(null)
  const [form] = Form.useForm()

  const { data, isLoading } = useListServiceTypesQuery({
    page,
    page_size: 20,
    is_active: isActive,
  })
  const [createServiceType, { isLoading: creating }] = useCreateServiceTypeMutation()
  const [updateServiceType, { isLoading: updating }] = useUpdateServiceTypeMutation()
  const [deleteServiceType] = useDeleteServiceTypeMutation()

  const filteredItems = React.useMemo(() => {
    if (!data?.items) return []
    if (!keyword.trim()) return data.items
    const k = keyword.trim().toLowerCase()
    return data.items.filter(
      (item) => item.name.toLowerCase().includes(k) || item.code.toLowerCase().includes(k)
    )
  }, [data, keyword])

  const handleOpenCreate = () => {
    setEditingId(null)
    form.resetFields()
    form.setFieldsValue({ is_active: true })
    setDrawerOpen(true)
  }

  const handleOpenEdit = (record: ServiceTypeItem) => {
    setEditingId(record.id)
    form.setFieldsValue({
      code: record.code,
      name: record.name,
      default_price: record.default_price,
      standard_duration_days: record.standard_duration_days,
      qualification_requirements: record.qualification_requirements,
      is_active: record.is_active,
    })
    setDrawerOpen(true)
  }

  const handleSubmit = async (values: any) => {
    try {
      if (editingId) {
        await updateServiceType({ id: editingId, data: values }).unwrap()
        message.success('更新成功')
      } else {
        await createServiceType(values).unwrap()
        message.success('创建成功')
      }
      setDrawerOpen(false)
      form.resetFields()
    } catch (err: any) {
      message.error(err?.data?.detail || '操作失败')
    }
  }

  const handleDelete = async (record: ServiceTypeItem) => {
    try {
      await deleteServiceType(record.id).unwrap()
      message.success('删除成功')
    } catch (err: any) {
      message.error(err?.data?.detail || '删除失败')
    }
  }

  const columns = [
    { title: '编码', dataIndex: 'code', key: 'code', width: 140 },
    { title: '名称', dataIndex: 'name', key: 'name' },
    {
      title: '默认价格',
      dataIndex: 'default_price',
      key: 'default_price',
      width: 120,
      render: (v?: number) => (v != null ? `¥${v}` : '-'),
    },
    {
      title: '标准工期(天)',
      dataIndex: 'standard_duration_days',
      key: 'standard_duration_days',
      width: 120,
      render: (v?: number) => v ?? '-',
    },
    {
      title: '状态',
      dataIndex: 'is_active',
      key: 'is_active',
      width: 100,
      render: (v: boolean) =>
        v ? <Tag color="success">启用</Tag> : <Tag color="default">停用</Tag>,
    },
    { title: '创建时间', dataIndex: 'created_at', key: 'created_at', width: 180, render: (v: string) => formatDateTime(v) },
    {
      title: '操作',
      key: 'action',
      width: 160,
      render: (_: any, r: ServiceTypeItem) => (
        <Space>
          <PermissionButton permission="service:update" type="link" size="small" onClick={() => handleOpenEdit(r)}>
            编辑
          </PermissionButton>
          <Popconfirm title="确认删除？" onConfirm={() => handleDelete(r)}>
            <PermissionButton permission="service:delete" type="link" danger size="small">
              删除
            </PermissionButton>
          </Popconfirm>
        </Space>
      ),
    },
  ]

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 16 }}>
        <Space>
          <Input.Search
            placeholder="搜索编码或名称"
            onSearch={setKeyword}
            style={{ width: 240 }}
            allowClear
          />
          <Select
            placeholder="状态"
            allowClear
            style={{ width: 120 }}
            onChange={(v) => setIsActive(v)}
            options={[
              { value: true, label: '启用' },
              { value: false, label: '停用' },
            ]}
          />
        </Space>
        <PermissionButton
          permission="service:create"
          type="primary"
          icon={<PlusOutlined />}
          onClick={handleOpenCreate}
        >
          新建服务类型
        </PermissionButton>
      </div>

      <Table
        rowKey="id"
        columns={columns}
        dataSource={filteredItems}
        loading={isLoading}
        pagination={{
          current: page,
          pageSize: 20,
          total: data?.total,
          onChange: setPage,
          showTotal: (t) => `共 ${t} 条`,
        }}
      />

      <Drawer
        title={editingId ? '编辑服务类型' : '新建服务类型'}
        open={drawerOpen}
        onClose={() => setDrawerOpen(false)}
        width={480}
        footer={
          <Space style={{ float: 'right' }}>
            <Button onClick={() => setDrawerOpen(false)}>取消</Button>
            <Button type="primary" loading={creating || updating} onClick={() => form.submit()}>
              保存
            </Button>
          </Space>
        }
      >
        <Form form={form} layout="vertical" onFinish={handleSubmit}>
          <Form.Item name="code" label="编码" rules={[{ required: true }]}>
            <Input placeholder="例如：evaluation" disabled={editingId !== null} />
          </Form.Item>
          <Form.Item name="name" label="名称" rules={[{ required: true }]}>
            <Input placeholder="例如：安全评价" />
          </Form.Item>
          <Form.Item name="default_price" label="默认价格">
            <Input type="number" placeholder="可选" />
          </Form.Item>
          <Form.Item name="standard_duration_days" label="标准工期(天)">
            <Input type="number" placeholder="可选" />
          </Form.Item>
          <Form.Item name="qualification_requirements" label="资质要求">
            <Input.TextArea rows={3} placeholder="可选" />
          </Form.Item>
          <Form.Item name="is_active" label="状态" rules={[{ required: true }]}>
            <Select
              options={[
                { value: true, label: '启用' },
                { value: false, label: '停用' },
              ]}
            />
          </Form.Item>
        </Form>
      </Drawer>
    </div>
  )
}

export default ServiceTypes

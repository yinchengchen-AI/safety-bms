import React, { useState, useCallback } from 'react'
import { Table, Button, Input, Space, Popconfirm, message, Drawer, Form, Typography } from 'antd'
import { PlusOutlined } from '@ant-design/icons'
import {
  useListPermissionsQuery,
  useCreatePermissionMutation,
  useUpdatePermissionMutation,
  useDeletePermissionMutation,
} from '@/store/api/permissionsApi'
import { PermissionButton } from '@/components/auth/PermissionButton'
import { formatDateTime } from '@/utils/constants'
import type { PermissionCreate, PermissionUpdate } from '@/store/api/permissionsApi'

const { Text } = Typography

const Permissions: React.FC = () => {
  const [page, setPage] = useState(1)
  const [keyword, setKeyword] = useState('')
  const [drawerOpen, setDrawerOpen] = useState(false)
  const [editingId, setEditingId] = useState<number | null>(null)
  const [form] = Form.useForm()

  const { data, isLoading } = useListPermissionsQuery({ page, page_size: 20, keyword: keyword || undefined })
  const [createPermission, { isLoading: creating }] = useCreatePermissionMutation()
  const [updatePermission, { isLoading: updating }] = useUpdatePermissionMutation()
  const [deletePermission] = useDeletePermissionMutation()

  const handleOpenCreate = useCallback(() => {
    setEditingId(null)
    form.resetFields()
    setDrawerOpen(true)
  }, [form])

  const handleOpenEdit = useCallback(
    (record: any) => {
      setEditingId(record.id)
      form.setFieldsValue({
        code: record.code,
        name: record.name,
        description: record.description,
      })
      setDrawerOpen(true)
    },
    [form]
  )

  const handleSubmit = async (values: any) => {
    try {
      if (editingId) {
        await updatePermission({ id: editingId, data: values as PermissionUpdate }).unwrap()
        message.success('权限更新成功')
      } else {
        await createPermission(values as PermissionCreate).unwrap()
        message.success('权限创建成功')
      }
      setDrawerOpen(false)
      form.resetFields()
    } catch (err: any) {
      message.error(err?.data?.detail || '操作失败')
    }
  }

  const handleDelete = async (id: number) => {
    try {
      await deletePermission(id).unwrap()
      message.success('删除成功')
    } catch (err: any) {
      message.error(err?.data?.detail || '删除失败')
    }
  }

  const columns = [
    { title: '权限码', dataIndex: 'code', key: 'code' },
    { title: '权限名称', dataIndex: 'name', key: 'name' },
    { title: '描述', dataIndex: 'description', key: 'description', ellipsis: true },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (v: string) => formatDateTime(v),
    },
    {
      title: '操作',
      key: 'action',
      render: (_: any, record: any) => (
        <Space>
          <PermissionButton permission="role:update" type="link" size="small" onClick={() => handleOpenEdit(record)}>
            编辑
          </PermissionButton>
          <Popconfirm title="确认删除？" onConfirm={() => handleDelete(record.id)}>
            <PermissionButton permission="role:delete" type="link" danger size="small">
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
        <Input.Search
          placeholder="搜索权限码或名称"
          onSearch={setKeyword}
          style={{ width: 280 }}
          allowClear
        />
        <PermissionButton permission="role:create" type="primary" icon={<PlusOutlined />} onClick={handleOpenCreate}>
          新建权限
        </PermissionButton>
      </div>

      <Table
        rowKey="id"
        columns={columns}
        dataSource={data?.items || []}
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
        title={editingId ? '编辑权限' : '新建权限'}
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
          <Form.Item name="code" label="权限码" rules={[{ required: true, message: '请输入权限码' }]}>
            <Input disabled={!!editingId} placeholder="如 customer:read" />
          </Form.Item>
          {editingId && (
            <Text type="secondary" style={{ display: 'block', marginTop: -12, marginBottom: 12 }}>
              权限码创建后不可修改
            </Text>
          )}
          <Form.Item name="name" label="权限名称" rules={[{ required: true, message: '请输入权限名称' }]}>
            <Input placeholder="如 客户查看" />
          </Form.Item>
          <Form.Item name="description" label="描述">
            <Input.TextArea rows={3} placeholder="权限用途说明" />
          </Form.Item>
        </Form>
      </Drawer>
    </div>
  )
}

export default Permissions

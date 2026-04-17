import React, { useState } from 'react'
import { Table, Button, Input, Space, Popconfirm, message, Drawer, Form, Radio, Tag, Checkbox } from 'antd'
import { PlusOutlined } from '@ant-design/icons'
import dayjs from 'dayjs'
import {
  useListRolesQuery,
  useCreateRoleMutation,
  useUpdateRoleMutation,
  useDeleteRoleMutation,
} from '@/store/api/rolesApi'
import { useListPermissionsQuery } from '@/store/api/permissionsApi'
import { downloadExport } from '@/utils/export'
import { PermissionButton } from '@/components/auth/PermissionButton'
import type { RoleCreate, RoleUpdate } from '@/store/api/rolesApi'

const dataScopeOptions = [
  { label: '全部数据', value: 'ALL' },
  { label: '本部门数据', value: 'DEPT' },
  { label: '仅本人数据', value: 'SELF' },
]

const permissionGroups = [
  { label: '客户管理', prefix: 'customer' },
  { label: '合同管理', prefix: 'contract' },
  { label: '服务管理', prefix: 'service' },
  { label: '开票管理', prefix: 'invoice' },
  { label: '收款管理', prefix: 'payment' },
  { label: '用户管理', prefix: 'user' },
  { label: '角色管理', prefix: 'role' },
  { label: '部门管理', prefix: 'department' },
  { label: '仪表盘', prefix: 'dashboard' },
  { label: '统计分析', prefix: 'analytics' },
  { label: '报表中心', prefix: 'report' },
]

const predefinedRoles = ['admin', 'sales', 'service', 'finance', 'viewer']

const Roles: React.FC = () => {
  const [page, setPage] = useState(1)
  const [keyword, setKeyword] = useState('')
  const [drawerOpen, setDrawerOpen] = useState(false)
  const [editingId, setEditingId] = useState<number | null>(null)
  const [form] = Form.useForm()

  const { data, isLoading } = useListRolesQuery({ page, page_size: 20, keyword })
  const { data: permissionsData } = useListPermissionsQuery({ page: 1, page_size: 200 })
  const [createRole, { isLoading: creating }] = useCreateRoleMutation()
  const [updateRole, { isLoading: updating }] = useUpdateRoleMutation()
  const [deleteRole] = useDeleteRoleMutation()

  const handleOpenCreate = () => {
    setEditingId(null)
    form.resetFields()
    form.setFieldsValue({ data_scope: 'ALL', permission_ids: [] })
    setDrawerOpen(true)
  }

  const handleOpenEdit = (record: any) => {
    setEditingId(record.id)
    form.setFieldsValue({
      name: record.name,
      description: record.description,
      data_scope: record.data_scope || 'ALL',
      permission_ids: record.permissions?.map((p: any) => p.id) || [],
    })
    setDrawerOpen(true)
  }

  const handleSubmit = async (values: any) => {
    const payload = {
      ...values,
      permission_ids: values.permission_ids || [],
    }
    try {
      if (editingId) {
        await updateRole({ id: editingId, data: payload as RoleUpdate }).unwrap()
        message.success('角色更新成功')
      } else {
        await createRole(payload as RoleCreate).unwrap()
        message.success('角色创建成功')
      }
      setDrawerOpen(false)
      form.resetFields()
    } catch (err: any) {
      message.error(err?.data?.detail || '操作失败')
    }
  }

  const handleDelete = async (id: number, name: string) => {
    if (predefinedRoles.includes(name)) {
      message.warning('预定义角色不允许删除')
      return
    }
    try {
      await deleteRole(id).unwrap()
      message.success('删除成功')
    } catch (err: any) {
      message.error(err?.data?.detail || '删除失败')
    }
  }

  const handleExport = async () => {
    const params = new URLSearchParams()
    if (keyword) params.append('keyword', keyword)
    try {
      await downloadExport(`/api/v1/roles/export?${params.toString()}`, `roles_${dayjs().format('YYYYMMDD_HHmmss')}.xlsx`)
    } catch (err: any) {
      message.error(err.message || '导出失败')
    }
  }

  const columns = [
    { title: '角色名称', dataIndex: 'name', key: 'name' },
    { title: '描述', dataIndex: 'description', key: 'description', ellipsis: true },
    { title: '数据范围', dataIndex: 'data_scope', key: 'data_scope', render: (v: string) => {
      const opt = dataScopeOptions.find((o) => o.value === v)
      return <Tag>{opt?.label || v}</Tag>
    }},
    { title: '操作', key: 'action', render: (_: any, r: any) => (
      <Space>
        <PermissionButton permission="role:update" type="link" size="small" onClick={() => handleOpenEdit(r)}>编辑</PermissionButton>
        <Popconfirm title="确认删除？" onConfirm={() => handleDelete(r.id, r.name)}>
          <PermissionButton permission="role:delete" type="link" danger size="small" disabled={predefinedRoles.includes(r.name)}>删除</PermissionButton>
        </Popconfirm>
      </Space>
    )},
  ]

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 16 }}>
        <Input.Search placeholder="搜索角色名称" onSearch={setKeyword} style={{ width: 240 }} allowClear />
        <Space>
          <PermissionButton permission="role:export" onClick={handleExport}>导出</PermissionButton>
          <PermissionButton permission="role:create" type="primary" icon={<PlusOutlined />} onClick={handleOpenCreate}>新建角色</PermissionButton>
        </Space>
      </div>

      <Table rowKey="id" columns={columns} dataSource={data?.items} loading={isLoading}
        pagination={{ current: page, pageSize: 20, total: data?.total, onChange: setPage, showTotal: (t) => `共 ${t} 条` }} />

      <Drawer title={editingId ? '编辑角色' : '新建角色'} open={drawerOpen} onClose={() => { setDrawerOpen(false) }} width={640} footer={
        <Space style={{ float: 'right' }}>
          <Button onClick={() => { setDrawerOpen(false) }}>取消</Button>
          <Button type="primary" loading={creating || updating} onClick={() => form.submit()}>保存</Button>
        </Space>
      }>
        <Form form={form} layout="vertical" onFinish={handleSubmit}>
          <Form.Item name="name" label="角色名称" rules={[{ required: true }]}><Input /></Form.Item>
          <Form.Item name="description" label="描述"><Input.TextArea rows={2} /></Form.Item>
          <Form.Item name="data_scope" label="数据范围" initialValue="ALL">
            <Radio.Group options={dataScopeOptions} />
          </Form.Item>
          <Form.Item name="permission_ids" label="权限配置">
            <div>
              {permissionGroups.map((g) => {
                const opts = permissionsData?.items?.filter((p) => p.code.startsWith(`${g.prefix}:`)).map((p) => ({ label: p.name, value: p.id })) || []
                if (opts.length === 0) return null
                return (
                  <div key={g.prefix} style={{ marginBottom: 16 }}>
                    <div style={{ fontWeight: 500, marginBottom: 6 }}>{g.label}</div>
                    <Checkbox.Group options={opts} />
                  </div>
                )
              })}
            </div>
          </Form.Item>
        </Form>
      </Drawer>
    </div>
  )
}

export default Roles

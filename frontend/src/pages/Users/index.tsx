import React, { useState, useMemo } from 'react'
import { Table, Button, Input, Space, Popconfirm, message, Drawer, Form, Tag, Switch, Select, TreeSelect } from 'antd'
import { PlusOutlined } from '@ant-design/icons'
import { PermissionButton } from '@/components/auth/PermissionButton'
import { useListUsersQuery, useCreateUserMutation, useDeleteUserMutation, useUpdateUserMutation } from '@/store/api/usersApi'
import { useListRolesQuery } from '@/store/api/rolesApi'
import { useListDepartmentsQuery } from '@/store/api/departmentsApi'
import type { User } from '@/types'
import dayjs from 'dayjs'
import { downloadExport } from '@/utils/export'

const roleColors: Record<string, string> = {
  admin: 'red', sales: 'blue', service: 'green', finance: 'orange', viewer: 'default',
}
const roleLabels: Record<string, string> = {
  admin: '管理员', sales: '销售', service: '服务', finance: '财务', viewer: '只读',
}

const Users: React.FC = () => {
  const [page, setPage] = useState(1)
  const [keyword, setKeyword] = useState('')
  const [departmentId, setDepartmentId] = useState<number | undefined>()
  const [createOpen, setCreateOpen] = useState(false)
  const [editOpen, setEditOpen] = useState(false)
  const [editingId, setEditingId] = useState<number | null>(null)
  const [form] = Form.useForm()
  const [editForm] = Form.useForm()

  const { data, isLoading } = useListUsersQuery({ page, page_size: 20, keyword, department_id: departmentId })
  const { data: rolesData } = useListRolesQuery()
  const roles = rolesData?.items
  const { data: departments } = useListDepartmentsQuery()
  const [createUser, { isLoading: creating }] = useCreateUserMutation()
  const [updateUser, { isLoading: updating }] = useUpdateUserMutation()
  const [deleteUser] = useDeleteUserMutation()

  const handleExport = async () => {
    const params = new URLSearchParams()
    if (keyword) params.append('keyword', keyword)
    if (departmentId) params.append('department_id', String(departmentId))
    try {
      await downloadExport(`/api/v1/users/export?${params.toString()}`, `users_${dayjs().format('YYYYMMDD_HHmmss')}.xlsx`)
    } catch (err: any) {
      message.error(err.message || '导出失败')
    }
  }

  const deptTreeData = useMemo(() => {
    if (!departments?.items) return []
    const build = (parentId: number | null): any[] =>
      departments.items
        .filter((d) => d.parent_id === parentId)
        .map((d) => ({
          title: d.name,
          value: d.id,
          key: d.id,
          children: build(d.id),
        }))
    return build(null)
  }, [departments])

  const deptMap = useMemo(() => {
    const map: Record<number, string> = {}
    departments?.items?.forEach((d) => { map[d.id] = d.name })
    return map
  }, [departments])

  const handleCreate = async (values: any) => {
    try {
      await createUser(values).unwrap()
      message.success('用户创建成功')
      setCreateOpen(false)
      form.resetFields()
    } catch (err: any) {
      message.error(err?.data?.detail || '创建失败')
    }
  }

  const handleEdit = (record: User & { department_id?: number }) => {
    setEditingId(record.id)
    editForm.setFieldsValue({
      full_name: record.full_name,
      phone: record.phone,
      email: record.email,
      is_active: record.is_active,
      role_ids: record.roles?.map((r) => r.id),
      department_id: record.department_id,
    })
    setEditOpen(true)
  }

  const handleUpdate = async (values: any) => {
    if (!editingId) return
    try {
      await updateUser({ id: editingId, data: values }).unwrap()
      message.success('用户更新成功')
      setEditOpen(false)
      editForm.resetFields()
      setEditingId(null)
    } catch (err: any) {
      message.error(err?.data?.detail || '更新失败')
    }
  }

  const columns = useMemo(() => [
    { title: '用户名', dataIndex: 'username', key: 'username' },
    { title: '姓名', dataIndex: 'full_name', key: 'full_name' },
    { title: '邮箱', dataIndex: 'email', key: 'email' },
    { title: '手机', dataIndex: 'phone', key: 'phone' },
    { title: '部门', dataIndex: 'department_id', key: 'department_id', render: (v?: number) => v ? deptMap[v] || '-' : '-' },
    { title: '角色', dataIndex: 'roles', key: 'roles', render: (rs: Array<{ name: string; display_name: string; id: number }>) => (
      <Space size={4} wrap>
        {rs?.map(r => <Tag key={r.id} color={roleColors[r.name] || 'default'}>{r.display_name || roleLabels[r.name] || r.name}</Tag>)}
      </Space>
    )},
    { title: '状态', dataIndex: 'is_active', key: 'is_active', render: (v: boolean) => <Tag color={v ? 'success' : 'error'}>{v ? '启用' : '禁用'}</Tag> },
    { title: '超管', dataIndex: 'is_superuser', key: 'is_superuser', render: (v: boolean) => v ? <Tag color="red">是</Tag> : null },
    { title: '操作', key: 'action', render: (_: any, r: User) => (
      <Space>
        <PermissionButton permission="user:update" type="link" size="small" onClick={() => handleEdit(r as any)}>编辑</PermissionButton>
        <Popconfirm title="确认删除该用户？" onConfirm={() => deleteUser(r.id)}>
          <PermissionButton permission="user:delete" type="link" danger size="small">删除</PermissionButton>
        </Popconfirm>
      </Space>
    )},
  ], [deleteUser, deptMap, handleEdit])

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 16 }}>
        <Space>
          <Input.Search placeholder="搜索用户名/姓名" onSearch={setKeyword} style={{ width: 240 }} allowClear />
          <TreeSelect
            style={{ width: 200 }}
            placeholder="选择部门"
            allowClear
            treeData={deptTreeData}
            onChange={(v) => setDepartmentId(v)}
          />
        </Space>
        <Space>
          <PermissionButton permission="user:export" onClick={handleExport}>导出</PermissionButton>
          <PermissionButton permission="user:create" type="primary" icon={<PlusOutlined />} onClick={() => setCreateOpen(true)}>新建用户</PermissionButton>
        </Space>
      </div>

      <Table rowKey="id" columns={columns} dataSource={data?.items} loading={isLoading}
        pagination={{ current: page, pageSize: 20, total: data?.total, onChange: setPage, showTotal: (t) => `共 ${t} 条` }} />

      <Drawer title="新建用户" open={createOpen} onClose={() => setCreateOpen(false)} width={480} footer={
        <Space style={{ float: 'right' }}>
          <Button onClick={() => setCreateOpen(false)}>取消</Button>
          <Button type="primary" loading={creating} onClick={() => form.submit()}>创建</Button>
        </Space>
      }>
        <Form form={form} layout="vertical" onFinish={handleCreate}>
          <Form.Item name="username" label="用户名" rules={[{ required: true }]}><Input /></Form.Item>
          <Form.Item name="full_name" label="姓名" rules={[{ required: true }]}><Input /></Form.Item>
          <Form.Item name="email" label="邮箱" rules={[{ type: 'email' }]}><Input /></Form.Item>
          <Form.Item name="phone" label="手机号"><Input /></Form.Item>
          <Form.Item name="password" label="密码" rules={[{ required: true, min: 8 }]}><Input.Password /></Form.Item>
          <Form.Item name="department_id" label="部门">
            <TreeSelect treeData={deptTreeData} allowClear placeholder="请选择部门" treeDefaultExpandAll />
          </Form.Item>
          <Form.Item name="role_ids" label="角色">
            <Select mode="multiple" options={roles?.map(r => ({ value: r.id, label: r.display_name || roleLabels[r.name] || r.name })) || []} />
          </Form.Item>
          <Form.Item name="is_active" label="启用" valuePropName="checked" initialValue={true}><Switch /></Form.Item>
        </Form>
      </Drawer>

      <Drawer title="编辑用户" open={editOpen} onClose={() => { setEditOpen(false); setEditingId(null) }} width={480} footer={
        <Space style={{ float: 'right' }}>
          <Button onClick={() => { setEditOpen(false); setEditingId(null) }}>取消</Button>
          <Button type="primary" loading={updating} onClick={() => editForm.submit()}>保存</Button>
        </Space>
      }>
        <Form form={editForm} layout="vertical" onFinish={handleUpdate}>
          <Form.Item name="full_name" label="姓名" rules={[{ required: true }]}><Input /></Form.Item>
          <Form.Item name="email" label="邮箱" rules={[{ type: 'email' }]}><Input /></Form.Item>
          <Form.Item name="phone" label="手机号"><Input /></Form.Item>
          <Form.Item name="department_id" label="部门">
            <TreeSelect treeData={deptTreeData} allowClear placeholder="请选择部门" treeDefaultExpandAll />
          </Form.Item>
          <Form.Item name="role_ids" label="角色">
            <Select mode="multiple" options={roles?.map(r => ({ value: r.id, label: r.display_name || roleLabels[r.name] || r.name })) || []} />
          </Form.Item>
          <Form.Item name="is_active" label="启用" valuePropName="checked"><Switch /></Form.Item>
        </Form>
      </Drawer>
    </div>
  )
}

export default Users

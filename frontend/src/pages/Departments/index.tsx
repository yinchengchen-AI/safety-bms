import React, { useState, useMemo } from 'react'
import { Table, Button, Input, Space, Popconfirm, message, Drawer, Form, TreeSelect } from 'antd'
import { PlusOutlined } from '@ant-design/icons'
import { PermissionButton } from '@/components/auth/PermissionButton'
import dayjs from 'dayjs'
import {
  useListDepartmentsQuery,
  useCreateDepartmentMutation,
  useUpdateDepartmentMutation,
  useDeleteDepartmentMutation,
} from '@/store/api/departmentsApi'
import { downloadExport } from '@/utils/export'
import type { Department, DepartmentCreate, DepartmentUpdate } from '@/store/api/departmentsApi'

const Departments: React.FC = () => {
  const [keyword, setKeyword] = useState('')
  const [drawerOpen, setDrawerOpen] = useState(false)
  const [editingId, setEditingId] = useState<number | null>(null)
  const [form] = Form.useForm()

  const { data, isLoading } = useListDepartmentsQuery()
  const [createDepartment, { isLoading: creating }] = useCreateDepartmentMutation()
  const [updateDepartment, { isLoading: updating }] = useUpdateDepartmentMutation()
  const [deleteDepartment] = useDeleteDepartmentMutation()

  const treeTableData = useMemo(() => {
    if (!data?.items) return []
    const items = keyword
      ? data.items.filter((d) => d.name.includes(keyword))
      : data.items
    const build = (parentId: number | null): any[] =>
      items
        .filter((d) => d.parent_id === parentId)
        .map((d) => ({
          ...d,
          children: build(d.id),
        }))
    return build(null)
  }, [data, keyword])

  const treeData = useMemo(() => {
    if (!data?.items) return []
    const build = (parentId: number | null): any[] =>
      data.items
        .filter((d) => d.parent_id === parentId)
        .map((d) => ({
          title: d.name,
          value: d.id,
          key: d.id,
          children: build(d.id),
        }))
    return build(null)
  }, [data])

  const handleOpenCreate = () => {
    setEditingId(null)
    form.resetFields()
    setDrawerOpen(true)
  }

  const handleOpenEdit = (record: Department) => {
    setEditingId(record.id)
    form.setFieldsValue({
      name: record.name,
      description: record.description,
      parent_id: record.parent_id,
    })
    setDrawerOpen(true)
  }

  const handleSubmit = async (values: any) => {
    try {
      if (editingId) {
        await updateDepartment({ id: editingId, data: values as DepartmentUpdate }).unwrap()
        message.success('部门更新成功')
      } else {
        await createDepartment(values as DepartmentCreate).unwrap()
        message.success('部门创建成功')
      }
      setDrawerOpen(false)
      form.resetFields()
    } catch (err: any) {
      message.error(err?.data?.detail || '操作失败')
    }
  }

  const handleDelete = async (record: Department) => {
    const hasChildren = data?.items?.some((d) => d.parent_id === record.id)
    if (hasChildren) {
      message.warning('请先删除子部门')
      return
    }
    try {
      await deleteDepartment(record.id).unwrap()
      message.success('删除成功')
    } catch (err: any) {
      message.error(err?.data?.detail || '删除失败')
    }
  }

  const handleExport = async () => {
    const params = new URLSearchParams()
    if (keyword) params.append('keyword', keyword)
    try {
      await downloadExport(`/api/v1/departments/export?${params.toString()}`, `departments_${dayjs().format('YYYYMMDD_HHmmss')}.xlsx`)
    } catch (err: any) {
      message.error(err.message || '导出失败')
    }
  }

  const columns = useMemo(
    () => [
      { title: '部门名称', dataIndex: 'name', key: 'name' },
      { title: '描述', dataIndex: 'description', key: 'description', ellipsis: true },
      {
        title: '操作',
        key: 'action',
        render: (_: any, r: Department) => (
          <Space>
            <PermissionButton permission="department:update" type="link" size="small" onClick={() => handleOpenEdit(r)}>
              编辑
            </PermissionButton>
            <Popconfirm title="确认删除？" onConfirm={() => handleDelete(r)}>
              <PermissionButton permission="department:delete" type="link" danger size="small">
                删除
              </PermissionButton>
            </Popconfirm>
          </Space>
        ),
      },
    ],
    [handleOpenEdit, handleDelete]
  )

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 16 }}>
        <Input.Search placeholder="搜索部门名称" onSearch={setKeyword} style={{ width: 240 }} allowClear />
        <Space>
          <PermissionButton permission="department:export" onClick={handleExport}>导出</PermissionButton>
          <PermissionButton permission="department:create" type="primary" icon={<PlusOutlined />} onClick={handleOpenCreate}>
            新建部门
          </PermissionButton>
        </Space>
      </div>

      <Table
        rowKey="id"
        columns={columns}
        dataSource={treeTableData}
        loading={isLoading}
        pagination={false}
        expandable={{ childrenColumnName: 'children', defaultExpandAllRows: true }}
      />

      <Drawer
        title={editingId ? '编辑部门' : '新建部门'}
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
          <Form.Item name="name" label="部门名称" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Form.Item name="description" label="描述">
            <Input.TextArea rows={2} />
          </Form.Item>
          <Form.Item name="parent_id" label="上级部门">
            <TreeSelect
              treeData={treeData}
              allowClear
              placeholder="请选择上级部门"
              treeDefaultExpandAll
              disabled={editingId !== null}
            />
          </Form.Item>
        </Form>
      </Drawer>
    </div>
  )
}

export default Departments

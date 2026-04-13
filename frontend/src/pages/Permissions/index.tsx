import React from 'react'
import { Table } from 'antd'
import { useListPermissionsQuery } from '@/store/api/permissionsApi'

const Permissions: React.FC = () => {
  const { data, isLoading } = useListPermissionsQuery({ page: 1, page_size: 200 })

  const columns = [
    { title: '权限码', dataIndex: 'code', key: 'code' },
    { title: '权限名称', dataIndex: 'name', key: 'name' },
    { title: '描述', dataIndex: 'description', key: 'description' },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (v: string) => v ? new Date(v).toLocaleString() : '-',
    },
  ]

  return (
    <div>
      <h2 style={{ marginBottom: 16 }}>权限管理</h2>
      <Table
        rowKey="id"
        columns={columns}
        dataSource={data?.items || []}
        loading={isLoading}
        pagination={false}
      />
    </div>
  )
}

export default Permissions

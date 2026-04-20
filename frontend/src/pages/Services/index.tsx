import React, { useState, useMemo } from 'react'
import { Table, Button, Input, Select, Tag, Space, message, Drawer, Form, DatePicker, Descriptions, Modal, Tabs, TableColumnsType, Upload, Popconfirm } from 'antd'
import type { UploadProps } from 'antd'
import { PlusOutlined, DeleteOutlined, EditOutlined, UploadOutlined, DownloadOutlined } from '@ant-design/icons'
import { useListServiceOrdersQuery, useCreateServiceOrderMutation, useUpdateServiceStatusMutation, useGetServiceOrderQuery, useUpdateServiceOrderMutation, useDeleteServiceOrderMutation, useCreateServiceItemMutation, useUpdateServiceItemMutation, useDeleteServiceItemMutation, useDeleteServiceReportMutation } from '@/store/api/servicesApi'
import { useListContractsQuery } from '@/store/api/contractsApi'
import { ServiceOrderStatusLabels, formatDateTime } from '@/utils/constants'
import type { ServiceOrder, ServiceOrderStatus, ServiceItem } from '@/types'
import dayjs from 'dayjs'
import type { Dayjs } from 'dayjs'
import { useListServiceTypesQuery } from '@/store/api/serviceTypesApi'

interface ServiceFormValues {
  order_no: string
  contract_id: number
  service_type: number
  title: string
  planned_start?: Dayjs
  planned_end?: Dayjs
  remark?: string
}

interface ItemFormValues {
  name: string
  description?: string
  quantity: number
  unit: string
  remark?: string
}

const statusColors: Record<ServiceOrderStatus, string> = {
  pending: 'default', in_progress: 'processing', completed: 'success', accepted: 'green',
}

const Services: React.FC = () => {
  const [page, setPage] = useState(1)
  const [keyword, setKeyword] = useState('')
  const [status, setStatus] = useState<ServiceOrderStatus | undefined>()
  const [createOpen, setCreateOpen] = useState(false)
  const [editOpen, setEditOpen] = useState(false)
  const [detailId, setDetailId] = useState<number | null>(null)
  const [form] = Form.useForm()
  const [editForm] = Form.useForm()

  const { data, isLoading, refetch } = useListServiceOrdersQuery({ page, page_size: 20, keyword, status })
  const { data: contractsData } = useListContractsQuery({ page: 1, page_size: 200 })
  const [createServiceOrder, { isLoading: creating }] = useCreateServiceOrderMutation()
  const [updateServiceOrder] = useUpdateServiceOrderMutation()
  const [deleteServiceOrder] = useDeleteServiceOrderMutation()
  const activeContracts = React.useMemo(() => {
    return contractsData?.items.filter(c => ['signed', 'executing', 'completed'].includes(c.status)) || []
  }, [contractsData])
  const { data: serviceTypesData } = useListServiceTypesQuery({ page_size: 200 })

  const serviceTypeMap = React.useMemo(() => {
    const map = new Map<number, string>()
    serviceTypesData?.items?.forEach((st) => map.set(st.id, st.name))
    return map
  }, [serviceTypesData])

  const serviceTypeOptions = React.useMemo(() => {
    return serviceTypesData?.items?.map((st) => ({ value: st.id, label: st.name })) || []
  }, [serviceTypesData])

  const handleCreate = async (values: ServiceFormValues) => {
    const payload = {
      ...values,
      planned_start: values.planned_start ? dayjs(values.planned_start).format('YYYY-MM-DD') : undefined,
      planned_end: values.planned_end ? dayjs(values.planned_end).format('YYYY-MM-DD') : undefined,
    }
    try {
      await createServiceOrder(payload).unwrap()
      message.success('服务工单创建成功')
      setCreateOpen(false)
      form.resetFields()
    } catch (err: any) {
      message.error(err?.data?.detail || '创建失败')
    }
  }

  const handleEdit = async (values: ServiceFormValues) => {
    if (!detailId) return
    const payload = {
      ...values,
      planned_start: values.planned_start ? dayjs(values.planned_start).format('YYYY-MM-DD') : undefined,
      planned_end: values.planned_end ? dayjs(values.planned_end).format('YYYY-MM-DD') : undefined,
    }
    try {
      await updateServiceOrder({ id: detailId, data: payload }).unwrap()
      message.success('服务工单更新成功')
      setEditOpen(false)
      refetch()
    } catch (err: any) {
      message.error(err?.data?.detail || '更新失败')
    }
  }

  const handleDelete = async (id: number) => {
    try {
      await deleteServiceOrder(id).unwrap()
      message.success('删除成功')
      refetch()
    } catch (err: any) {
      message.error(err?.data?.detail || '删除失败')
    }
  }

  const columns = useMemo(() => [
    { title: '工单编号', dataIndex: 'order_no', key: 'order_no', render: (no: string, r: ServiceOrder) => (
      <Button type="link" onClick={() => setDetailId(r.id)}>{no}</Button>
    )},
    { title: '服务类型', dataIndex: 'service_type', key: 'service_type', render: (s: number) => serviceTypeMap.get(s) || s },
    { title: '客户', dataIndex: 'customer_name', key: 'customer_name' },
    { title: '负责人', dataIndex: 'assignee_name', key: 'assignee_name' },
    { title: '状态', dataIndex: 'status', key: 'status', render: (s: ServiceOrderStatus) => (
      <Tag color={statusColors[s]}>{ServiceOrderStatusLabels[s]}</Tag>
    )},
    { title: '计划开始', dataIndex: 'planned_start', key: 'planned_start' },
    { title: '计划结束', dataIndex: 'planned_end', key: 'planned_end' },
    { title: '操作', key: 'action', render: (_: any, r: ServiceOrder) => (
      <Space>
        {(r.status === 'pending' || r.status === 'in_progress') && (
          <Button size="small" type="link" onClick={() => {
            editForm.setFieldsValue({
              order_no: r.order_no,
              contract_id: r.contract_id,
              service_type: r.service_type,
              title: r.title,
              planned_start: r.planned_start ? dayjs(r.planned_start) : undefined,
              planned_end: r.planned_end ? dayjs(r.planned_end) : undefined,
              remark: r.remark,
            })
            setEditOpen(true)
          }}>编辑</Button>
        )}
        {r.status === 'pending' && (
          <Popconfirm title="确定删除该工单？" onConfirm={() => handleDelete(r.id)}>
            <Button size="small" danger type="link">删除</Button>
          </Popconfirm>
        )}
      </Space>
    )},
  ], [editForm])

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 16 }}>
        <Space>
          <Input.Search placeholder="搜索工单编号" onSearch={setKeyword} style={{ width: 240 }} allowClear />
          <Select placeholder="工单状态" allowClear style={{ width: 120 }} onChange={setStatus}
            options={Object.entries(ServiceOrderStatusLabels).map(([v, l]) => ({ value: v, label: l }))} />
        </Space>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => setCreateOpen(true)}>新建工单</Button>
      </div>

      <Table rowKey="id" columns={columns} dataSource={data?.items} loading={isLoading}
        pagination={{ current: page, pageSize: 20, total: data?.total, onChange: setPage, showTotal: (t) => `共 ${t} 条` }} />

      <Drawer title="新建服务工单" open={createOpen} onClose={() => setCreateOpen(false)} width={640} footer={
        <Space style={{ float: 'right' }}>
          <Button onClick={() => setCreateOpen(false)}>取消</Button>
          <Button type="primary" loading={creating} onClick={() => form.submit()}>创建</Button>
        </Space>
      }>
        <Form form={form} layout="vertical" onFinish={handleCreate}>
          <Form.Item name="order_no" label="工单编号" rules={[{ required: true }]}><Input /></Form.Item>
          <Form.Item name="contract_id" label="关联合同" rules={[{ required: true }]}>
            <Select showSearch optionFilterProp="label"
              options={activeContracts.map(c => ({ value: c.id, label: `${c.contract_no} - ${c.title}` }))} />
          </Form.Item>
          <Form.Item name="service_type" label="服务类型" rules={[{ required: true }]}>
            <Select options={serviceTypeOptions} />
          </Form.Item>
          <Form.Item name="title" label="工单标题" rules={[{ required: true }]}><Input /></Form.Item>
          <Form.Item name="planned_start" label="计划开始日期"><DatePicker style={{ width: '100%' }} /></Form.Item>
          <Form.Item name="planned_end" label="计划结束日期"><DatePicker style={{ width: '100%' }} /></Form.Item>
          <Form.Item name="remark" label="备注"><Input.TextArea rows={3} /></Form.Item>
        </Form>
      </Drawer>

      <Drawer title="编辑服务工单" open={editOpen} onClose={() => setEditOpen(false)} width={640} footer={
        <Space style={{ float: 'right' }}>
          <Button onClick={() => setEditOpen(false)}>取消</Button>
          <Button type="primary" onClick={() => editForm.submit()}>保存</Button>
        </Space>
      }>
        <Form form={editForm} layout="vertical" onFinish={handleEdit}>
          <Form.Item name="order_no" label="工单编号" rules={[{ required: true }]}><Input /></Form.Item>
          <Form.Item name="contract_id" label="关联合同" rules={[{ required: true }]}>
            <Select showSearch optionFilterProp="label"
              options={activeContracts.map(c => ({ value: c.id, label: `${c.contract_no} - ${c.title}` }))} />
          </Form.Item>
          <Form.Item name="service_type" label="服务类型" rules={[{ required: true }]}>
            <Select options={serviceTypeOptions} />
          </Form.Item>
          <Form.Item name="title" label="工单标题" rules={[{ required: true }]}><Input /></Form.Item>
          <Form.Item name="planned_start" label="计划开始日期"><DatePicker style={{ width: '100%' }} /></Form.Item>
          <Form.Item name="planned_end" label="计划结束日期"><DatePicker style={{ width: '100%' }} /></Form.Item>
          <Form.Item name="remark" label="备注"><Input.TextArea rows={3} /></Form.Item>
        </Form>
      </Drawer>

      {detailId && <ServiceDetail id={detailId} onClose={() => setDetailId(null)} />}
    </div>
  )
}

const ServiceDetail: React.FC<{ id: number; onClose: () => void }> = ({ id, onClose }) => {
  const { data, refetch } = useGetServiceOrderQuery(id)
  const [updateStatus] = useUpdateServiceStatusMutation()
  const [createServiceItem] = useCreateServiceItemMutation()
  const [updateServiceItem] = useUpdateServiceItemMutation()
  const [deleteServiceItem] = useDeleteServiceItemMutation()
  const [deleteServiceReport] = useDeleteServiceReportMutation()
  const [itemModalOpen, setItemModalOpen] = useState(false)
  const [editingItem, setEditingItem] = useState<ServiceItem | null>(null)
  const [itemForm] = Form.useForm()
  const { data: serviceTypesData } = useListServiceTypesQuery({ page_size: 200 })
  const serviceTypeMap = React.useMemo(() => {
    const map = new Map<number, string>()
    serviceTypesData?.items?.forEach((st) => map.set(st.id, st.name))
    return map
  }, [serviceTypesData])

  if (!data) return null

  const handleStatusChange = async (newStatus: ServiceOrderStatus) => {
    try {
      await updateStatus({ id, status: newStatus }).unwrap()
      message.success('状态更新成功')
      refetch()
    } catch (err: any) {
      message.error(err?.data?.detail || '状态更新失败')
    }
  }

  const handleItemSubmit = async (values: ItemFormValues) => {
    try {
      if (editingItem) {
        await updateServiceItem({ orderId: id, itemId: editingItem.id, data: values }).unwrap()
        message.success('服务项更新成功')
      } else {
        await createServiceItem({ orderId: id, data: values }).unwrap()
        message.success('服务项添加成功')
      }
      setItemModalOpen(false)
      itemForm.resetFields()
      setEditingItem(null)
      refetch()
    } catch (err: any) {
      message.error(err?.data?.detail || '操作失败')
    }
  }

  const handleItemDelete = async (itemId: number) => {
    try {
      await deleteServiceItem({ orderId: id, itemId }).unwrap()
      message.success('删除成功')
      refetch()
    } catch (err: any) {
      message.error(err?.data?.detail || '删除失败')
    }
  }

  const handleReportDelete = async (reportId: number) => {
    try {
      await deleteServiceReport({ orderId: id, reportId }).unwrap()
      message.success('删除成功')
      refetch()
    } catch (err: any) {
      message.error(err?.data?.detail || '删除失败')
    }
  }

  const isLocked = data.status === 'completed' || data.status === 'accepted'

  const uploadProps: UploadProps = {
    name: 'file',
    action: `/api/v1/services/${id}/reports`,
    headers: { Authorization: `Bearer ${localStorage.getItem('access_token') || ''}` },
    showUploadList: false,
    customRequest: async (options: any) => {
      const { file, onSuccess, onError } = options
      try {
        const formData = new FormData()
        formData.append('file', file as File)
        const response = await fetch(`/api/v1/services/${id}/reports`, {
          method: 'POST',
          headers: { Authorization: `Bearer ${localStorage.getItem('access_token') || ''}` },
          body: formData,
        })
        let errorMsg = '上传失败'
        try {
          const data = await response.json()
          if (data.detail) {
            errorMsg = data.detail
          }
        } catch {
          if (response.status === 401) {
            errorMsg = '登录已过期，请重新登录'
          } else if (response.status === 403) {
            errorMsg = '没有上传权限'
          } else if (response.status === 413) {
            errorMsg = '文件过大，超过服务器限制'
          }
        }
        if (!response.ok) {
          message.error(errorMsg)
          onError?.(new Error(errorMsg))
          return
        }
        message.success('上传成功')
        refetch()
        onSuccess?.({})
      } catch (err) {
        message.error('上传失败，请检查网络连接')
        onError?.(err as Error)
      }
    },
  }

  const itemColumns: TableColumnsType<ServiceItem> = [
    { title: '名称', dataIndex: 'name', key: 'name' },
    { title: '描述', dataIndex: 'description', key: 'description', ellipsis: true },
    { title: '数量', dataIndex: 'quantity', key: 'quantity', width: 80 },
    { title: '单位', dataIndex: 'unit', key: 'unit', width: 80 },
    { title: '备注', dataIndex: 'remark', key: 'remark', ellipsis: true },
    { title: '操作', key: 'action', width: 120, render: (_, record) => (
      isLocked ? null : (
        <Space>
          <Button size="small" type="link" icon={<EditOutlined />} onClick={() => {
            setEditingItem(record)
            itemForm.setFieldsValue(record)
            setItemModalOpen(true)
          }}>编辑</Button>
          <Popconfirm title="确定删除？" onConfirm={() => handleItemDelete(record.id)}>
            <Button size="small" danger type="link" icon={<DeleteOutlined />}>删除</Button>
          </Popconfirm>
        </Space>
      )
    )},
  ]

  const tabItems = [
    {
      key: 'info',
      label: '基本信息',
      children: (
        <Descriptions column={2} bordered size="small">
          <Descriptions.Item label="工单编号">{data.order_no}</Descriptions.Item>
          <Descriptions.Item label="状态"><Tag color={statusColors[data.status]}>{ServiceOrderStatusLabels[data.status]}</Tag></Descriptions.Item>
          <Descriptions.Item label="工单标题" span={2}>{data.title}</Descriptions.Item>
          <Descriptions.Item label="服务类型">{serviceTypeMap.get(data.service_type) || data.service_type}</Descriptions.Item>
          <Descriptions.Item label="负责人">{data.assignee_name}</Descriptions.Item>
          <Descriptions.Item label="计划开始">{data.planned_start}</Descriptions.Item>
          <Descriptions.Item label="计划结束">{data.planned_end}</Descriptions.Item>
          <Descriptions.Item label="实际开始">{data.actual_start}</Descriptions.Item>
          <Descriptions.Item label="实际结束">{data.actual_end}</Descriptions.Item>
          <Descriptions.Item label="备注" span={2}>{data.remark}</Descriptions.Item>
        </Descriptions>
      ),
    },
    {
      key: 'items',
      label: `服务项 (${data.items.length})`,
      children: (
        <div>
          {!isLocked && (
            <div style={{ marginBottom: 16 }}>
              <Button type="primary" icon={<PlusOutlined />} onClick={() => {
                setEditingItem(null)
                itemForm.resetFields()
                setItemModalOpen(true)
              }}>添加服务项</Button>
            </div>
          )}
          <Table columns={itemColumns} dataSource={data.items} rowKey="id" size="small" pagination={false} />
        </div>
      ),
    },
    {
      key: 'reports',
      label: `服务报告 (${data.reports.length})`,
      children: (
        <div>
          {!isLocked && (
            <div style={{ marginBottom: 16 }}>
              <Upload {...uploadProps}>
                <Button icon={<UploadOutlined />}>上传报告</Button>
              </Upload>
              <div style={{ fontSize: 12, color: '#999', marginTop: 8 }}>支持 PDF、Word、WPS、Excel、图片格式，单文件不超过 20MB</div>
            </div>
          )}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            {data.reports.length === 0 && <div style={{ color: '#999', textAlign: 'center', padding: 20 }}>暂无服务报告</div>}
            {data.reports.map(report => (
              <div key={report.id} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '8px 12px', background: '#f5f5f5', borderRadius: 4 }}>
                <div>
                  <div style={{ fontWeight: 500 }}>{report.file_name}</div>
                  <div style={{ fontSize: 12, color: '#999' }}>{formatDateTime(report.created_at)} {report.file_size ? ` - ${(report.file_size / 1024).toFixed(1)}KB` : ''}</div>
                </div>
                <Space>
                  <Button size="small" icon={<DownloadOutlined />} onClick={() => window.open(report.file_url, '_blank')}>下载</Button>
                  {!isLocked && (
                    <Popconfirm title="确定删除？" onConfirm={() => handleReportDelete(report.id)}>
                      <Button size="small" danger icon={<DeleteOutlined />}>删除</Button>
                    </Popconfirm>
                  )}
                </Space>
              </div>
            ))}
          </div>
        </div>
      ),
    },
  ]

  const footerButtons = (
    <Space>
      {data.status === 'pending' && (
        <Button type="primary" onClick={() => handleStatusChange('in_progress')}>开始服务</Button>
      )}
      {data.status === 'in_progress' && (
        <Button type="primary" onClick={() => handleStatusChange('completed')}>完成服务</Button>
      )}
    </Space>
  )

  return (
    <Drawer title="工单详情" open width={720} onClose={onClose} footer={footerButtons}>
      <Tabs items={tabItems} />
      <Modal title={editingItem ? '编辑服务项' : '添加服务项'} open={itemModalOpen} onCancel={() => { setItemModalOpen(false); itemForm.resetFields(); setEditingItem(null) }} onOk={() => itemForm.submit()} destroyOnClose>
        <Form form={itemForm} layout="vertical" onFinish={handleItemSubmit}>
          <Form.Item name="name" label="名称" rules={[{ required: true }]}><Input /></Form.Item>
          <Form.Item name="description" label="描述"><Input.TextArea rows={2} /></Form.Item>
          <Space>
            <Form.Item name="quantity" label="数量" initialValue={1}><Input type="number" style={{ width: 100 }} /></Form.Item>
            <Form.Item name="unit" label="单位" initialValue="次"><Input style={{ width: 100 }} /></Form.Item>
          </Space>
          <Form.Item name="remark" label="备注"><Input.TextArea rows={2} /></Form.Item>
        </Form>
      </Modal>
    </Drawer>
  )
}

export default Services

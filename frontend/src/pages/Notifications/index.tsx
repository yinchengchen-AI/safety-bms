import React, { useState } from 'react'
import { List, Card, Badge, Button, Typography, Space, Tag, Empty, Tabs } from 'antd'
import {
  useListNotificationsQuery,
  useMarkAsReadMutation,
  useMarkAllAsReadMutation,
  useDeleteNotificationMutation,
  useClearAllNotificationsMutation,
} from '@/store/api/notificationsApi'
import dayjs from 'dayjs'

const { Text, Title } = Typography

type TabKey = 'all' | 'unread' | 'read'

const Notifications: React.FC = () => {
  const [activeTab, setActiveTab] = useState<TabKey>('all')
  const [page, setPage] = useState(1)
  const pageSize = 20

  const listParams: { page: number; page_size: number; is_read?: boolean } = { page, page_size: pageSize }
  if (activeTab === 'unread') listParams.is_read = false
  if (activeTab === 'read') listParams.is_read = true

  const { data, isLoading } = useListNotificationsQuery(listParams)
  const [markAsRead, { isLoading: marking }] = useMarkAsReadMutation()
  const [markAllAsRead, { isLoading: markingAll }] = useMarkAllAsReadMutation()
  const [deleteNotification, { isLoading: deleting }] = useDeleteNotificationMutation()
  const [clearAllNotifications, { isLoading: clearingAll }] = useClearAllNotificationsMutation()

  const handleMarkAsRead = async (id: number) => {
    try {
      await markAsRead(id).unwrap()
    } catch {
      // 错误由 RTK Query 全局处理，必要时可扩展
    }
  }

  const handleMarkAllAsRead = async () => {
    try {
      await markAllAsRead().unwrap()
    } catch {
      // 错误由 RTK Query 全局处理，必要时可扩展
    }
  }

  const handleDelete = async (id: number) => {
    try {
      await deleteNotification(id).unwrap()
    } catch {
      // 错误由 RTK Query 全局处理，必要时可扩展
    }
  }

  const handleClearAll = async () => {
    try {
      await clearAllNotifications().unwrap()
    } catch {
      // 错误由 RTK Query 全局处理，必要时可扩展
    }
  }

  const items = data?.items || []
  const hasItems = items.length > 0

  return (
    <Card>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <Title level={4} style={{ margin: 0 }}>通知中心</Title>
        <Space>
          {hasItems && (
            <Button danger loading={clearingAll} onClick={handleClearAll}>
              清空全部
            </Button>
          )}
          <Button type="primary" loading={markingAll} onClick={handleMarkAllAsRead}>
            全部标为已读
          </Button>
        </Space>
      </div>
      <Tabs
        activeKey={activeTab}
        onChange={(key) => {
          setActiveTab(key as TabKey)
          setPage(1)
        }}
        items={[
          { key: 'all', label: '全部' },
          { key: 'unread', label: '未读' },
          { key: 'read', label: '已读' },
        ]}
        style={{ marginBottom: 16 }}
      />
      <List
        loading={isLoading}
        dataSource={items}
        locale={{ emptyText: <Empty description="暂无通知" /> }}
        pagination={{
          current: page,
          pageSize: pageSize,
          total: data?.total || 0,
          onChange: setPage,
          showTotal: (total) => `共 ${total} 条`,
        }}
        renderItem={(item) => (
          <List.Item
            key={item.id}
            actions={[
              !item.is_read && (
                <Button key="read" size="small" loading={marking} onClick={() => handleMarkAsRead(item.id)}>
                  标为已读
                </Button>
              ),
              <Button key="delete" type="link" size="small" danger loading={deleting} onClick={() => handleDelete(item.id)}>
                删除
              </Button>,
            ]}
          >
            <List.Item.Meta
              title={
                <Space>
                  {!item.is_read && <Badge status="processing" />}
                  <Text strong={!item.is_read}>{item.title}</Text>
                  {item.is_read && <Tag color="default">已读</Tag>}
                </Space>
              }
              description={
                <div>
                  <div style={{ marginBottom: 8 }}>{item.content}</div>
                  <Text type="secondary">{dayjs(item.created_at).format('YYYY-MM-DD HH:mm')}</Text>
                </div>
              }
            />
          </List.Item>
        )}
      />
    </Card>
  )
}

export default Notifications

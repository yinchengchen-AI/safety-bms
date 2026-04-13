import React from 'react'
import { Layout, Menu, theme, Dropdown, Avatar, Space, Typography, Badge, Popover, List, Spin, Empty, Button } from 'antd'
import {
  LogoutOutlined,
  UserOutlined,
  MenuFoldOutlined,
  MenuUnfoldOutlined,
  BellOutlined,
} from '@ant-design/icons'
import { useNavigate, useLocation, Outlet } from 'react-router-dom'
import { useDispatch, useSelector } from 'react-redux'
import { toggleSider } from '@/store/slices/uiSlice'
import { logout, selectCurrentUser, selectUserPermissions } from '@/store/slices/authSlice'
import { useLogoutMutation } from '@/store/api/usersApi'
import { useGetUnreadCountQuery, useListNotificationsQuery, useMarkAsReadMutation } from '@/store/api/notificationsApi'
import { menuConfig } from '@/config/menuConfig'
import type { MenuItem } from '@/config/menuConfig'
import dayjs from 'dayjs'

const { Header, Sider, Content } = Layout

function toAntMenuItems(items: MenuItem[], hasPermission: (perm: string) => boolean): any[] {
  return items
    .filter((item) => {
      if (!item.requiredPermissions || item.requiredPermissions.length === 0) return true
      return item.requiredPermissions.some((p) => hasPermission(p))
    })
    .map((item) => {
      const Icon = item.icon as unknown as React.ComponentType<any>
      if (item.children && item.children.length > 0) {
        const children = toAntMenuItems(item.children, hasPermission)
        if (children.length === 0) return null
        return {
          key: item.key,
          icon: <Icon />,
          label: item.label,
          children,
        }
      }
      return {
        key: item.key,
        icon: <Icon />,
        label: item.label,
      }
    })
    .filter(Boolean)
}

const AppLayout: React.FC = () => {
  const navigate = useNavigate()
  const location = useLocation()
  const dispatch = useDispatch()
  const collapsed = useSelector((state: { ui: { siderCollapsed: boolean } }) => state.ui.siderCollapsed)
  const currentUser = useSelector(selectCurrentUser)
  const permissions = useSelector(selectUserPermissions)
  const [doLogout] = useLogoutMutation()
  const { data: unreadData } = useGetUnreadCountQuery()
  const { data: notificationsData, isLoading: notificationsLoading } = useListNotificationsQuery({ page: 1, page_size: 5, is_read: false })
  const [markAsRead] = useMarkAsReadMutation()
  const { token } = theme.useToken()

  const siderWidth = collapsed ? 80 : 200

  const hasPermission = React.useCallback(
    (perm: string) => {
      if (currentUser?.is_superuser) return true
      return permissions.includes(perm)
    },
    [currentUser, permissions]
  )

  const antMenuItems = React.useMemo(() => toAntMenuItems(menuConfig, hasPermission), [hasPermission])

  const handleLogout = async () => {
    try {
      await doLogout().unwrap()
    } catch (err: any) {
      console.error('Logout failed:', err)
    }
    dispatch(logout())
    navigate('/login')
  }

  const userMenuItems = [
    { key: 'profile', icon: <UserOutlined />, label: '个人信息' },
    { type: 'divider' as const },
    { key: 'logout', icon: <LogoutOutlined />, label: '退出登录', danger: true },
  ]

  const unreadCount = unreadData?.count || 0

  const handleMarkAsRead = async (id: number, e: React.MouseEvent) => {
    e.stopPropagation()
    try {
      await markAsRead(id).unwrap()
    } catch {
      // 错误由 RTK Query 全局处理
    }
  }

  const notificationItems = notificationsData?.items || []

  const bellContent = (
    <div style={{ width: 320 }}>
      <Spin spinning={notificationsLoading}>
        {notificationItems.length === 0 ? (
          <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="暂无新通知" style={{ margin: '16px 0' }} />
        ) : (
          <List
            size="small"
            dataSource={notificationItems}
            renderItem={(item) => (
              <List.Item
                style={{ padding: '8px 12px', cursor: 'pointer' }}
                onClick={() => navigate('/notifications')}
                actions={[
                  <Button
                    key="read"
                    type="link"
                    size="small"
                    style={{ padding: 0 }}
                    onClick={(e) => handleMarkAsRead(item.id, e)}
                  >
                    标为已读
                  </Button>,
                ]}
              >
                <div style={{ overflow: 'hidden' }}>
                  <div style={{ fontWeight: item.is_read ? 'normal' : 700, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                    {item.title}
                  </div>
                  <div style={{ color: token.colorTextSecondary, fontSize: 12, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                    {item.content}
                  </div>
                  <div style={{ color: token.colorTextDescription, fontSize: 12, marginTop: 2 }}>
                    {dayjs(item.created_at).format('YYYY-MM-DD HH:mm')}
                  </div>
                </div>
              </List.Item>
            )}
          />
        )}
        <div
          style={{
            textAlign: 'center',
            padding: '8px 12px',
            borderTop: `1px solid ${token.colorBorderSecondary}`,
            cursor: 'pointer',
            color: token.colorPrimary,
            fontSize: 13,
          }}
          onClick={() => navigate('/notifications')}
        >
          查看全部通知
        </div>
      </Spin>
    </div>
  )

  const selectedKeys = ['/' + location.pathname.split('/')[1]]

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider
        collapsible
        collapsed={collapsed}
        trigger={null}
        style={{
          position: 'fixed',
          left: 0,
          top: 0,
          bottom: 0,
          zIndex: 100,
          background: token.colorBgContainer,
          borderRight: `1px solid ${token.colorBorderSecondary}`,
        }}
      >
        <div style={{ height: 64, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '0 16px' }}>
          <div style={{ width: 28, height: 28, borderRadius: 4, background: token.colorPrimary, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <span style={{ color: '#fff', fontWeight: 700 }}>安</span>
          </div>
          {!collapsed && (
            <Typography.Text strong style={{ marginLeft: 8, fontSize: 14 }}>
              安全生产BMS
            </Typography.Text>
          )}
        </div>
        <Menu
          mode="inline"
          selectedKeys={selectedKeys}
          defaultOpenKeys={['system']}
          items={antMenuItems}
          onClick={({ key }) => navigate(key)}
          style={{ borderRight: 0, height: 'calc(100vh - 64px)', overflow: 'auto' }}
        />
      </Sider>

      <Layout style={{ marginLeft: siderWidth }}>
        <Header
          style={{
            position: 'fixed',
            top: 0,
            left: siderWidth,
            right: 0,
            zIndex: 99,
            height: 64,
            padding: '0 24px',
            background: token.colorBgContainer,
            borderBottom: `1px solid ${token.colorBorderSecondary}`,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
          }}
        >
          {React.createElement(collapsed ? MenuUnfoldOutlined : MenuFoldOutlined, {
            onClick: () => dispatch(toggleSider()),
            style: { fontSize: 18, cursor: 'pointer' },
          })}

          <Space size={16}>
            <Popover placement="bottomRight" title="通知" content={bellContent} trigger="click">
              <Badge count={unreadCount} size="small" offset={[0, 2]}>
                <BellOutlined style={{ fontSize: 18, cursor: 'pointer' }} />
              </Badge>
            </Popover>
            <Dropdown
              menu={{
                items: userMenuItems,
                onClick: ({ key }) => {
                  if (key === 'logout') handleLogout()
                  if (key === 'profile') navigate('/profile')
                },
              }}
            >
              <Space style={{ cursor: 'pointer' }}>
                <Avatar icon={<UserOutlined />} src={currentUser?.avatar_url} />
                <Typography.Text>{currentUser?.full_name || currentUser?.username}</Typography.Text>
              </Space>
            </Dropdown>
          </Space>
        </Header>

        <Content
          style={{
            marginTop: 64,
            padding: 24,
            background: token.colorBgContainer,
            minHeight: 'calc(100vh - 64px)',
            overflow: 'auto',
          }}
        >
          <Outlet />
        </Content>
      </Layout>
    </Layout>
  )
}

export default AppLayout

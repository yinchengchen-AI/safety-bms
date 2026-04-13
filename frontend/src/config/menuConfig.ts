import type { ComponentType } from 'react'
import type { AntdIconProps } from '@ant-design/icons/lib/components/AntdIcon'
import {
  DashboardOutlined,
  TeamOutlined,
  FileTextOutlined,
  ToolOutlined,
  InboxOutlined,
  DollarOutlined,
  UserOutlined,
  SafetyOutlined,
  SettingOutlined,
  ApartmentOutlined,
} from '@ant-design/icons'

export interface MenuItem {
  key: string
  label: string
  icon: ComponentType<AntdIconProps>
  path?: string
  requiredPermissions?: string[]
  children?: MenuItem[]
}

export const menuConfig: MenuItem[] = [
  { key: '/', icon: DashboardOutlined, label: '仪表盘', path: '/', requiredPermissions: ['dashboard:read'] },
  { key: '/customers', icon: TeamOutlined, label: '客户管理', path: '/customers', requiredPermissions: ['customer:read'] },
  { key: '/contracts', icon: FileTextOutlined, label: '合同管理', path: '/contracts', requiredPermissions: ['contract:read'] },
  { key: '/contract-templates', icon: FileTextOutlined, label: '合同模板', path: '/contract-templates', requiredPermissions: ['contract:read'] },
  { key: '/services', icon: ToolOutlined, label: '服务管理', path: '/services', requiredPermissions: ['service:read'] },
  { key: '/invoices', icon: InboxOutlined, label: '开票管理', path: '/invoices', requiredPermissions: ['invoice:read'] },
  { key: '/payments', icon: DollarOutlined, label: '收款管理', path: '/payments', requiredPermissions: ['payment:read'] },
  {
    key: 'system',
    icon: SettingOutlined,
    label: '系统管理',
    children: [
      { key: '/users', icon: UserOutlined, label: '用户管理', path: '/users', requiredPermissions: ['user:read'] },
      { key: '/roles', icon: SafetyOutlined, label: '角色管理', path: '/roles', requiredPermissions: ['role:read'] },
      { key: '/departments', icon: ApartmentOutlined, label: '部门管理', path: '/departments', requiredPermissions: ['department:read'] },
      { key: '/permissions', icon: SafetyOutlined, label: '权限管理', path: '/permissions', requiredPermissions: ['role:read'] },
    ],
  },
]

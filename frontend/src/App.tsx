import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { ConfigProvider, theme } from 'antd'
import zhCN from 'antd/locale/zh_CN'
import dayjs from 'dayjs'
import 'dayjs/locale/zh-cn'

import AppLayout from '@/components/layout/AppLayout'
import PrivateRoute from '@/components/auth/PrivateRoute'
import AuthInitializer from '@/components/auth/AuthInitializer'
import ErrorBoundary from '@/components/common/ErrorBoundary'
import Login from '@/pages/Login'
import Dashboard from '@/pages/Dashboard'
import Analytics from '@/pages/Analytics'
import Customers from '@/pages/Customers'
import Contracts from '@/pages/Contracts'
import ContractTemplates from '@/pages/ContractTemplates'
import ServiceTypes from '@/pages/ServiceTypes'
import Services from '@/pages/Services'
import Invoices from '@/pages/Invoices'
import Payments from '@/pages/Payments'
import Users from '@/pages/Users'
import Roles from '@/pages/Roles'
import Permissions from '@/pages/Permissions'
import Departments from '@/pages/Departments'
import Profile from '@/pages/Profile'
import Notifications from '@/pages/Notifications'

dayjs.locale('zh-cn')

const App = () => {
  return (
    <ConfigProvider locale={zhCN} theme={{ algorithm: theme.defaultAlgorithm }}>
      <BrowserRouter>
        <AuthInitializer>
          <ErrorBoundary>
            <Routes>
              <Route path="/login" element={<Login />} />
              <Route element={<PrivateRoute />}>
                <Route element={<AppLayout />}>
                  <Route path="/" element={<Dashboard />} />
                  <Route path="/customers/*" element={<Customers />} />
                  <Route path="/contracts/*" element={<Contracts />} />
                  <Route path="/contract-templates/*" element={<ContractTemplates />} />
                  <Route path="/service-types/*" element={<ServiceTypes />} />
                  <Route path="/services/*" element={<Services />} />
                  <Route path="/invoices/*" element={<Invoices />} />
                  <Route path="/payments/*" element={<Payments />} />
                  <Route path="/profile" element={<Profile />} />
                  <Route path="/notifications" element={<Notifications />} />
                </Route>
              </Route>
              <Route element={<PrivateRoute requiredPermissions={['analytics:read']} />}>
                <Route element={<AppLayout />}>
                  <Route path="/analytics/*" element={<Analytics />} />
                </Route>
              </Route>
              <Route element={<PrivateRoute requiredPermissions={['user:read']} />}>
                <Route element={<AppLayout />}>
                  <Route path="/users/*" element={<Users />} />
                </Route>
              </Route>
              <Route element={<PrivateRoute requiredPermissions={['role:read']} />}>
                <Route element={<AppLayout />}>
                  <Route path="/roles/*" element={<Roles />} />
                  <Route path="/permissions" element={<Permissions />} />
                </Route>
              </Route>
              <Route element={<PrivateRoute requiredPermissions={['department:read']} />}>
                <Route element={<AppLayout />}>
                  <Route path="/departments/*" element={<Departments />} />
                </Route>
              </Route>
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </ErrorBoundary>
        </AuthInitializer>
      </BrowserRouter>
    </ConfigProvider>
  )
}

export default App

import { Suspense, lazy } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { ConfigProvider, theme, Spin } from 'antd'
import zhCN from 'antd/locale/zh_CN'
import dayjs from 'dayjs'
import 'dayjs/locale/zh-cn'

import AppLayout from '@/components/layout/AppLayout'
import PrivateRoute from '@/components/auth/PrivateRoute'
import AuthInitializer from '@/components/auth/AuthInitializer'
import ErrorBoundary from '@/components/common/ErrorBoundary'
import Login from '@/pages/Login'

const Dashboard = lazy(() => import('@/pages/Dashboard'))
const Analytics = lazy(() => import('@/pages/Analytics'))
const Customers = lazy(() => import('@/pages/Customers'))
const Contracts = lazy(() => import('@/pages/Contracts'))
const ContractTemplates = lazy(() => import('@/pages/ContractTemplates'))
const ServiceTypes = lazy(() => import('@/pages/ServiceTypes'))
const Services = lazy(() => import('@/pages/Services'))
const Invoices = lazy(() => import('@/pages/Invoices'))
const Payments = lazy(() => import('@/pages/Payments'))
const Users = lazy(() => import('@/pages/Users'))
const Roles = lazy(() => import('@/pages/Roles'))
const Permissions = lazy(() => import('@/pages/Permissions'))
const Departments = lazy(() => import('@/pages/Departments'))
const Profile = lazy(() => import('@/pages/Profile'))
const Notifications = lazy(() => import('@/pages/Notifications'))
const Reports = lazy(() => import('@/pages/Reports'))

dayjs.locale('zh-cn')

const PageLoading = () => (
  <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
    <Spin size="large" tip="加载中..." />
  </div>
)

const App = () => {
  return (
    <ConfigProvider locale={zhCN} theme={{ algorithm: theme.defaultAlgorithm }}>
      <BrowserRouter>
        <AuthInitializer>
          <ErrorBoundary>
            <Suspense fallback={<PageLoading />}>
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
                <Route element={<PrivateRoute requiredPermissions={['report:read']} />}>
                  <Route element={<AppLayout />}>
                    <Route path="/reports/*" element={<Reports />} />
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
            </Suspense>
          </ErrorBoundary>
        </AuthInitializer>
      </BrowserRouter>
    </ConfigProvider>
  )
}

export default App

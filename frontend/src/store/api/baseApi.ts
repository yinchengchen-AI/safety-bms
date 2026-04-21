import { createApi, fetchBaseQuery } from '@reduxjs/toolkit/query/react'

const env = (window as any).__ENV__ || {}

export const baseApi = createApi({
  reducerPath: 'api',
  baseQuery: fetchBaseQuery({
    baseUrl: env.API_BASE_URL || '/api/v1',
    credentials: 'include',
  }),
  tagTypes: ['User', 'Customer', 'Contract', 'ContractTemplate', 'Service', 'ServiceType', 'Invoice', 'Payment', 'Dashboard', 'Analytics', 'Report', 'Role', 'Department', 'Notification', 'Permission'],
  endpoints: () => ({}),
})

import { createApi, fetchBaseQuery } from '@reduxjs/toolkit/query/react'

export const baseApi = createApi({
  reducerPath: 'api',
  baseQuery: fetchBaseQuery({
    baseUrl: '/api/v1',
    credentials: 'include',
  }),
  tagTypes: ['User', 'Customer', 'Contract', 'ContractTemplate', 'Service', 'ServiceType', 'Invoice', 'Payment', 'Dashboard', 'Analytics', 'Report', 'Role', 'Department', 'Notification', 'Permission'],
  endpoints: () => ({}),
})

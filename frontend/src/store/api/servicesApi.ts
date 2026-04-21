import { baseApi } from './baseApi'
import type { ServiceOrder, ServiceOrderCreate, PageResponse, ServiceOrderStatus, ServiceItem, ServiceItemUpdate } from '@/types'

export const servicesApi = baseApi.injectEndpoints({
  endpoints: (builder) => ({
    listServiceOrders: builder.query<PageResponse<ServiceOrder>, { page?: number; page_size?: number; contract_id?: number; customer_id?: number; assignee_id?: number; status?: ServiceOrderStatus; keyword?: string }>({
      query: (params) => ({ url: '/services', params }),
      providesTags: ['Service'],
    }),
    getServiceOrder: builder.query<ServiceOrder, number>({
      query: (id) => `/services/${id}`,
      providesTags: (_, __, id) => [{ type: 'Service', id }],
    }),
    createServiceOrder: builder.mutation<ServiceOrder, ServiceOrderCreate>({
      query: (body) => ({ url: '/services', method: 'POST', body }),
      invalidatesTags: ['Service'],
    }),
    updateServiceOrder: builder.mutation<ServiceOrder, { id: number; data: Partial<ServiceOrderCreate> }>({
      query: ({ id, data }) => ({ url: `/services/${id}`, method: 'PATCH', body: data }),
      invalidatesTags: (_, __, { id }) => [{ type: 'Service', id }, 'Service'],
    }),
    updateServiceStatus: builder.mutation<ServiceOrder, { id: number; status: ServiceOrderStatus }>({
      query: ({ id, status }) => ({ url: `/services/${id}/status`, method: 'POST', body: { status } }),
      invalidatesTags: (_, __, { id }) => [{ type: 'Service', id }, 'Service'],
    }),
    deleteServiceOrder: builder.mutation<{ message: string }, number>({
      query: (id) => ({ url: `/services/${id}`, method: 'DELETE' }),
      invalidatesTags: ['Service'],
    }),
    createServiceItem: builder.mutation<ServiceItem, { orderId: number; data: Omit<ServiceItem, 'id' | 'order_id'> }>({
      query: ({ orderId, data }) => ({ url: `/services/${orderId}/items`, method: 'POST', body: data }),
      invalidatesTags: (_, __, { orderId }) => [{ type: 'Service', orderId }],
    }),
    updateServiceItem: builder.mutation<ServiceItem, { orderId: number; itemId: number; data: ServiceItemUpdate }>({
      query: ({ orderId, itemId, data }) => ({ url: `/services/${orderId}/items/${itemId}`, method: 'PATCH', body: data }),
      invalidatesTags: (_, __, { orderId }) => [{ type: 'Service', orderId }],
    }),
    deleteServiceItem: builder.mutation<{ message: string }, { orderId: number; itemId: number }>({
      query: ({ orderId, itemId }) => ({ url: `/services/${orderId}/items/${itemId}`, method: 'DELETE' }),
      invalidatesTags: (_, __, { orderId }) => [{ type: 'Service', orderId }],
    }),
    deleteServiceReport: builder.mutation<{ message: string }, { orderId: number; reportId: number }>({
      query: ({ orderId, reportId }) => ({ url: `/services/${orderId}/reports/${reportId}`, method: 'DELETE' }),
      invalidatesTags: (_, __, { orderId }) => [{ type: 'Service', orderId }],
    }),
  }),
})

export const {
  useListServiceOrdersQuery,
  useGetServiceOrderQuery,
  useCreateServiceOrderMutation,
  useUpdateServiceOrderMutation,
  useUpdateServiceStatusMutation,
  useDeleteServiceOrderMutation,
  useCreateServiceItemMutation,
  useUpdateServiceItemMutation,
  useDeleteServiceItemMutation,
  useDeleteServiceReportMutation,
} = servicesApi

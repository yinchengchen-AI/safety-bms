import { baseApi } from './baseApi'
import type { ServiceOrder, ServiceOrderCreate, PageResponse, ServiceOrderStatus } from '@/types'

export const servicesApi = baseApi.injectEndpoints({
  endpoints: (builder) => ({
    listServiceOrders: builder.query<PageResponse<ServiceOrder>, { page?: number; page_size?: number; contract_id?: number; assignee_id?: number; status?: ServiceOrderStatus; keyword?: string }>({
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
  }),
})

export const {
  useListServiceOrdersQuery,
  useGetServiceOrderQuery,
  useCreateServiceOrderMutation,
  useUpdateServiceOrderMutation,
  useUpdateServiceStatusMutation,
  useDeleteServiceOrderMutation,
} = servicesApi

import { baseApi } from './baseApi'
import type { PageResponse } from '@/types'

export interface ServiceTypeItem {
  id: number
  code: string
  name: string
  default_price?: number
  standard_duration_days?: number
  qualification_requirements?: string
  default_contract_template_id?: number
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface ServiceTypeCreate {
  code: string
  name: string
  default_price?: number
  standard_duration_days?: number
  qualification_requirements?: string
  default_contract_template_id?: number
  is_active?: boolean
}

export interface ServiceTypeUpdate {
  code?: string
  name?: string
  default_price?: number
  standard_duration_days?: number
  qualification_requirements?: string
  default_contract_template_id?: number
  is_active?: boolean
}

export const serviceTypesApi = baseApi.injectEndpoints({
  endpoints: (builder) => ({
    listServiceTypes: builder.query<PageResponse<ServiceTypeItem>, { page?: number; page_size?: number; is_active?: boolean } | void>({
      query: (params) => ({ url: '/service-types', params: params || undefined }),
      providesTags: ['ServiceType'],
    }),
    createServiceType: builder.mutation<ServiceTypeItem, ServiceTypeCreate>({
      query: (body) => ({ url: '/service-types', method: 'POST', body }),
      invalidatesTags: ['ServiceType'],
    }),
    updateServiceType: builder.mutation<ServiceTypeItem, { id: number; data: ServiceTypeUpdate }>({
      query: ({ id, data }) => ({ url: `/service-types/${id}`, method: 'PUT', body: data }),
      invalidatesTags: ['ServiceType'],
    }),
    deleteServiceType: builder.mutation<{ message: string }, number>({
      query: (id) => ({ url: `/service-types/${id}`, method: 'DELETE' }),
      invalidatesTags: ['ServiceType'],
    }),
  }),
})

export const {
  useListServiceTypesQuery,
  useCreateServiceTypeMutation,
  useUpdateServiceTypeMutation,
  useDeleteServiceTypeMutation,
} = serviceTypesApi

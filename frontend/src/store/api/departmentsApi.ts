import { baseApi } from './baseApi'
import type { PageResponse } from '@/types'

export interface Department {
  id: number
  name: string
  description?: string
  parent_id?: number | null
  created_at?: string
  updated_at?: string
}

export interface DepartmentCreate {
  name: string
  description?: string
  parent_id?: number | null
}

export interface DepartmentUpdate {
  name?: string
  description?: string
  parent_id?: number | null
}

export const departmentsApi = baseApi.injectEndpoints({
  endpoints: (builder) => ({
    listDepartments: builder.query<PageResponse<Department>, { page?: number; page_size?: number; keyword?: string } | void>({
      query: (params) => ({ url: '/departments', params: params || undefined }),
      providesTags: ['Department'],
    }),
    createDepartment: builder.mutation<Department, DepartmentCreate>({
      query: (body) => ({ url: '/departments', method: 'POST', body }),
      invalidatesTags: ['Department'],
    }),
    updateDepartment: builder.mutation<Department, { id: number; data: DepartmentUpdate }>({
      query: ({ id, data }) => ({ url: `/departments/${id}`, method: 'PATCH', body: data }),
      invalidatesTags: ['Department'],
    }),
    deleteDepartment: builder.mutation<{ message: string }, number>({
      query: (id) => ({ url: `/departments/${id}`, method: 'DELETE' }),
      invalidatesTags: ['Department'],
    }),
  }),
})

export const {
  useListDepartmentsQuery,
  useCreateDepartmentMutation,
  useUpdateDepartmentMutation,
  useDeleteDepartmentMutation,
} = departmentsApi

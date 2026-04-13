import { baseApi } from './baseApi'
import type { Role, PageResponse } from '@/types'

export interface RoleCreate {
  name: string
  description?: string
  permission_ids: number[]
  data_scope?: 'all' | 'department' | 'self'
}

export interface RoleUpdate {
  name?: string
  description?: string
  permission_ids?: number[]
  data_scope?: 'all' | 'department' | 'self'
}

export const rolesApi = baseApi.injectEndpoints({
  endpoints: (builder) => ({
    listRoles: builder.query<PageResponse<Role>, { page?: number; page_size?: number; keyword?: string } | void>({
      query: (params) => ({ url: '/roles', params: params || {} }),
      providesTags: ['Role'],
    }),
    getRole: builder.query<Role & { data_scope?: string }, number>({
      query: (id) => `/roles/${id}`,
      providesTags: (_, __, id) => [{ type: 'Role', id }],
    }),
    createRole: builder.mutation<Role, RoleCreate>({
      query: (body) => ({ url: '/roles', method: 'POST', body }),
      invalidatesTags: ['Role'],
    }),
    updateRole: builder.mutation<Role, { id: number; data: RoleUpdate }>({
      query: ({ id, data }) => ({ url: `/roles/${id}`, method: 'PUT', body: data }),
      invalidatesTags: (_, __, { id }) => [{ type: 'Role', id }, 'Role'],
    }),
    deleteRole: builder.mutation<{ message: string }, number>({
      query: (id) => ({ url: `/roles/${id}`, method: 'DELETE' }),
      invalidatesTags: ['Role'],
    }),
  }),
})

export const {
  useListRolesQuery,
  useGetRoleQuery,
  useCreateRoleMutation,
  useUpdateRoleMutation,
  useDeleteRoleMutation,
} = rolesApi

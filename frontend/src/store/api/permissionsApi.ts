import { baseApi } from './baseApi'

export interface Permission {
  id: number
  code: string
  name: string
  description?: string
  created_at: string
}

export interface PermissionCreate {
  code: string
  name: string
  description?: string
}

export interface PermissionUpdate {
  name?: string
  description?: string
}

export const permissionsApi = baseApi.injectEndpoints({
  endpoints: (builder) => ({
    listPermissions: builder.query<{ items: Permission[]; total: number }, { page?: number; page_size?: number; keyword?: string } | void>({
      query: (params) => ({ url: '/permissions', params: params || {} }),
      providesTags: ['Permission'],
    }),
    createPermission: builder.mutation<Permission, PermissionCreate>({
      query: (body) => ({ url: '/permissions', method: 'POST', body }),
      invalidatesTags: ['Permission'],
    }),
    updatePermission: builder.mutation<Permission, { id: number; data: PermissionUpdate }>({
      query: ({ id, data }) => ({ url: `/permissions/${id}`, method: 'PUT', body: data }),
      invalidatesTags: ['Permission'],
    }),
    deletePermission: builder.mutation<{ message: string }, number>({
      query: (id) => ({ url: `/permissions/${id}`, method: 'DELETE' }),
      invalidatesTags: ['Permission'],
    }),
  }),
})

export const {
  useListPermissionsQuery,
  useCreatePermissionMutation,
  useUpdatePermissionMutation,
  useDeletePermissionMutation,
} = permissionsApi

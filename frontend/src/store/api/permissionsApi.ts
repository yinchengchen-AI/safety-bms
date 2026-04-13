import { baseApi } from './baseApi'

export interface Permission {
  id: number
  code: string
  name: string
  description?: string
  created_at: string
}

export const permissionsApi = baseApi.injectEndpoints({
  endpoints: (builder) => ({
    listPermissions: builder.query<{ items: Permission[]; total: number }, { page?: number; page_size?: number } | void>({
      query: (params) => ({ url: '/permissions', params: params || {} }),
      providesTags: ['Permission'],
    }),
  }),
})

export const { useListPermissionsQuery } = permissionsApi

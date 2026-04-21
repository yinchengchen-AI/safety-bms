import { baseApi } from './baseApi'
import type { User, UserCreate, UserUpdate, Role, PageResponse, LoginRequest, TokenResponse } from '@/types'

export const usersApi = baseApi.injectEndpoints({
  endpoints: (builder) => ({
    // Auth
    login: builder.mutation<TokenResponse, LoginRequest>({
      query: (body) => ({ url: '/auth/login', method: 'POST', body }),
      invalidatesTags: ['User'],
    }),
    logout: builder.mutation<{ message: string }, void>({
      query: () => ({ url: '/auth/logout', method: 'POST' }),
    }),
    getMe: builder.query<User & { permissions?: string[] }, void>({
      query: () => '/auth/me',
      providesTags: ['User'],
    }),

    // Me
    updateMe: builder.mutation<User, Partial<Pick<User, 'full_name' | 'phone' | 'email' | 'avatar_url'>>>({
      query: (body) => ({ url: '/users/me', method: 'PATCH', body }),
      invalidatesTags: ['User'],
    }),
    uploadAvatar: builder.mutation<{ file_url: string; file_name: string; file_size: number }, File>({
      query: (file) => {
        const formData = new FormData()
        formData.append('file', file)
        return {
          url: '/users/me/avatar',
          method: 'POST',
          body: formData,
        }
      },
      invalidatesTags: ['User'],
    }),
    changePassword: builder.mutation<{ message: string }, { old_password: string; new_password: string }>({
      query: (body) => ({ url: '/users/me/password', method: 'POST', body }),
    }),

    // Users
    listUsers: builder.query<PageResponse<User>, { page?: number; page_size?: number; is_active?: boolean; keyword?: string; department_id?: number }>({
      query: (params) => ({ url: '/users', params }),
      providesTags: ['User'],
    }),
    createUser: builder.mutation<User, UserCreate>({
      query: (body) => ({ url: '/users', method: 'POST', body }),
      invalidatesTags: ['User'],
    }),
    updateUser: builder.mutation<User, { id: number; data: UserUpdate }>({
      query: ({ id, data }) => ({ url: `/users/${id}`, method: 'PATCH', body: data }),
      invalidatesTags: ['User'],
    }),
    deleteUser: builder.mutation<{ message: string }, number>({
      query: (id) => ({ url: `/users/${id}`, method: 'DELETE' }),
      invalidatesTags: ['User'],
    }),
    listRoles: builder.query<Role[], void>({
      query: () => '/users/roles',
      providesTags: ['Role'],
    }),
  }),
})

export const {
  useLoginMutation,
  useLogoutMutation,
  useGetMeQuery,
  useUpdateMeMutation,
  useUploadAvatarMutation,
  useChangePasswordMutation,
  useListUsersQuery,
  useCreateUserMutation,
  useUpdateUserMutation,
  useDeleteUserMutation,
  useListRolesQuery,
} = usersApi

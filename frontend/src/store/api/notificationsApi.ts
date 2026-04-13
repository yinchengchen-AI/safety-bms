import { baseApi } from './baseApi'
import type { PageResponse, Notification } from '@/types'

export const notificationsApi = baseApi.injectEndpoints({
  endpoints: (builder) => ({
    listNotifications: builder.query<PageResponse<Notification>, { page?: number; page_size?: number; is_read?: boolean }>({
      query: (params) => ({ url: '/notifications', params }),
      providesTags: ['Notification'],
    }),
    markAsRead: builder.mutation<{ message: string }, number>({
      query: (id) => ({ url: `/notifications/${id}/read`, method: 'POST' }),
      invalidatesTags: ['Notification'],
    }),
    markAllAsRead: builder.mutation<{ message: string }, void>({
      query: () => ({ url: '/notifications/read-all', method: 'POST' }),
      invalidatesTags: ['Notification'],
    }),
    getUnreadCount: builder.query<{ count: number }, void>({
      query: () => '/notifications/unread-count',
      providesTags: ['Notification'],
    }),
    deleteNotification: builder.mutation<{ message: string }, number>({
      query: (id) => ({ url: `/notifications/${id}`, method: 'DELETE' }),
      invalidatesTags: ['Notification'],
    }),
    clearAllNotifications: builder.mutation<{ message: string }, void>({
      query: () => ({ url: '/notifications/clear-all', method: 'DELETE' }),
      invalidatesTags: ['Notification'],
    }),
  }),
})

export const {
  useListNotificationsQuery,
  useMarkAsReadMutation,
  useMarkAllAsReadMutation,
  useGetUnreadCountQuery,
  useDeleteNotificationMutation,
  useClearAllNotificationsMutation,
} = notificationsApi

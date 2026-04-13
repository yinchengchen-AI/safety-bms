import { baseApi } from './baseApi'
import type { DashboardStats } from '@/types'

export const dashboardApi = baseApi.injectEndpoints({
  endpoints: (builder) => ({
    getDashboardStats: builder.query<DashboardStats, void>({
      query: () => '/dashboard/stats',
      providesTags: ['Dashboard'],
    }),
  }),
})

export const { useGetDashboardStatsQuery } = dashboardApi

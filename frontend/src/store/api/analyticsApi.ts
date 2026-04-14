import { baseApi } from './baseApi'
import type {
  AnalyticsDrilldownResponse,
  AnalyticsOverview,
  CustomerInsightsResponse,
  PerformanceRankingResponse,
  ReceivableAgingResponse,
  RevenueTrendResponse,
  ServiceEfficiencyResponse,
  ServiceType,
} from '@/types'

export interface AnalyticsQueryParams {
  date_from?: string
  date_to?: string
  service_type?: ServiceType
}

export interface AnalyticsDrilldownParams extends AnalyticsQueryParams {
  source: string
  period?: string
  series_type?: string
  group_value?: string
}

type CustomerInsightsQueryParams = {
  date_from?: string
  date_to?: string
}

const analyticsFetchArgs = (url: string, params?: AnalyticsQueryParams | AnalyticsDrilldownParams) => {
  if (!params) return url
  return { url, params: params as Record<string, string | undefined> }
}

const customerInsightsFetchArgs = (url: string, params?: CustomerInsightsQueryParams) => {
  if (!params) return url
  return { url, params: params as Record<string, string | undefined> }
}

export const analyticsApi = baseApi.injectEndpoints({
  endpoints: (builder) => ({
    getAnalyticsOverview: builder.query<AnalyticsOverview, AnalyticsQueryParams | undefined>({
      query: (params) => analyticsFetchArgs('/analytics/overview', params),
      providesTags: ['Analytics'],
    }),
    getRevenueTrend: builder.query<RevenueTrendResponse, AnalyticsQueryParams | undefined>({
      query: (params) => analyticsFetchArgs('/analytics/revenue-trend', params),
      providesTags: ['Analytics'],
    }),
    getPerformanceRanking: builder.query<PerformanceRankingResponse, AnalyticsQueryParams | undefined>({
      query: (params) => analyticsFetchArgs('/analytics/performance-ranking', params),
      providesTags: ['Analytics'],
    }),
    getReceivableAging: builder.query<ReceivableAgingResponse, AnalyticsQueryParams | undefined>({
      query: (params) => analyticsFetchArgs('/analytics/receivable-aging', params),
      providesTags: ['Analytics'],
    }),
    getCustomerInsights: builder.query<CustomerInsightsResponse, CustomerInsightsQueryParams | undefined>({
      query: (params) => customerInsightsFetchArgs('/analytics/customer-insights', params),
      providesTags: ['Analytics'],
    }),
    getServiceEfficiency: builder.query<ServiceEfficiencyResponse, AnalyticsQueryParams | undefined>({
      query: (params) => analyticsFetchArgs('/analytics/service-efficiency', params),
      providesTags: ['Analytics'],
    }),
    getAnalyticsDrilldown: builder.query<AnalyticsDrilldownResponse, AnalyticsDrilldownParams>({
      query: (params) => analyticsFetchArgs('/analytics/drilldown', params),
      providesTags: ['Analytics'],
    }),
  }),
})

export const {
  useGetAnalyticsOverviewQuery,
  useGetRevenueTrendQuery,
  useGetPerformanceRankingQuery,
  useGetReceivableAgingQuery,
  useGetCustomerInsightsQuery,
  useGetServiceEfficiencyQuery,
  useLazyGetAnalyticsDrilldownQuery,
} = analyticsApi

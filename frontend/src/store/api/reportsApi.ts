import { baseApi } from './baseApi'

export interface ReportMeta {
  id: string
  name: string
  description: string
  supported_filters: string[]
}

export interface ReportPageResponse {
  total: number
  page: number
  page_size: number
  items: any[]
}

export interface GetReportDataParams {
  reportId: string
  page?: number
  page_size?: number
  date_from?: string
  date_to?: string
  service_type?: number
  status?: string
  payment_method?: string
}

export const reportsApi = baseApi.injectEndpoints({
  endpoints: (builder) => ({
    listReports: builder.query<ReportMeta[], void>({
      query: () => '/reports',
      providesTags: ['Report'],
    }),
    getReportData: builder.query<ReportPageResponse, GetReportDataParams>({
      query: (params) => {
        const { reportId, ...rest } = params
        const searchParams = new URLSearchParams()
        Object.entries(rest).forEach(([key, value]) => {
          if (value !== undefined && value !== null && value !== '') {
            searchParams.append(key, String(value))
          }
        })
        return `/reports/${reportId}?${searchParams.toString()}`
      },
      providesTags: ['Report'],
    }),
  }),
})

export const { useListReportsQuery, useGetReportDataQuery, useLazyGetReportDataQuery } = reportsApi

export function getReportExportUrl(params: GetReportDataParams): string {
  const { reportId, ...rest } = params
  const searchParams = new URLSearchParams()
  Object.entries(rest).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== '') {
      searchParams.append(key, String(value))
    }
  })
  return `/api/v1/reports/${reportId}/export?${searchParams.toString()}`
}

import { baseApi } from './baseApi'
import type { Invoice, InvoiceCreate, PageResponse, InvoiceStatus } from '@/types'

export interface InvoiceAuditRequest {
  action: 'approve' | 'reject'
  remark?: string
  invoice_date?: string
  actual_invoice_no?: string
}

export const invoicesApi = baseApi.injectEndpoints({
  endpoints: (builder) => ({
    listInvoices: builder.query<PageResponse<Invoice>, { page?: number; page_size?: number; contract_id?: number; customer_id?: number; status?: InvoiceStatus; keyword?: string }>({
      query: (params) => ({ url: '/invoices', params }),
      providesTags: ['Invoice'],
    }),
    getInvoice: builder.query<Invoice, number>({
      query: (id) => `/invoices/${id}`,
      providesTags: (_, __, id) => [{ type: 'Invoice', id }],
    }),
    createInvoice: builder.mutation<Invoice, InvoiceCreate>({
      query: (body) => ({ url: '/invoices', method: 'POST', body }),
      invalidatesTags: ['Invoice'],
    }),
    updateInvoice: builder.mutation<Invoice, { id: number; data: Partial<Invoice> }>({
      query: ({ id, data }) => ({ url: `/invoices/${id}`, method: 'PATCH', body: data }),
      invalidatesTags: (_, __, { id }) => [{ type: 'Invoice', id }, 'Invoice'],
    }),
    deleteInvoice: builder.mutation<{ message: string }, number>({
      query: (id) => ({ url: `/invoices/${id}`, method: 'DELETE' }),
      invalidatesTags: ['Invoice'],
    }),
    auditInvoice: builder.mutation<Invoice, { id: number; data: InvoiceAuditRequest }>({
      query: ({ id, data }) => ({ url: `/invoices/${id}/audit`, method: 'POST', body: data }),
      invalidatesTags: (_, __, { id }) => [{ type: 'Invoice', id }, 'Invoice'],
    }),
    getDownloadUrl: builder.query<{ url: string }, number>({
      query: (id) => `/invoices/${id}/download-url`,
    }),
  }),
})

export const {
  useListInvoicesQuery,
  useGetInvoiceQuery,
  useCreateInvoiceMutation,
  useUpdateInvoiceMutation,
  useDeleteInvoiceMutation,
  useAuditInvoiceMutation,
  useGetDownloadUrlQuery,
} = invoicesApi

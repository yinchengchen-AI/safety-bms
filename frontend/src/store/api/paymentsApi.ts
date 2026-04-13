import { baseApi } from './baseApi'
import type { Payment, PaymentCreate, PageResponse, ContractReceivable } from '@/types'

export const paymentsApi = baseApi.injectEndpoints({
  endpoints: (builder) => ({
    listPayments: builder.query<PageResponse<Payment>, { page?: number; page_size?: number; contract_id?: number; customer_id?: number; invoice_id?: number }>({
      query: (params) => ({ url: '/payments', params }),
      providesTags: ['Payment'],
    }),
    getPayment: builder.query<Payment, number>({
      query: (id) => `/payments/${id}`,
      providesTags: (_, __, id) => [{ type: 'Payment', id }],
    }),
    createPayment: builder.mutation<Payment, PaymentCreate>({
      query: (body) => ({ url: '/payments', method: 'POST', body }),
      invalidatesTags: ['Payment'],
    }),
    updatePayment: builder.mutation<Payment, { id: number; data: Partial<Payment> }>({
      query: ({ id, data }) => ({ url: `/payments/${id}`, method: 'PATCH', body: data }),
      invalidatesTags: (_, __, { id }) => [{ type: 'Payment', id }, 'Payment'],
    }),
    getContractReceivable: builder.query<ContractReceivable, number>({
      query: (contractId) => `/payments/receivable/${contractId}`,
      providesTags: ['Payment'],
    }),
    deletePayment: builder.mutation<{ message: string }, number>({
      query: (id) => ({ url: `/payments/${id}`, method: 'DELETE' }),
      invalidatesTags: ['Payment'],
    }),
    listOverdueContracts: builder.query<ContractReceivable[], void>({
      query: () => '/payments/overdue',
      providesTags: ['Payment'],
    }),
  }),
})

export const {
  useListPaymentsQuery,
  useGetPaymentQuery,
  useCreatePaymentMutation,
  useUpdatePaymentMutation,
  useDeletePaymentMutation,
  useGetContractReceivableQuery,
  useListOverdueContractsQuery,
} = paymentsApi

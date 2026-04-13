import { baseApi } from './baseApi'
import type {
  Customer, CustomerListItem, CustomerCreate, CustomerContact,
  CustomerFollowUp, PageResponse, CustomerStatus,
} from '@/types'

export const customersApi = baseApi.injectEndpoints({
  endpoints: (builder) => ({
    listCustomers: builder.query<PageResponse<CustomerListItem>, { page?: number; page_size?: number; status?: CustomerStatus; keyword?: string }>({
      query: (params) => ({ url: '/customers', params }),
      providesTags: ['Customer'],
    }),
    getCustomer: builder.query<Customer, number>({
      query: (id) => `/customers/${id}`,
      providesTags: (_, __, id) => [{ type: 'Customer', id }],
    }),
    createCustomer: builder.mutation<Customer, CustomerCreate>({
      query: (body) => ({ url: '/customers', method: 'POST', body }),
      invalidatesTags: ['Customer'],
    }),
    updateCustomer: builder.mutation<Customer, { id: number; data: Partial<CustomerCreate> }>({
      query: ({ id, data }) => ({ url: `/customers/${id}`, method: 'PATCH', body: data }),
      invalidatesTags: (_, __, { id }) => [{ type: 'Customer', id }, 'Customer'],
    }),
    deleteCustomer: builder.mutation<{ message: string }, number>({
      query: (id) => ({ url: `/customers/${id}`, method: 'DELETE' }),
      invalidatesTags: ['Customer'],
    }),
    addContact: builder.mutation<CustomerContact, { customerId: number; data: Omit<CustomerContact, 'id' | 'customer_id' | 'created_at'> }>({
      query: ({ customerId, data }) => ({ url: `/customers/${customerId}/contacts`, method: 'POST', body: data }),
      invalidatesTags: (_, __, { customerId }) => [{ type: 'Customer', id: customerId }],
    }),
    addFollowUp: builder.mutation<CustomerFollowUp, { customerId: number; data: { content: string; follow_up_at: string; next_follow_up_at?: string } }>({
      query: ({ customerId, data }) => ({ url: `/customers/${customerId}/follow-ups`, method: 'POST', body: data }),
      invalidatesTags: (_, __, { customerId }) => [{ type: 'Customer', id: customerId }],
    }),
    listFollowUps: builder.query<CustomerFollowUp[], number>({
      query: (customerId) => `/customers/${customerId}/follow-ups`,
      providesTags: (_, __, customerId) => [{ type: 'Customer', id: customerId }],
    }),
  }),
})

export const {
  useListCustomersQuery,
  useGetCustomerQuery,
  useCreateCustomerMutation,
  useUpdateCustomerMutation,
  useDeleteCustomerMutation,
  useAddContactMutation,
  useAddFollowUpMutation,
  useListFollowUpsQuery,
} = customersApi

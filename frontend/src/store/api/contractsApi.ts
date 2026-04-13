import { baseApi } from './baseApi'
import type { Contract, ContractCreate, PageResponse, ContractStatus, ContractSignRequest, ContractUploadSignedRequest } from '@/types'

export const contractsApi = baseApi.injectEndpoints({
  endpoints: (builder) => ({
    listContracts: builder.query<PageResponse<Contract>, { page?: number; page_size?: number; customer_id?: number; status?: ContractStatus; keyword?: string }>({
      query: (params) => ({ url: '/contracts', params }),
      providesTags: ['Contract'],
    }),
    getContract: builder.query<Contract, number>({
      query: (id) => `/contracts/${id}`,
      providesTags: (_, __, id) => [{ type: 'Contract', id }],
    }),
    createContract: builder.mutation<Contract, ContractCreate>({
      query: (body) => ({ url: '/contracts', method: 'POST', body }),
      invalidatesTags: ['Contract'],
    }),
    updateContract: builder.mutation<Contract, { id: number; data: Partial<ContractCreate> }>({
      query: ({ id, data }) => ({ url: `/contracts/${id}`, method: 'PATCH', body: data }),
      invalidatesTags: (_, __, { id }) => [{ type: 'Contract', id }, 'Contract'],
    }),
    updateContractStatus: builder.mutation<Contract, { id: number; status: ContractStatus; remark?: string }>({
      query: ({ id, ...body }) => ({ url: `/contracts/${id}/status`, method: 'POST', body }),
      invalidatesTags: (_, __, { id }) => [{ type: 'Contract', id }, 'Contract'],
    }),
    deleteContract: builder.mutation<{ message: string }, number>({
      query: (id) => ({ url: `/contracts/${id}`, method: 'DELETE' }),
      invalidatesTags: ['Contract'],
    }),
    getContractDraftUrl: builder.query<{ url: string }, number>({
      query: (id) => `/contracts/${id}/draft-url`,
    }),
    generateContractDraft: builder.mutation<Contract, number>({
      query: (id) => ({ url: `/contracts/${id}/generate-draft`, method: 'POST' }),
      invalidatesTags: (_, __, id) => [{ type: 'Contract', id }, 'Contract'],
    }),
    signContract: builder.mutation<Contract, { id: number; data: ContractSignRequest }>({
      query: ({ id, data }) => ({ url: `/contracts/${id}/sign`, method: 'POST', body: data }),
      invalidatesTags: (_, __, { id }) => [{ type: 'Contract', id }, 'Contract'],
    }),
    uploadSignedContract: builder.mutation<Contract, { id: number; data: ContractUploadSignedRequest }>({
      query: ({ id, data }) => ({ url: `/contracts/${id}/upload-signed`, method: 'POST', body: data }),
      invalidatesTags: (_, __, { id }) => [{ type: 'Contract', id }, 'Contract'],
    }),
    getContractPdfUrl: builder.query<{ url: string }, number>({
      query: (id) => `/contracts/${id}/download-pdf`,
    }),
  }),
})

export const {
  useListContractsQuery,
  useGetContractQuery,
  useCreateContractMutation,
  useUpdateContractMutation,
  useUpdateContractStatusMutation,
  useDeleteContractMutation,
  useLazyGetContractDraftUrlQuery,
  useGenerateContractDraftMutation,
  useSignContractMutation,
  useUploadSignedContractMutation,
  useLazyGetContractPdfUrlQuery,
} = contractsApi

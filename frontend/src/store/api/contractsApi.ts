import { baseApi } from './baseApi'
import type { Contract, ContractAttachmentCreate, ContractCreate, PageResponse, ContractStatus } from '@/types'

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
    uploadContractAttachmentFile: builder.mutation<{ file_url: string; file_name: string; file_size: number }, { id: number; file: File }>({
      query: ({ id, file }) => {
        const formData = new FormData()
        formData.append('file', file)
        return { url: `/contracts/${id}/attachments/upload`, method: 'POST', body: formData }
      },
    }),
    uploadContractAttachment: builder.mutation<Contract, { id: number; data: ContractAttachmentCreate }>({
      query: ({ id, data }) => ({ url: `/contracts/${id}/attachments`, method: 'POST', body: data }),
      invalidatesTags: (_, __, { id }) => [{ type: 'Contract', id }, 'Contract'],
    }),
    deleteContractAttachment: builder.mutation<{ message: string }, { id: number; attachmentId: number }>({
      query: ({ id, attachmentId }) => ({ url: `/contracts/${id}/attachments/${attachmentId}`, method: 'DELETE' }),
      invalidatesTags: (_, __, { id }) => [{ type: 'Contract', id }, 'Contract'],
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
  useUploadContractAttachmentFileMutation,
  useUploadContractAttachmentMutation,
  useDeleteContractAttachmentMutation,
} = contractsApi

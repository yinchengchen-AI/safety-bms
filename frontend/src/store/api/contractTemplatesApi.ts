import { baseApi } from './baseApi'
import type { ContractTemplate, PageResponse } from '@/types'

export interface ContractTemplateCreate {
  name: string
  service_type: number
  is_default?: boolean
}

export const contractTemplatesApi = baseApi.injectEndpoints({
  endpoints: (builder) => ({
    listContractTemplates: builder.query<PageResponse<ContractTemplate>, { page?: number; page_size?: number; service_type?: number }>({
      query: (params) => ({ url: '/contract-templates', params }),
      providesTags: ['ContractTemplate'],
    }),
    createContractTemplate: builder.mutation<ContractTemplate, ContractTemplateCreate>({
      query: (body) => ({ url: '/contract-templates', method: 'POST', body }),
      invalidatesTags: ['ContractTemplate'],
    }),
    uploadContractTemplateFile: builder.mutation<{ file_url: string; file_name: string; file_size: number }, { id: number; file: File }>({
      query: ({ id, file }) => {
        const formData = new FormData()
        formData.append('file', file)
        return {
          url: `/contract-templates/${id}/upload`,
          method: 'POST',
          body: formData,
        }
      },
      invalidatesTags: (_, __, { id }) => [{ type: 'ContractTemplate', id }, 'ContractTemplate'],
    }),
    updateContractTemplate: builder.mutation<ContractTemplate, { id: number; data: Partial<ContractTemplateCreate> }>({
      query: ({ id, data }) => ({ url: `/contract-templates/${id}`, method: 'PATCH', body: data }),
      invalidatesTags: (_, __, { id }) => [{ type: 'ContractTemplate', id }, 'ContractTemplate'],
    }),
    deleteContractTemplate: builder.mutation<{ message: string }, number>({
      query: (id) => ({ url: `/contract-templates/${id}`, method: 'DELETE' }),
      invalidatesTags: ['ContractTemplate'],
    }),
    getTemplateDownloadUrl: builder.query<{ url: string }, number>({
      query: (id) => ({ url: `/contract-templates/${id}/download-url` }),
    }),
  }),
})

export const {
  useListContractTemplatesQuery,
  useCreateContractTemplateMutation,
  useUpdateContractTemplateMutation,
  useUploadContractTemplateFileMutation,
  useDeleteContractTemplateMutation,
  useLazyGetTemplateDownloadUrlQuery,
} = contractTemplatesApi

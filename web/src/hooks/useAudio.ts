import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '@/lib/api'
import { AudioFile, ProcessingJob } from '@/lib/types'

export const useAudioFiles = (projectId?: number) => {
  return useQuery({
    queryKey: ['audio-files', projectId],
    queryFn: async () => {
      const params = projectId ? { project_id: projectId } : {}
      const response = await api.get('/api/v1/audio/files', { params })
      return response.data
    },
  })
}

export const useAudioFile = (id: number) => {
  return useQuery({
    queryKey: ['audio-files', id],
    queryFn: async () => {
      const response = await api.get(`/api/v1/audio/files/${id}`)
      return response.data
    },
    enabled: !!id,
  })
}

export const useUploadAudio = () => {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: async ({ file, projectId }: { file: File; projectId?: number }) => {
      const formData = new FormData()
      formData.append('file', file)
      if (projectId) {
        formData.append('project_id', projectId.toString())
      }
      
      const response = await api.post('/api/v1/audio/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      })
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['audio-files'] })
    },
  })
}

export const useProcessingJobs = (projectId?: number, status?: string) => {
  return useQuery({
    queryKey: ['processing-jobs', projectId, status],
    queryFn: async () => {
      const params: any = {}
      if (projectId) params.project_id = projectId
      if (status) params.status_filter = status
      
      const response = await api.get('/api/v1/audio/jobs', { params })
      return response.data
    },
  })
}

export const useProcessingJob = (id: number) => {
  return useQuery({
    queryKey: ['processing-jobs', id],
    queryFn: async () => {
      const response = await api.get(`/api/v1/audio/jobs/${id}`)
      return response.data
    },
    enabled: !!id,
    refetchInterval: (data) => {
      // Refetch every 2 seconds if job is still processing
      return data?.status === 'processing' ? 2000 : false
    },
  })
}

export const useProcessAudio = () => {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: async (jobData: {
      name: string
      description?: string
      audio_file_id: number
      project_id?: number
      effects_config?: Record<string, any>
      output_format?: string
    }) => {
      const response = await api.post('/api/v1/audio/process', jobData)
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['processing-jobs'] })
    },
  })
}

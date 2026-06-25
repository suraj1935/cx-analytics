import { useState, useCallback, useEffect } from 'react'
import axios from 'axios'
import { apiClient } from '@/services/api'

interface UseApiState<T> {
  data: T | null
  loading: boolean
  error: Error | null
}

function getApiErrorMessage(error: unknown, fallback: string) {
  if (!axios.isAxiosError(error)) {
    return error instanceof Error ? error.message : fallback
  }

  if (error.response?.status === 401) {
    return 'Your session expired. Please sign in again.'
  }

  const detail = error.response?.data?.detail
  if (typeof detail === 'string') {
    return detail
  }

  return error.message || fallback
}

export function useApi<T>(asyncFn: () => Promise<T>, immediate: boolean = true) {
  const [state, setState] = useState<UseApiState<T>>({
    data: null,
    loading: immediate,
    error: null,
  })

  const execute = useCallback(async () => {
    setState({ data: null, loading: true, error: null })
    try {
      const result = await asyncFn()
      setState({ data: result, loading: false, error: null })
      return result
    } catch (error) {
      const err = error instanceof Error ? error : new Error(String(error))
      setState({ data: null, loading: false, error: err })
    }
  }, [asyncFn])

  // Auto-execute on mount when immediate=true
  useEffect(() => {
    if (immediate) {
      execute()
    }
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  return { ...state, execute }
}

export function useFileUpload() {
  const [uploading, setUploading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const upload = useCallback(async (file: File) => {
    setUploading(true)
    setError(null)
    try {
      return await apiClient.uploadFile(file)
    } catch (err) {
      const msg = getApiErrorMessage(err, 'Upload failed')
      setError(msg)
      throw err
    } finally {
      setUploading(false)
    }
  }, [])

  return { upload, uploading, error }
}

export function useAnalytics() {
  return useApi(() => apiClient.getAnalytics(), true)
}

export function useAuditDetails(auditId: string | null) {
  const fetchDetails = useCallback(() => {
    if (!auditId) return Promise.resolve([])
    return apiClient.getAuditDetails(auditId)
  }, [auditId])
  return useApi(fetchDetails, !!auditId)
}

export function useAudioUpload() {
  const [uploading, setUploading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const upload = useCallback(async (file: File) => {
    setUploading(true)
    setError(null)
    try {
      return await apiClient.uploadAudio(file)
    } catch (err) {
      const msg = getApiErrorMessage(err, 'Audio upload failed')
      setError(msg)
      throw err
    } finally {
      setUploading(false)
    }
  }, [])

  return { upload, uploading, error }
}

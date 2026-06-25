import axios, { type InternalAxiosRequestConfig } from 'axios'
import { AnalyticsData, AudioTranscript, UserSettings } from '@/types'
import { supabase } from './supabase'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api'

interface RetryableRequestConfig extends InternalAxiosRequestConfig {
  _authRetry?: boolean
}

let refreshPromise: Promise<string | null> | null = null

async function refreshAccessToken() {
  if (!refreshPromise) {
    refreshPromise = supabase.auth.refreshSession().then(({ data, error }) => {
      if (error || !data.session?.access_token) return null
      return data.session.access_token
    }).finally(() => {
      refreshPromise = null
    })
  }
  return refreshPromise
}

class ApiClient {
  private client = axios.create({
    baseURL: API_URL,
    timeout: 30000,
  })

  constructor() {
    this.client.interceptors.request.use(async (config) => {
      const { data } = await supabase.auth.getSession()
      const token = data.session?.access_token
      if (token) {
        config.headers.Authorization = `Bearer ${token}`
      }
      return config
    })

    this.client.interceptors.response.use(
      (response) => response,
      async (error) => {
        if (!axios.isAxiosError(error) || error.response?.status !== 401 || !error.config) {
          return Promise.reject(error)
        }

        const config = error.config as RetryableRequestConfig
        if (config._authRetry) {
          await supabase.auth.signOut({ scope: 'local' })
          return Promise.reject(error)
        }

        config._authRetry = true
        const token = await refreshAccessToken()
        if (!token) {
          await supabase.auth.signOut({ scope: 'local' })
          return Promise.reject(error)
        }

        config.headers.Authorization = `Bearer ${token}`
        return this.client.request(config)
      },
    )
  }

  async healthCheck(): Promise<boolean> {
    try {
      const response = await this.client.get('/health')
      return response.status === 200
    } catch {
      return false
    }
  }

  async uploadFile(file: File) {
    const formData = new FormData()
    formData.append('file', file)
    const response = await this.client.post('/upload/', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    return response.data
  }

  async getAnalytics(): Promise<AnalyticsData> {
    const response = await this.client.get('/analytics')
    return response.data
  }

  async getAuditDetails(auditId: string): Promise<any[]> {
    const response = await this.client.get(`/analytics/audit/${auditId}`)
    return response.data
  }

  async uploadAudio(file: File): Promise<AudioTranscript> {
    const formData = new FormData()
    formData.append('file', file)
    const response = await this.client.post('/audio/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    const recordingId = response.data.id
    const started = Date.now()
    const timeoutMs = 30 * 60 * 1000

    while (Date.now() - started < timeoutMs) {
      const transcript = await this.getAudio(recordingId)
      if (transcript.status === 'done') {
        return transcript
      }
      if (transcript.status === 'failed') {
        throw new Error(transcript.error_msg || 'Audio transcription failed')
      }
      await new Promise((resolve) => window.setTimeout(resolve, 5000))
    }

    throw new Error('Audio transcription timed out')
  }

  async getAudio(audioId: string): Promise<AudioTranscript> {
    const response = await this.client.get(`/audio/${audioId}`)
    return response.data
  }

  async getAudioFile(audioId: string): Promise<Blob> {
    const response = await this.client.get(`/audio/${audioId}/file`, { responseType: 'blob' })
    return response.data
  }

  async getSettings(): Promise<UserSettings> {
    return (await this.client.get('/settings')).data
  }

  async updateSettings(settings: UserSettings): Promise<UserSettings> {
    return (await this.client.put('/settings', settings)).data
  }
}

export const apiClient = new ApiClient()

import axios from 'axios'
import { AnalyticsData, AudioTranscript } from '@/types'
import { supabase } from './supabase'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api'

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
}

export const apiClient = new ApiClient()

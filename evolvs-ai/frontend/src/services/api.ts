import axios from 'axios'
import { AnalyticsData, AudioTranscript } from '@/types'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api'

class ApiClient {
  private client = axios.create({
    baseURL: API_URL,
    timeout: 30000,
  })

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

  async uploadAudio(file: File): Promise<AudioTranscript> {
    const formData = new FormData()
    formData.append('file', file)
    const response = await this.client.post('/audio/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    return response.data
  }

  async getAudio(audioId: string): Promise<AudioTranscript> {
    const response = await this.client.get(`/audio/${audioId}`)
    return response.data
  }
}

export const apiClient = new ApiClient()

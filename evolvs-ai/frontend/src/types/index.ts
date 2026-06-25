export interface Audit {
  audit_id: string
  project: string
  status: string
  final_score: number
  system_score: number
  created_at: string
  [key: string]: any // Allow additional columns from the Excel
}

export interface Agent {
  agent: string
  agent_id?: string
  audits: number
  completed_audits?: number
  completion_rate: number
  average_final_score: number
  average_system_score?: number
  average_qa_turnaround?: number
  dispute_rate?: number
  sla_adherence: number
  [key: string]: any
}

export interface Parameter {
  criterion_key: string
  label: string
  category?: string
  audits?: number
  average_score?: number
  pass_rate: number
  failures: number
  auto_fails?: number
  weight?: number
  [key: string]: any
}

export interface Reason {
  criterion_key: string
  label: string
  occurrences: number
  audits?: number
  failures?: number
  [key: string]: any
}

export interface Summary {
  total_audits: number
  completion_rate: number
  average_final_score: number
}

export interface AnalyticsData {
  summary: Summary
  audits: Audit[]
  agents: Agent[]
  parameters: Parameter[]
  reasons: Reason[]
}

export interface AudioTranscript {
  id: string
  file_name: string
  duration: number
  status?: 'pending' | 'processing' | 'done' | 'failed'
  error_msg?: string | null
  transcript: string
  vtt_content: string
  created_at: string
  original_file_retained?: boolean
}

export interface UserSettings {
  retain_original_audio: boolean
  llm_model: string
  embedding_model: string
}

export interface Audit {
  audit_id: string
  project: string
  status: string
  final_score: number
  system_score: number
  created_at: string
}

export interface Agent {
  agent: string
  audits: number
  average_final_score: number
  completion_rate: number
  sla_adherence: number
}

export interface Parameter {
  criterion_key: string
  label: string
  failures: number
  pass_rate: number
}

export interface Reason {
  criterion_key: string
  label: string
  occurrences: number
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
  transcript: string
  vtt_content: string
  created_at: string
}

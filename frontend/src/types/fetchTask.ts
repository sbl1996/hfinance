export type FetchTaskRunStatus = 'PENDING' | 'RUNNING' | 'SUCCESS' | 'FAILED'

export interface FetchTaskRunSummary {
  id: number
  scheduled_for: string
  status: FetchTaskRunStatus
  started_at?: string | null
  finished_at?: string | null
  error_message?: string | null
  price_date?: string | null
  price_value?: number | null
}

export interface FetchTask {
  id: number
  code: string
  name: string
  market: 'A_STOCK' | 'HK_STOCK' | 'FUND'
  enabled: boolean
  run_time: string
  weekdays: number[]
  created_at: string
  updated_at: string
  latest_run?: FetchTaskRunSummary | null
}

export interface FetchTaskCreatePayload {
  code: string
  name: string
  market: 'A_STOCK' | 'HK_STOCK' | 'FUND'
  enabled: boolean
  run_time: string
  weekdays: number[]
}

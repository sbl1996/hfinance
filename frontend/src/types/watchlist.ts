export type WatchMarket = 'A_STOCK' | 'HK_STOCK' | 'FUND' | 'US_STOCK' | 'CN_INDEX'

export interface WatchlistItem {
  id: number
  code: string
  name: string
  market: WatchMarket
  latest_price: number | null
  price_currency: string | null
  price_date: string | null
  growth_rate: number | null
  created_at: string
  updated_at: string
}

export interface WatchlistListResponse {
  items: WatchlistItem[]
}

export interface WatchlistCreatePayload {
  code: string
  name: string
  market: WatchMarket
}

export interface WatchlistUpdatePayload {
  code?: string
  name?: string
  market?: WatchMarket
}

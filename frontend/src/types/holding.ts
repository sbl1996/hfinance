export interface PriceHistoryItem {
  date: string
  price: number
  yield_rate: number | null
}

export interface PriceHistoryResponse {
  code: string
  name: string
  unit_cost: number
  market: string
  currency: string
  current_price: number | null
  price_currency: string | null
  price_date: string | null
  market_value_cny: number | null
  pnl_cny: number | null
  pnl_rate: number | null
  growth_rate: number | null
  growth_pnl_cny: number | null
  quantity: number
  cost_total_cny: number
  history: PriceHistoryItem[]
  empty: boolean
}

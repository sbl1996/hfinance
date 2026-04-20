import { defineStore } from 'pinia'
import { ref } from 'vue'
import request from '@/utils/request'

export const useHoldingStore = defineStore('holding', () => {
  const holdings = ref<any[]>([])
  const summary = ref({ total_market_value_cny: 0, total_cost_cny: 0, total_pnl_cny: 0, daily_pnl_cny: 0 })
  const loading = ref(false)
  const refreshing = ref(false)
  const refreshingCodes = ref<Set<string>>(new Set())

  async function fetchHoldings() {
    loading.value = true
    try {
      const data: any = await request.get('/holdings')
      holdings.value = data.items
      summary.value = {
        total_market_value_cny: data.total_market_value_cny,
        total_cost_cny: data.total_cost_cny,
        total_pnl_cny: data.total_pnl_cny,
        daily_pnl_cny: data.daily_pnl_cny,
      }
    } finally {
      loading.value = false
    }
  }

  async function createHolding(data: any) {
    await request.post('/holdings', data)
    await fetchHoldings()
  }

  async function updateHolding(id: number, data: any) {
    await request.put(`/holdings/${id}`, data)
    await fetchHoldings()
  }

  async function deleteHolding(id: number) {
    await request.delete(`/holdings/${id}`)
    await fetchHoldings()
  }

  async function refreshMarket() {
    refreshing.value = true
    try {
      await request.post('/market/refresh')
      await fetchHoldings()
    } finally {
      refreshing.value = false
    }
  }

  async function refreshSingle(code: string, market: string) {
    refreshingCodes.value.add(code)
    try {
      await request.post(`/market/refresh/${code}`, null, { params: { market } })
      await fetchHoldings()
    } finally {
      refreshingCodes.value.delete(code)
    }
  }

  return { holdings, summary, loading, refreshing, refreshingCodes, fetchHoldings, createHolding, updateHolding, deleteHolding, refreshMarket, refreshSingle }
})

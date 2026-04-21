import { defineStore } from 'pinia'
import { ref } from 'vue'
import request from '@/utils/request'
import { showSuccessToast } from 'vant'

export const useHoldingStore = defineStore('holding', () => {
  const holdings = ref<any[]>([])
  const summary = ref({ total_market_value_cny: 0, total_cost_cny: 0, total_pnl_cny: 0, daily_pnl_cny: 0 })
  const loading = ref(false)
  const refreshing = ref(false)
  const invalidatingFundNavCache = ref(false)
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

  async function reorderHoldings(items: Array<{ id: number; sort_order: number }>) {
    await request.post('/holdings/reorder', { items })
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

  async function invalidateFundNavCache() {
    invalidatingFundNavCache.value = true
    try {
      await request.post('/market/fund-nav-cache/invalidate')
    } finally {
      invalidatingFundNavCache.value = false
    }
  }

  async function importFundHistory(id: number) {
    const result: any = await request.post(`/holdings/${id}/import-history`)
    showSuccessToast(result.detail || '全量导入完成')
    await fetchHoldings()
    return result
  }

  return {
    holdings,
    summary,
    loading,
    refreshing,
    invalidatingFundNavCache,
    refreshingCodes,
    fetchHoldings,
    createHolding,
    updateHolding,
    reorderHoldings,
    deleteHolding,
    refreshMarket,
    refreshSingle,
    invalidateFundNavCache,
    importFundHistory,
  }
})

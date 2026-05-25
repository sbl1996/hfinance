import { defineStore } from 'pinia'
import { ref } from 'vue'
import request from '@/utils/request'
import { showSuccessToast } from 'vant'
import type { WatchlistCreatePayload, WatchlistItem, WatchlistUpdatePayload } from '@/types/watchlist'

export const useWatchlistStore = defineStore('watchlist', () => {
  const items = ref<WatchlistItem[]>([])
  const loading = ref(false)
  const refreshingCodes = ref<Set<string>>(new Set())

  async function fetchWatchlist() {
    loading.value = true
    try {
      const data: { items: WatchlistItem[] } = await request.get('/watchlist')
      items.value = data.items
    } finally {
      loading.value = false
    }
  }

  async function createWatchlistItem(payload: WatchlistCreatePayload) {
    await request.post('/watchlist', payload)
    await fetchWatchlist()
  }

  async function fetchWatchlistItem(id: number) {
    const data: WatchlistItem = await request.get(`/watchlist/${id}`)
    return data
  }

  async function updateWatchlistItem(id: number, payload: WatchlistUpdatePayload) {
    await request.put(`/watchlist/${id}`, payload)
    await fetchWatchlist()
  }

  async function deleteWatchlistItem(id: number) {
    await request.delete(`/watchlist/${id}`)
    await fetchWatchlist()
  }

  async function refreshSingle(code: string, market: string) {
    refreshingCodes.value.add(code)
    try {
      await request.post('/market/refresh/single', null, { params: { code, market } })
      await fetchWatchlist()
    } finally {
      refreshingCodes.value.delete(code)
    }
  }

  async function importFundHistory(id: number) {
    const result: any = await request.post(`/watchlist/${id}/import-history`)
    showSuccessToast(result.detail || '全量导入完成')
    await fetchWatchlist()
    return result
  }

  async function fetchPriceHistory(id: number) {
    const data: any = await request.get(`/watchlist/${id}/price_history`)
    return data
  }

  return {
    items,
    loading,
    refreshingCodes,
    fetchWatchlist,
    createWatchlistItem,
    fetchWatchlistItem,
    updateWatchlistItem,
    deleteWatchlistItem,
    refreshSingle,
    importFundHistory,
    fetchPriceHistory,
  }
})

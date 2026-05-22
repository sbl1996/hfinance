import { defineStore } from 'pinia'
import { ref } from 'vue'
import request from '@/utils/request'
import type { WatchlistCreatePayload, WatchlistItem } from '@/types/watchlist'

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

  async function refreshSingle(code: string, market: string) {
    refreshingCodes.value.add(code)
    try {
      await request.post('/market/refresh/single', null, { params: { code, market } })
      await fetchWatchlist()
    } finally {
      refreshingCodes.value.delete(code)
    }
  }

  return {
    items,
    loading,
    refreshingCodes,
    fetchWatchlist,
    createWatchlistItem,
    refreshSingle,
  }
})

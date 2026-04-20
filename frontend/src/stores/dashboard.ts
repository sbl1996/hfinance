import { defineStore } from 'pinia'
import { ref } from 'vue'
import request from '@/utils/request'

export const useDashboardStore = defineStore('dashboard', () => {
  const overview = ref<any>(null)
  const distribution = ref<any>(null)
  const loading = ref(false)

  async function fetchOverview() {
    loading.value = true
    try {
      overview.value = await request.get('/dashboard/overview')
    } finally {
      loading.value = false
    }
  }

  async function fetchDistribution() {
    try {
      distribution.value = await request.get('/dashboard/distribution')
    } catch { /* ignore */ }
  }

  return { overview, distribution, loading, fetchOverview, fetchDistribution }
})

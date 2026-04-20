import { defineStore } from 'pinia'
import { ref } from 'vue'
import request from '@/utils/request'

export const useLiabilityStore = defineStore('liability', () => {
  const liabilities = ref<any[]>([])
  const totalAmount = ref(0)
  const loading = ref(false)

  async function fetchLiabilities() {
    loading.value = true
    try {
      const data: any = await request.get('/liabilities')
      liabilities.value = data.items
      totalAmount.value = data.total_amount_cny
    } finally {
      loading.value = false
    }
  }

  async function createLiability(data: any) {
    await request.post('/liabilities', data)
    await fetchLiabilities()
  }

  async function updateLiability(id: number, data: any) {
    await request.put(`/liabilities/${id}`, data)
    await fetchLiabilities()
  }

  async function deleteLiability(id: number) {
    await request.delete(`/liabilities/${id}`)
    await fetchLiabilities()
  }

  return { liabilities, totalAmount, loading, fetchLiabilities, createLiability, updateLiability, deleteLiability }
})

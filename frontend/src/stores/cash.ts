import { defineStore } from 'pinia'
import { ref } from 'vue'
import request from '@/utils/request'

export const useCashStore = defineStore('cash', () => {
  const accounts = ref<any[]>([])
  const totalBalance = ref(0)
  const loading = ref(false)

  async function fetchAccounts() {
    loading.value = true
    try {
      const data: any = await request.get('/cash')
      accounts.value = data.items
      totalBalance.value = data.total_balance_cny
    } finally {
      loading.value = false
    }
  }

  async function createAccount(data: any) {
    await request.post('/cash', data)
    await fetchAccounts()
  }

  async function updateAccount(id: number, data: any) {
    await request.put(`/cash/${id}`, data)
    await fetchAccounts()
  }

  async function deleteAccount(id: number) {
    await request.delete(`/cash/${id}`)
    await fetchAccounts()
  }

  return { accounts, totalBalance, loading, fetchAccounts, createAccount, updateAccount, deleteAccount }
})

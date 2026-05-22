import { defineStore } from 'pinia'
import { ref } from 'vue'
import request from '@/utils/request'
import type { FetchTask, FetchTaskCreatePayload, FetchTaskRunSummary } from '@/types/fetchTask'

export const useFetchTaskStore = defineStore('fetchTask', () => {
  const tasks = ref<FetchTask[]>([])
  const loading = ref(false)
  const runsLoading = ref(false)
  const currentRuns = ref<FetchTaskRunSummary[]>([])

  async function fetchTasks() {
    loading.value = true
    try {
      const data: { items: FetchTask[] } = await request.get('/fetch-tasks')
      tasks.value = data.items
    } finally {
      loading.value = false
    }
  }

  async function createTask(payload: FetchTaskCreatePayload) {
    await request.post('/fetch-tasks', payload)
    await fetchTasks()
  }

  async function updateTask(taskId: number, payload: Partial<FetchTaskCreatePayload>) {
    await request.put(`/fetch-tasks/${taskId}`, payload)
    await fetchTasks()
  }

  async function deleteTask(taskId: number) {
    await request.delete(`/fetch-tasks/${taskId}`)
    await fetchTasks()
  }

  async function toggleTask(taskId: number, enabled: boolean) {
    await request.post(`/fetch-tasks/${taskId}/toggle`, { enabled })
    await fetchTasks()
  }

  async function fetchRuns(taskId: number, limit = 20) {
    runsLoading.value = true
    try {
      const data: { items: FetchTaskRunSummary[] } = await request.get(`/fetch-tasks/${taskId}/runs`, { params: { limit } })
      currentRuns.value = data.items
      return data.items
    } finally {
      runsLoading.value = false
    }
  }

  return {
    tasks,
    loading,
    runsLoading,
    currentRuns,
    fetchTasks,
    createTask,
    updateTask,
    deleteTask,
    toggleTask,
    fetchRuns,
  }
})

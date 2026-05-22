import { defineStore } from 'pinia'
import { ref } from 'vue'
import request from '@/utils/request'
import type { FetchTask, FetchTaskCreatePayload, FetchTaskRunSummary } from '@/types/fetchTask'

export const useFetchTaskStore = defineStore('fetchTask', () => {
  const tasks = ref<FetchTask[]>([])
  const loading = ref(false)
  const runsLoading = ref(false)
  const currentRuns = ref<FetchTaskRunSummary[]>([])

  async function fetchTasks(options: { silent?: boolean } = {}) {
    if (!options.silent) {
      loading.value = true
    }
    try {
      const data: { items: FetchTask[] } = await request.get('/fetch-tasks')
      tasks.value = data.items
    } finally {
      if (!options.silent) {
        loading.value = false
      }
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

  async function runNow(taskId: number) {
    const run: FetchTaskRunSummary = await request.post(`/fetch-tasks/${taskId}/run-now`)
    await fetchTasks()
    return run
  }

  async function fetchRuns(taskId: number, limit = 20, options: { silent?: boolean } = {}) {
    if (!options.silent) {
      runsLoading.value = true
    }
    try {
      const data: { items: FetchTaskRunSummary[] } = await request.get(`/fetch-tasks/${taskId}/runs`, { params: { limit } })
      currentRuns.value = data.items
      return data.items
    } finally {
      if (!options.silent) {
        runsLoading.value = false
      }
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
    runNow,
    fetchRuns,
  }
})

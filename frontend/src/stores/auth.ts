import { defineStore } from 'pinia'
import { ref } from 'vue'
import request from '@/utils/request'

export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem('token') || '')
  const isLoggedIn = ref(!!token.value)

  async function login(password: string) {
    const data: any = await request.post('/auth/login', { password })
    token.value = data.token
    localStorage.setItem('token', data.token)
    isLoggedIn.value = true
  }

  function logout() {
    token.value = ''
    localStorage.removeItem('token')
    isLoggedIn.value = false
    window.location.href = '/login'
  }

  return { token, isLoggedIn, login, logout }
})

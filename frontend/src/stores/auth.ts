import { defineStore } from 'pinia'
import request from '@/utils/request'
import { authSession, clearAuthToken, setAuthToken } from '@/stores/authSession'

export const useAuthStore = defineStore('auth', () => {
  const { token, isLoggedIn, role, isGuest } = authSession

  async function login(password: string) {
    const data: any = await request.post('/auth/login', { password })
    setAuthToken(data.token)
  }

  function logout() {
    clearAuthToken()
  }

  return { token, isLoggedIn, role, isGuest, login, logout }
})

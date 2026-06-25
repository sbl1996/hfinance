import { computed, ref } from 'vue'
import { getRoleFromToken } from '@/utils/auth'

const TOKEN_STORAGE_KEY = 'token'

function readStoredToken(): string {
  const storedToken = localStorage.getItem(TOKEN_STORAGE_KEY) || ''
  if (!storedToken) return ''
  if (!getRoleFromToken(storedToken)) {
    localStorage.removeItem(TOKEN_STORAGE_KEY)
    return ''
  }
  return storedToken
}

const token = ref(readStoredToken())
const role = computed(() => getRoleFromToken(token.value))
const isLoggedIn = computed(() => !!role.value)
const isGuest = computed(() => role.value === 'guest')

export function setAuthToken(nextToken: string) {
  token.value = nextToken
  localStorage.setItem(TOKEN_STORAGE_KEY, nextToken)
}

export function clearAuthToken() {
  token.value = ''
  localStorage.removeItem(TOKEN_STORAGE_KEY)
}

export function syncAuthToken() {
  token.value = readStoredToken()
}

export const authSession = {
  token,
  role,
  isLoggedIn,
  isGuest,
}

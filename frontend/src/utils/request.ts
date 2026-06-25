/**
 * Axios 实例封装
 * - 统一 baseURL
 * - Token 拦截器（请求头自动注入）
 * - 401 响应自动跳转登录
 * - 全局错误处理
 */
import axios from 'axios'
import { showToast } from 'vant'
import 'vant/es/toast/style'
import router from '@/router'
import { authSession, clearAuthToken } from '@/stores/authSession'

const request = axios.create({
  baseURL: '/api',
  timeout: 30000,
})

// ---- 请求拦截器：自动注入 Token ----
request.interceptors.request.use(
  (config) => {
    if (authSession.token.value) {
      config.headers.Authorization = `Bearer ${authSession.token.value}`
    }
    return config
  },
  (error) => Promise.reject(error),
)

// 用于防止短时间内重复弹出相同的错误提示
let lastErrorTime = 0
const ERROR_THROTTLE = 1000 

function buildRequestLabel(error: any): string {
  const method = error.config?.method?.toUpperCase?.() || 'UNKNOWN'
  const baseURL = error.config?.baseURL || ''
  const url = error.config?.url || ''
  return `${method} ${baseURL}${url}`
}

function logRequestError(error: any) {
  const label = buildRequestLabel(error)
  const params = error.config?.params
  const payload = error.config?.data
  const status = error.response?.status
  const responseData = error.response?.data

  console.groupCollapsed(`[API] ${label}`)
  console.log('kind:', classifyRequestError(error))
  console.log('status:', status ?? 'NO_RESPONSE')
  console.log('params:', params ?? null)
  console.log('payload:', payload ?? null)
  console.log('response:', responseData ?? null)
  console.log('code:', error.code ?? null)
  console.log('message:', error.message)
  console.log('raw error:', error)
  console.groupEnd()
}

function classifyRequestError(error: any): 'backend_response' | 'network_or_proxy' | 'frontend_request' {
  if (error.response) {
    return 'backend_response'
  }
  if (error.request) {
    return 'network_or_proxy'
  }
  return 'frontend_request'
}

function buildUserErrorMessage(error: any): string {
  const status = error.response?.status
  const detail = error.response?.data?.detail
  const kind = classifyRequestError(error)
  const label = buildRequestLabel(error)

  if (status === 401) {
    return `登录已失效\n${label}\n请重新登录`
  }

  if (kind === 'backend_response') {
    const backendMessage = detail
      ? (typeof detail === 'string' ? detail : JSON.stringify(detail))
      : ''
    return backendMessage
      ? `后端已返回失败\n${label}\n状态码: ${status}\n信息: ${backendMessage}`
      : `后端已返回失败\n${label}\n状态码: ${status}`
  }

  if (kind === 'network_or_proxy') {
    if (error.code === 'ECONNABORTED') {
      return `请求超时\n${label}\n请求已发出，但后端长时间未响应`
    }
    if (error.message === 'Network Error' || error.code === 'ERR_NETWORK') {
      return `网络或代理失败\n${label}\n请求未拿到后端响应\n请检查服务、Nginx 或证书`
    }
    return `请求未收到响应\n${label}\n请求已发出，但未收到后端响应`
  }

  return `前端请求失败\n${label}\n${error.message || '请求初始化失败'}`
}

// ---- 响应拦截器：统一错误处理 ----
request.interceptors.response.use(
  (response) => response.data,
  (error) => {
    logRequestError(error)
    const status = error.response?.status
    
    if (status === 401) {
      clearAuthToken()
      if (router.currentRoute.value.name !== 'Login') {
        void router.replace({ name: 'Login' })
      }
      return Promise.reject(error)
    }

    const now = Date.now()
    if (now - lastErrorTime > ERROR_THROTTLE) {
      lastErrorTime = now

      showToast({
        message: buildUserErrorMessage(error),
        type: 'fail',
        duration: 5000,
        wordBreak: 'break-word',
      })
    }
    
    return Promise.reject(error)
  },
)

export default request

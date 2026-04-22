/**
 * Axios 实例封装
 * - 统一 baseURL
 * - Token 拦截器（请求头自动注入）
 * - 401 响应自动跳转登录
 * - 全局错误处理
 */
import axios from 'axios'
import { showToast, showDialog } from 'vant'

const request = axios.create({
  baseURL: '/api',
  timeout: 30000,
})

// ---- 请求拦截器：自动注入 Token ----
request.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error),
)

// 用于防止短时间内重复弹出相同的错误提示
let lastErrorTime = 0
const ERROR_THROTTLE = 1000 

// ---- 响应拦截器：统一错误处理 ----
request.interceptors.response.use(
  (response) => response.data,
  (error) => {
    console.error('API Error:', error)
    const status = error.response?.status
    
    if (status === 401) {
      localStorage.removeItem('token')
      window.location.href = '/login'
      return Promise.reject(error)
    }

    const now = Date.now()
    if (now - lastErrorTime > ERROR_THROTTLE) {
      lastErrorTime = now
      
      let message = '请求失败'
      const detail = error.response?.data?.detail
      
      if (detail) {
        message = typeof detail === 'string' ? detail : JSON.stringify(detail)
      } else if (error.code === 'ERR_NETWORK') {
        message = '网络连接失败，请检查后端服务'
      } else if (error.code === 'ECONNABORTED') {
        message = '请求超时'
      } else if (status >= 500) {
        message = `服务器错误(${status})`
      } else if (error.message) {
        message = error.message
      }

      showToast({
        message,
        type: 'fail',
        duration: 3000,
      })
    }
    
    return Promise.reject(error)
  },
)

export default request

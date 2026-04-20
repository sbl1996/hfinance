/**
 * Axios 实例封装
 * - 统一 baseURL
 * - Token 拦截器（请求头自动注入）
 * - 401 响应自动跳转登录
 * - 全局错误处理
 */
import axios from 'axios'
import { showToast } from 'vant'

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

// ---- 响应拦截器：统一错误处理 ----
request.interceptors.response.use(
  (response) => response.data,
  (error) => {
    const status = error.response?.status
    if (status === 401) {
      // Token 过期或无效，清除并跳转登录
      localStorage.removeItem('token')
      // 使用 window.location 硬跳转，避免循环依赖
      window.location.href = '/login'
      return Promise.reject(error)
    }
    const message = error.response?.data?.detail || error.message || '请求失败'
    showToast(message)
    return Promise.reject(error)
  },
)

export default request

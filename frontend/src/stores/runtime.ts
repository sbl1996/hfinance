import { defineStore } from 'pinia'
import { ref } from 'vue'
import request from '@/utils/request'

export type RoutePolicy = 'DIRECT' | 'VPN'
export type RouteSource =
  | 'YAHOO' | 'XUEQIU' | 'EASTMONEY' | 'TENCENT' | 'FUTU'
  | 'AK_HK' | 'AK_FUND' | 'AK_A' | 'AK_US' | 'CHINAMONEY'
export type RoutePolicies = Record<RouteSource, RoutePolicy>
type RoutePoliciesResponse = { policies: RoutePolicies; proxy_url: string }

export const ROUTE_SOURCE_LABELS: Record<RouteSource, string> = {
  YAHOO: 'Yahoo Finance', XUEQIU: '雪球', EASTMONEY: '东方财富', TENCENT: '腾讯', FUTU: '富途',
  AK_HK: 'AKShare 港股', AK_FUND: 'AKShare 基金', AK_A: 'AKShare A股/ETF', AK_US: 'AKShare 美股', CHINAMONEY: '中国外汇交易中心',
}
export const ROUTE_SOURCES = Object.keys(ROUTE_SOURCE_LABELS) as RouteSource[]

export const useRuntimeStore = defineStore('runtime', () => {
  const policies = ref<RoutePolicies | null>(null)
  const proxyUrl = ref('')
  const loading = ref(false)
  const updating = ref(false)

  async function fetchRoutePolicies() {
    loading.value = true
    try {
      const data: RoutePoliciesResponse = await request.get('/market/route-policies')
      policies.value = data.policies
      proxyUrl.value = data.proxy_url
      return data
    } finally {
      loading.value = false
    }
  }

  async function setRoutePolicy(source: RouteSource, policy: RoutePolicy) {
    if (!policies.value) return
    updating.value = true
    const previous = policies.value[source]
    policies.value[source] = policy
    try {
      const data: RoutePoliciesResponse = await request.put('/market/route-policies', {
        policies: policies.value,
      })
      policies.value = data.policies
      proxyUrl.value = data.proxy_url
      return data
    } catch (error) {
      policies.value[source] = previous
      throw error
    } finally {
      updating.value = false
    }
  }

  return {
    policies,
    proxyUrl,
    loading,
    updating,
    fetchRoutePolicies,
    setRoutePolicy,
  }
})

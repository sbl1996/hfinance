import { defineStore } from 'pinia'
import { ref } from 'vue'
import request from '@/utils/request'

type ProxyStateResponse = {
  vpn_enabled: boolean
  proxy_url: string
}

export const useRuntimeStore = defineStore('runtime', () => {
  const vpnEnabled = ref(false)
  const proxyUrl = ref('')
  const loading = ref(false)
  const updating = ref(false)

  async function fetchProxyState() {
    loading.value = true
    try {
      const data: ProxyStateResponse = await request.get('/market/proxy-state')
      vpnEnabled.value = data.vpn_enabled
      proxyUrl.value = data.proxy_url
      return data
    } finally {
      loading.value = false
    }
  }

  async function setVpnEnabled(enabled: boolean) {
    updating.value = true
    try {
      const data: ProxyStateResponse = await request.post('/market/proxy-state', {
        vpn_enabled: enabled,
      })
      vpnEnabled.value = data.vpn_enabled
      proxyUrl.value = data.proxy_url
      return data
    } finally {
      updating.value = false
    }
  }

  return {
    vpnEnabled,
    proxyUrl,
    loading,
    updating,
    fetchProxyState,
    setVpnEnabled,
  }
})

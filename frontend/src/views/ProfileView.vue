<template>
  <div class="profile-page">
    <!-- 用户身份卡片 -->
    <div class="user-card">
      <div class="avatar-container">
        <van-icon name="contact-o" class="avatar-icon" />
      </div>
      <div class="user-info">
        <h2 class="user-role">{{ authStore.isGuest ? '安全访客' : '系统管理员' }}</h2>
        <p class="user-desc">
          {{ authStore.isGuest ? '拥有只读的随机缩放资产示范数据访问权' : '拥有全部资产配置、修改及后台任务运行权' }}
        </p>
      </div>
    </div>

    <!-- 系统信息列表 -->
    <van-cell-group inset class="info-group">
      <van-cell title="应用版本" icon="info-o" :value="'v' + version" />
      <van-cell center icon="shield-o">
        <template #title>
          <span>数据源路由策略</span>
          <div class="cell-desc">
            每个数据源可单独选择直连或 VPN；代理地址：{{ runtimeStore.proxyUrl || '加载中' }}
          </div>
        </template>
      </van-cell>
      <van-cell v-for="source in ROUTE_SOURCES" :key="source" center :title="ROUTE_SOURCE_LABELS[source]">
        <template #value>
          <van-radio-group
            direction="horizontal"
            :model-value="runtimeStore.policies?.[source]"
            :disabled="authStore.isGuest || runtimeStore.loading || runtimeStore.updating"
            @update:model-value="(value) => handleRoutePolicy(source, value)"
          >
            <van-radio name="DIRECT">直连</van-radio>
            <van-radio name="VPN">VPN</van-radio>
          </van-radio-group>
        </template>
      </van-cell>
      <van-cell title="检查更新" icon="passed" is-link @click="checkUpdate" />
    </van-cell-group>

    <!-- 退出登录按钮 -->
    <div class="action-container">
      <van-button
        type="danger"
        block
        round
        plain
        icon="log-out"
        class="logout-btn"
        @click="handleLogout"
      >
        退出登录
      </van-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { ROUTE_SOURCE_LABELS, ROUTE_SOURCES, type RoutePolicy, type RouteSource, useRuntimeStore } from '@/stores/runtime'
import { showDialog, showToast } from 'vant'

const version = __APP_VERSION__
const router = useRouter()
const authStore = useAuthStore()
const runtimeStore = useRuntimeStore()

onMounted(() => {
  runtimeStore.fetchRoutePolicies().catch(() => {
    // error toast is handled globally
  })
})

function checkUpdate() {
  showToast({
    message: '当前已是最新版本',
    type: 'success',
    duration: 1500
  })
}

async function handleRoutePolicy(source: RouteSource, policy: string | number) {
  if (policy !== 'DIRECT' && policy !== 'VPN') return
  try {
    await runtimeStore.setRoutePolicy(source, policy as RoutePolicy)
    showToast({
      message: `${ROUTE_SOURCE_LABELS[source]}已切换为${policy === 'VPN' ? 'VPN' : '直连'}`,
      type: 'success',
      duration: 1500
    })
  } catch {
    await runtimeStore.fetchRoutePolicies().catch(() => {
      // error toast is handled globally
    })
  }
}

function handleLogout() {
  showDialog({
    title: '提示',
    message: '确定要退出登录吗？',
    showCancelButton: true,
  }).then(async () => {
    authStore.logout()
    await router.replace({ name: 'Login' })
  }).catch(() => {
    // on cancel
  })
}
</script>

<style scoped>
.profile-page {
  padding: 16px 12px;
}

.user-card {
  background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
  border-radius: 16px;
  padding: 24px;
  color: white;
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 20px;
  box-shadow: 0 4px 12px rgba(30, 60, 114, 0.2);
}

.avatar-container {
  width: 56px;
  height: 56px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.2);
  display: flex;
  align-items: center;
  justify-content: center;
  backdrop-filter: blur(4px);
}

.avatar-icon {
  font-size: 32px;
  color: white;
}

.user-info {
  flex: 1;
  min-width: 0;
}

.user-role {
  font-size: 20px;
  font-weight: 600;
  margin: 0 0 6px 0;
}

.user-desc {
  font-size: 12px;
  opacity: 0.85;
  line-height: 1.4;
  margin: 0;
  word-break: break-all;
}

.info-group {
  margin: 0 !important;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
}

.cell-desc {
  margin-top: 4px;
  color: #969799;
  font-size: 12px;
  line-height: 1.4;
}

.action-container {
  margin-top: 32px;
  padding: 0 8px;
}

.logout-btn {
  border-width: 1.5px;
  font-weight: 500;
}
</style>

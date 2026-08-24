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

    <section class="route-panel">
      <div class="panel-heading">
        <div class="panel-icon"><van-icon name="guide-o" /></div>
        <div class="panel-heading-copy">
          <h3>数据源路由策略</h3>
          <p>按数据源选择网络出口，修改后立即生效</p>
        </div>
        <van-tag round type="primary" plain>{{ vpnCount }} 个 VPN</van-tag>
      </div>

      <div class="proxy-note">
        <van-icon name="shield-o" />
        <span>VPN 代理：{{ runtimeStore.proxyUrl || '加载中' }}</span>
      </div>

      <div v-for="group in routeGroups" :key="group.title" class="route-group">
        <div class="group-title"><span>{{ group.title }}</span><em>{{ group.sources.length }} 个来源</em></div>
        <div class="route-list">
          <div v-for="source in group.sources" :key="source" class="route-row">
            <div class="source-mark"><van-icon :name="source === 'YAHOO' ? 'bar-chart-o' : 'shop-o'" /></div>
            <div class="source-copy">
              <strong>{{ ROUTE_SOURCE_LABELS[source] }}</strong>
              <small>{{ sourceDescriptions[source] }}</small>
            </div>
            <van-radio-group
              class="route-choice"
              direction="horizontal"
              :model-value="runtimeStore.policies?.[source]"
              :disabled="authStore.isGuest || runtimeStore.loading || runtimeStore.updating"
              @update:model-value="(value) => handleRoutePolicy(source, value)"
            >
              <van-radio name="DIRECT">直连</van-radio>
              <van-radio name="VPN">VPN</van-radio>
            </van-radio-group>
          </div>
        </div>
      </div>

      <div v-if="authStore.isGuest" class="guest-hint"><van-icon name="info-o" /> 访客模式仅可查看，管理员可修改路由策略</div>
    </section>

    <van-cell-group inset class="info-group">
      <van-cell title="应用版本" icon="info-o" :value="'v' + version" />
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

const sourceDescriptions: Record<RouteSource, string> = {
  YAHOO: '国内指数优先使用的海外行情源', XUEQIU: '雪球行情与历史数据', EASTMONEY: '东方财富行情与净值',
  TENCENT: '腾讯行情页面', FUTU: '富途行情页面', AK_HK: 'AKShare 港股数据', AK_FUND: 'AKShare 基金净值',
  AK_A: 'AKShare A 股与 ETF', AK_US: 'AKShare 美股数据', CHINAMONEY: '外汇交易中心汇率',
}
const routeGroups = [
  { title: '网页行情源', sources: ['YAHOO', 'XUEQIU', 'EASTMONEY', 'TENCENT', 'FUTU'] as RouteSource[] },
  { title: 'AKShare 与官方数据', sources: ['AK_HK', 'AK_FUND', 'AK_A', 'AK_US', 'CHINAMONEY'] as RouteSource[] },
]
const vpnCount = computed(() => ROUTE_SOURCES.filter((source) => runtimeStore.policies?.[source] === 'VPN').length)

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
  padding: 16px 12px 24px;
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

.route-panel {
  margin-bottom: 16px;
  padding: 18px 14px 14px;
  background: #fff;
  border: 1px solid rgba(25, 137, 250, 0.08);
  border-radius: 16px;
  box-shadow: 0 4px 16px rgba(32, 57, 85, 0.06);
}

.panel-heading {
  display: flex;
  align-items: center;
  gap: 10px;
}

.panel-icon {
  width: 38px;
  height: 38px;
  display: grid;
  place-items: center;
  color: #1989fa;
  background: #eaf4ff;
  border-radius: 11px;
  font-size: 20px;
}

.panel-heading-copy {
  flex: 1;
  min-width: 0;
}

.panel-heading h3 {
  color: #323233;
  font-size: 16px;
  line-height: 22px;
  font-weight: 600;
}

.panel-heading p {
  margin-top: 2px;
  color: #969799;
  font-size: 12px;
}

.proxy-note {
  display: flex;
  align-items: center;
  gap: 6px;
  margin: 15px 0 12px;
  padding: 9px 10px;
  color: #64748b;
  background: #f7f9fc;
  border-radius: 8px;
  font-size: 12px;
}

.route-group + .route-group {
  margin-top: 18px;
}

.group-title {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin: 0 2px 7px;
  color: #646566;
  font-size: 12px;
  font-weight: 600;
}

.group-title em {
  color: #c8c9cc;
  font-size: 11px;
  font-style: normal;
  font-weight: 400;
}

.route-list {
  overflow: hidden;
  border: 1px solid #f0f1f3;
  border-radius: 11px;
}

.route-row {
  display: flex;
  align-items: center;
  gap: 9px;
  min-height: 60px;
  padding: 9px 10px;
  background: #fff;
}

.route-row + .route-row { border-top: 1px solid #f3f4f5; }

.source-mark {
  flex: 0 0 28px;
  width: 28px;
  height: 28px;
  display: grid;
  place-items: center;
  color: #1989fa;
  background: #f0f7ff;
  border-radius: 8px;
  font-size: 15px;
}

.source-copy { flex: 1; min-width: 0; }
.source-copy strong { display: block; color: #323233; font-size: 13px; font-weight: 500; }
.source-copy small { display: block; overflow: hidden; margin-top: 3px; color: #969799; font-size: 10px; line-height: 14px; text-overflow: ellipsis; white-space: nowrap; }

.route-choice { flex: 0 0 auto; }
.route-choice :deep(.van-radio) { gap: 3px; color: #646566; font-size: 11px; }
.route-choice :deep(.van-radio + .van-radio) { margin-left: 7px; }
.route-choice :deep(.van-radio__icon) { font-size: 15px; }

.guest-hint {
  display: flex;
  align-items: center;
  gap: 5px;
  margin: 12px 2px 0;
  color: #969799;
  font-size: 11px;
}

.info-group {
  margin: 0 !important;
  overflow: hidden;
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

<template>
  <router-view v-if="isLoginPage" />
  <div v-else class="app-container">
    <div class="app-content">
      <router-view />
    </div>
    <van-tabbar v-model="activeTab" route>
      <van-tabbar-item to="/dashboard" icon="chart-trending-o">总览</van-tabbar-item>
      <van-tabbar-item to="/investment" icon="bar-chart-o">投资</van-tabbar-item>
      <van-tabbar-item to="/accounting" icon="balance-o">记账</van-tabbar-item>
    </van-tabbar>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()
const activeTab = ref(0)

const isLoginPage = computed(() => route.path === '/login')
</script>

<style>
:root {
  --van-primary-color: #1989fa;
  --pnl-positive: #ee0a24;
  --pnl-negative: #07c160;
  --max-content-width: 480px;
}

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

html {
  /* 移动端字体基准：默认 16px，手机上 15px 会让 1rem 对应的 px 更合适 */
  font-size: 16px;
}

html, body, #app {
  height: 100%;
  min-height: 100dvh;
  width: 100%;
  overflow-x: hidden;
  font-family: -apple-system, BlinkMacSystemFont, 'Helvetica Neue', Helvetica, Segoe UI, Arial, Roboto, 'PingFang SC', 'miui', 'Hiragino Sans GB', 'Microsoft Yahei', sans-serif;
  background-color: #f7f8fa;
  -webkit-font-smoothing: antialiased;
}

.app-container {
  height: 100%;
  min-height: 100dvh;
  width: 100%;
  display: flex;
  flex-direction: column;
  position: relative;
  overflow: hidden;
}

.app-content {
  flex: 1;
  min-height: 0;
  width: 100%;
  overflow-y: auto;
  -webkit-overflow-scrolling: touch;
  padding-bottom: calc(56px + env(safe-area-inset-bottom) + 8px);
}

.van-tabbar {
  width: 100%;
  left: 0;
  right: 0;
  bottom: 0;
  padding-bottom: env(safe-area-inset-bottom);
  box-sizing: content-box;
}

/* 盈亏颜色 */
.pnl-positive {
  color: var(--pnl-positive) !important;
}

.pnl-negative {
  color: var(--pnl-negative) !important;
}

/* 移动端字体放大适配 */
@media screen and (max-width: 480px) {
  .overview-item .overview-label,
  .summary-label,
  .info-label,
  .legend-name,
  .section-total,
  .ring-label {
    font-size: 13px !important;
  }

  .overview-sub-value,
  .summary-value,
  .holding-pnl,
  .holding-name,
  .section-title,
  .card-title,
  .legend-value,
  .ring-total {
    font-size: 17px !important;
  }

  .overview-main .overview-value {
    font-size: 32px !important;
  }

  .holding-info-row {
    font-size: 14px !important;
  }

  .legend-item {
    font-size: 14px !important;
  }

  .empty-tip {
    font-size: 15px !important;
  }
}

@media screen and (min-width: 768px) {
  .app-container {
    max-width: var(--max-content-width);
    margin: 0 auto;
  }

  /* 桌面端保持内容区与底部导航同宽并居中 */
  .van-tabbar {
    max-width: var(--max-content-width);
    left: 50% !important;
    right: auto;
    transform: translateX(-50%);
  }
}
</style>

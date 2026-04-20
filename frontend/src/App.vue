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
}

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

html, body, #app {
  height: 100%;
  width: 100%;
  overflow-x: hidden;
  font-family: -apple-system, BlinkMacSystemFont, 'Helvetica Neue', Helvetica, Segoe UI, Arial, Roboto, 'PingFang SC', 'miui', 'Hiragino Sans GB', 'Microsoft Yahei', sans-serif;
  background-color: #f7f8fa;
  -webkit-font-smoothing: antialiased;
}

.app-container {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.app-content {
  flex: 1;
  overflow-y: auto;
  -webkit-overflow-scrolling: touch;
  padding-bottom: 8px;
}

/* 盈亏颜色 */
.pnl-positive {
  color: var(--pnl-positive) !important;
}

.pnl-negative {
  color: var(--pnl-negative) !important;
}
</style>

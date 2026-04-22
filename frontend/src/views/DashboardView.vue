<template>
  <div class="dashboard-page">
    <!-- 资产总览卡片 -->
    <OverviewCard :overview="dashboardStore.overview" :loading="dashboardStore.loading" />

    <!-- 资产分布 -->
    <DistributionChart :distribution="dashboardStore.distribution" />
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { useDashboardStore } from '@/stores/dashboard'
import OverviewCard from '@/components/OverviewCard.vue'
import DistributionChart from '@/components/DistributionChart.vue'

const dashboardStore = useDashboardStore()

onMounted(async () => {
  // 并行发起请求，不使用 await Promise.all 以免一个失败全部中断
  // 这里允许每个请求各自失败，错误由 axios 拦截器处理
  dashboardStore.fetchOverview().catch(() => {})
  dashboardStore.fetchDistribution().catch(() => {})
})
</script>

<style scoped>
.dashboard-page {
  padding: 12px;
}
</style>

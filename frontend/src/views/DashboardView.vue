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
  await Promise.all([
    dashboardStore.fetchOverview(),
    dashboardStore.fetchDistribution(),
  ])
})
</script>

<style scoped>
.dashboard-page {
  padding: 12px;
}
</style>

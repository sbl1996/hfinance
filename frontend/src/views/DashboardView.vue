<template>
  <div class="dashboard-page">
    <!-- 资产总览卡片 -->
    <OverviewCard :overview="dashboardStore.overview" :loading="dashboardStore.loading" />

    <!-- 资产分布 -->
    <DistributionChart :distribution="dashboardStore.distribution" />

    <!-- 盈亏日历 -->
    <PnlCalendar
      :calendar-data="dashboardStore.calendarData"
      @change-month="handleChangeMonth"
      @click-day="handleClickDay"
    />

    <!-- 日盈亏明细弹窗 -->
    <van-dialog
      v-model:show="showDayDetail"
      :title="dayDetailTitle"
      :show-confirm-button="false"
      close-on-click-overlay
    >
      <div class="day-detail-list">
        <div v-for="item in dayDetailData" :key="item.code" class="day-detail-item">
          <div class="day-detail-name">{{ item.name }}</div>
          <div class="day-detail-code">{{ item.code }}</div>
          <div :class="['day-detail-pnl', item.daily_pnl_cny > 0 ? 'pnl-positive' : item.daily_pnl_cny < 0 ? 'pnl-negative' : '']">
            {{ item.daily_pnl_cny > 0 ? '+' : '' }}{{ formatMoney(item.daily_pnl_cny, '', 2) }}
          </div>
        </div>
        <div v-if="dayDetailData.length === 0" class="day-detail-empty">暂无数据</div>
      </div>
      <p class="day-detail-hint">⚠️ 当日调仓可能会导致当日盈亏快照出现轻微偏差</p>
    </van-dialog>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useDashboardStore } from '@/stores/dashboard'
import { formatMoney } from '@/utils/format'
import request from '@/utils/request'
import OverviewCard from '@/components/OverviewCard.vue'
import DistributionChart from '@/components/DistributionChart.vue'
import PnlCalendar from '@/components/PnlCalendar.vue'

const dashboardStore = useDashboardStore()
const showDayDetail = ref(false)
const dayDetailTitle = ref('')
const dayDetailData = ref<any[]>([])

onMounted(async () => {
  await Promise.all([
    dashboardStore.fetchOverview(),
    dashboardStore.fetchDistribution(),
    dashboardStore.fetchCalendar(new Date().getFullYear(), new Date().getMonth() + 1),
  ])
})

function handleChangeMonth(year: number, month: number) {
  dashboardStore.fetchCalendar(year, month)
}

async function handleClickDay(date: string) {
  dayDetailTitle.value = `${date} 盈亏明细`
  try {
    const data: any = await request.get(`/dashboard/calendar/${date}`)
    dayDetailData.value = data
  } catch {
    dayDetailData.value = []
  }
  showDayDetail.value = true
}
</script>

<style scoped>
.dashboard-page {
  padding: 12px;
}

.day-detail-list {
  max-height: 50vh;
  overflow-y: auto;
}

.day-detail-item {
  display: flex;
  align-items: center;
  padding: 12px 16px;
  border-bottom: 1px solid #f5f5f5;
}

.day-detail-name {
  flex: 1;
  font-size: 14px;
  font-weight: 500;
}

.day-detail-code {
  font-size: 12px;
  color: #999;
  margin-right: 12px;
}

.day-detail-pnl {
  font-size: 14px;
  font-weight: 600;
}

.day-detail-empty {
  padding: 24px;
  text-align: center;
  color: #999;
}

.day-detail-hint {
  font-size: 11px;
  color: #999;
  text-align: center;
  padding: 8px 16px 12px;
}
</style>

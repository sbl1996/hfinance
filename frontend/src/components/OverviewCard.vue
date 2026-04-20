<template>
  <div class="overview-card">
    <van-loading v-if="loading" class="card-loading" />
    <template v-else-if="overview">
      <div class="overview-main">
        <div class="overview-label">净资产</div>
        <div class="overview-value">{{ formatMoney(overview.net_assets_cny) }}</div>
      </div>
      <div class="overview-row">
        <div class="overview-item">
          <div class="overview-label">总资产</div>
          <div class="overview-sub-value">{{ formatMoney(overview.total_assets_cny) }}</div>
        </div>
        <div class="overview-item">
          <div class="overview-label">总负债</div>
          <div class="overview-sub-value">{{ formatMoney(overview.total_liabilities_cny) }}</div>
        </div>
      </div>
      <div class="overview-row">
        <div class="overview-item">
          <div class="overview-label">今日盈亏</div>
          <div :class="['overview-sub-value', pnlColorClass(overview.daily_pnl_cny)]">
            {{ overview.daily_pnl_cny > 0 ? '+' : '' }}{{ formatMoney(overview.daily_pnl_cny) }}
          </div>
        </div>
        <div class="overview-item">
          <div class="overview-label">累计盈亏</div>
          <div :class="['overview-sub-value', pnlColorClass(overview.total_pnl_cny)]">
            {{ overview.total_pnl_cny > 0 ? '+' : '' }}{{ formatMoney(overview.total_pnl_cny) }}
          </div>
        </div>
      </div>
    </template>
    <div v-else class="card-empty">暂无数据</div>
  </div>
</template>

<script setup lang="ts">
import { formatMoney, pnlColorClass } from '@/utils/format'

defineProps<{
  overview: any
  loading: boolean
}>()
</script>

<style scoped>
.overview-card {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 12px;
  padding: 20px;
  color: white;
  margin-bottom: 12px;
}

.card-loading, .card-empty {
  text-align: center;
  padding: 24px;
}

.overview-main {
  text-align: center;
  margin-bottom: 16px;
}

.overview-main .overview-label {
  font-size: 14px;
  opacity: 0.8;
}

.overview-main .overview-value {
  font-size: 28px;
  font-weight: 700;
  margin-top: 4px;
  word-break: break-all;
}

.overview-row {
  display: flex;
  margin-top: 12px;
}

.overview-item {
  flex: 1;
}

.overview-item .overview-label {
  font-size: 13px;
  opacity: 0.7;
}

.overview-sub-value {
  font-size: 16px;
  font-weight: 600;
  margin-top: 2px;
}
</style>

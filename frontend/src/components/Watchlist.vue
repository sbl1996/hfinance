<template>
  <div class="watchlist">
    <div
      v-for="item in items"
      :key="item.id"
      class="watch-item"
    >
      <div class="watch-header">
        <div class="header-left">
          <span :class="['market-badge', `market-badge-${item.market?.toLowerCase?.() ?? 'default'}`]">
            {{ marketLabel(item.market) }}
          </span>
          <span class="watch-name">{{ item.name }}</span>
          <span class="watch-code">{{ item.code }}</span>
        </div>
        <div class="watch-actions">
          <span :class="['watch-growth', pnlColorClass(item.growth_rate)]">
            {{ item.growth_rate !== null && item.growth_rate !== undefined ? formatPercent(item.growth_rate) : '--' }}
          </span>
          <van-icon
            name="replay"
            size="18"
            :class="['action-refresh', { 'action-refreshing': refreshingCodes.has(item.code) }]"
            @click.stop="emit('refresh', item)"
          />
        </div>
      </div>
      <div class="watch-info">
        <div class="watch-info-row">
          <span class="info-label">最新价</span>
          <span class="info-value">
            {{ item.latest_price ?? '--' }} {{ item.price_currency ?? '' }}
          </span>
        </div>
        <div class="watch-info-row">
          <span class="info-label">日期</span>
          <span class="info-value">{{ item.price_date ?? '--' }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { formatPercent, pnlColorClass } from '@/utils/format'
import type { WatchlistItem } from '@/types/watchlist'

defineProps<{
  items: WatchlistItem[]
  refreshingCodes: Set<string>
}>()

const emit = defineEmits<{
  refresh: [item: WatchlistItem]
}>()

function marketLabel(market?: string | null) {
  if (market === 'A_STOCK') return 'A股'
  if (market === 'HK_STOCK') return '港股'
  if (market === 'FUND') return '基金'
  if (market === 'US_STOCK') return '美股'
  return '--'
}
</script>

<style scoped>
.watch-item {
  background: white;
  border-radius: 12px;
  padding: 14px;
  margin-bottom: 8px;
}

.watch-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
  min-width: 0;
}

.watch-name {
  font-size: 16px;
  font-weight: 600;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.watch-code {
  color: #969799;
  font-size: 12px;
  flex-shrink: 0;
}

.market-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 2px 7px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 600;
  line-height: 1;
  flex-shrink: 0;
}

.market-badge-a_stock {
  background: #e8f3ff;
  color: #1f6fd6;
}

.market-badge-hk_stock {
  background: #fff1e8;
  color: #d46b08;
}

.market-badge-fund {
  background: #edf8ee;
  color: #389e0d;
}

.market-badge-us_stock {
  background: #eef1ff;
  color: #4458c8;
}

.market-badge-default {
  background: #f2f3f5;
  color: #666;
}

.watch-actions {
  display: flex;
  gap: 8px;
  align-items: center;
  flex-shrink: 0;
}

.watch-growth {
  font-size: 15px;
  font-weight: 600;
  white-space: nowrap;
}

.watch-info {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 4px 12px;
}

.watch-info-row {
  display: flex;
  justify-content: space-between;
  font-size: 13px;
}

.info-label {
  color: #999;
}

.info-value {
  color: #333;
  font-weight: 500;
}

.action-refresh {
  color: #1989fa;
  cursor: pointer;
}

.action-refreshing {
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
</style>

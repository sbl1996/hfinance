<template>
  <div class="watchlist">
    <div
      v-for="item in items"
      :key="item.id"
      class="watch-item"
      @click="emit('view', item)"
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
          <van-icon
            name="replay"
            size="18"
            :class="['action-refresh', { 'action-refreshing': refreshingCodes.has(item.code) }]"
            @click.stop="emit('refresh', item)"
          />
          <van-icon
            name="arrow"
            size="18"
            class="action-enter"
          />
        </div>
      </div>
      <div class="watch-info">
        <span class="watch-summary">
          <span class="info-label">{{ latestPriceLabel(item.price_date) }}</span>
          <span class="info-value">{{ formattedPrice(item.latest_price, item.price_currency) }}</span>
          <span v-if="item.growth_rate !== null && item.growth_rate !== undefined" :class="['info-growth', pnlColorClass(item.growth_rate)]">
            ({{ formatPercent(item.growth_rate) }})
          </span>
          <span v-else class="info-growth">(--)</span>
        </span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { formatMonthDay, formatPercent, pnlColorClass } from '@/utils/format'
import type { WatchlistItem } from '@/types/watchlist'

defineProps<{
  items: WatchlistItem[]
  refreshingCodes: Set<string>
}>()

const emit = defineEmits<{
  view: [item: WatchlistItem]
  refresh: [item: WatchlistItem]
}>()

function marketLabel(market?: string | null) {
  if (market === 'A_STOCK') return 'A股'
  if (market === 'HK_STOCK') return '港股'
  if (market === 'FUND') return '基金'
  if (market === 'US_STOCK') return '美股'
  return '--'
}

function latestPriceLabel(priceDate?: string | null) {
  const monthDay = formatMonthDay(priceDate)
  return monthDay === '--' ? '最新价' : `${monthDay}最新价`
}

function formattedPrice(price?: number | null, currency?: string | null) {
  if (price === null || price === undefined) {
    return '--'
  }
  if (currency === 'USD') {
    return `$${price}`
  }
  if (currency === 'HKD') {
    return `${price} HKD`
  }
  return `${price}`
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
  gap: 10px;
  align-items: center;
  flex-shrink: 0;
}

.watch-info {
  display: flex;
  align-items: center;
}

.watch-summary {
  display: flex;
  align-items: baseline;
  gap: 6px;
  flex-wrap: wrap;
  font-size: 13px;
}

.info-label {
  color: #999;
}

.info-value {
  color: #333;
  font-weight: 500;
}

.info-growth {
  font-weight: 500;
}

.action-refresh {
  color: #1989fa;
  cursor: pointer;
}

.action-enter {
  color: #c8c9cc;
}

.action-refreshing {
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
</style>

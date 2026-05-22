<template>
  <div class="watchlist">
    <div
      v-for="item in items"
      :key="item.id"
      class="watch-item"
      @click="emit('view', item)"
    >
      <div class="watch-header">
        <div class="watch-main">
          <div class="watch-text">
            <div class="watch-title-row">
              <span class="watch-name">{{ item.name }}</span>
              <van-icon
                name="replay"
                size="18"
                :class="['action-refresh', { 'action-refreshing': refreshingCodes.has(item.code) }]"
                @click.stop="emit('refresh', item)"
              />
            </div>
            <div class="watch-meta">
              <span :class="['market-badge', `market-badge-${item.market?.toLowerCase?.() ?? 'default'}`]">
                {{ marketLabel(item.market) }}
              </span>
              <span class="watch-code">{{ item.code }}</span>
            </div>
          </div>
        </div>
        <div class="watch-side">
          <div class="watch-quote">
            <span :class="['watch-price', growthTextClass(item.growth_rate)]">{{ formattedPrice(item.latest_price, item.price_currency) }}</span>
            <span
              v-if="item.growth_rate !== null && item.growth_rate !== undefined"
              :class="['watch-growth', 'watch-growth-pill', growthPillClass(item.growth_rate)]"
            >
              {{ formatPercent(item.growth_rate) }}
            </span>
            <span v-else class="watch-growth watch-growth-pill watch-growth-neutral">--</span>
          </div>
        </div>
        <div class="watch-actions">
          <van-icon
            name="arrow"
            size="18"
            class="action-enter"
          />
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

function growthPillClass(value: number | null | undefined) {
  if (value === null || value === undefined || value === 0) {
    return 'watch-growth-neutral'
  }
  return value > 0 ? 'watch-growth-positive' : 'watch-growth-negative'
}

function growthTextClass(value: number | null | undefined) {
  if (value === null || value === undefined || value === 0) {
    return 'watch-price-neutral'
  }
  return value > 0 ? 'watch-price-positive' : 'watch-price-negative'
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
  gap: 10px;
}

.watch-main {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  flex: 1;
  min-width: 0;
}

.watch-text {
  min-width: 0;
  flex: 1;
}

.watch-title-row {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
}

.watch-name {
  display: block;
  font-size: 18px;
  font-weight: 700;
  line-height: 1.15;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.watch-meta {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: 8px;
}

.watch-code {
  color: #b5b9c2;
  font-size: 13px;
  flex-shrink: 0;
  letter-spacing: 0.02em;
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

.watch-side {
  display: flex;
  align-items: center;
  margin-left: auto;
}

.watch-quote {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

.watch-price {
  font-size: 22px;
  font-weight: 700;
  white-space: nowrap;
  letter-spacing: -0.02em;
}

.watch-price-positive {
  color: #ef4444;
}

.watch-price-negative {
  color: #16a34a;
}

.watch-price-neutral {
  color: #333;
}

.watch-growth {
  font-size: 15px;
  font-weight: 700;
  white-space: nowrap;
}

.watch-growth-pill {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 78px;
  padding: 6px 10px;
  border-radius: 12px;
  line-height: 1;
  box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.08);
}

.watch-growth-positive {
  background: linear-gradient(180deg, #ff6a63 0%, #ef4444 100%);
  color: #fff;
}

.watch-growth-negative {
  background: linear-gradient(180deg, #25b46b 0%, #16a34a 100%);
  color: #fff;
}

.watch-growth-neutral {
  background: #f2f3f5;
  color: #909399;
}

.watch-actions {
  display: flex;
  gap: 10px;
  align-items: center;
  flex-shrink: 0;
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

<template>
  <div class="holding-list">
    <div
      v-for="(h, index) in holdings"
      :key="h.id"
      :class="['holding-item', { 'holding-item-sort-mode': sortMode }]"
      @click="handleItemClick(h)"
      @touchstart.passive="startLongPress(h)"
      @touchend="cancelLongPress"
      @touchcancel="cancelLongPress"
      @mousedown="startLongPress(h)"
      @mouseup="cancelLongPress"
      @mouseleave="cancelLongPress"
    >
      <div class="holding-header">
        <div class="header-left">
          <span :class="['market-badge', `market-badge-${h.market?.toLowerCase?.() ?? 'default'}`]">
            {{ marketLabel(h.market) }}
          </span>
          <span class="holding-name">{{ h.name }}</span>
          <span v-if="h.ignored" class="ignored-badge">已忽略</span>
        </div>
        <div class="holding-actions">
          <template v-if="sortMode">
            <van-icon
              name="arrow-up"
              size="18"
              :class="['action-sort', { 'action-disabled': index === 0 }]"
              @click.stop="index > 0 && emit('moveUp', h)"
            />
            <van-icon
              name="arrow-down"
              size="18"
              :class="['action-sort', { 'action-disabled': index === holdings.length - 1 }]"
              @click.stop="index < holdings.length - 1 && emit('moveDown', h)"
            />
          </template>
          <template v-else>
            <span :class="['holding-pnl', pnlColorClass(h.pnl_cny)]">
              {{ h.pnl_cny > 0 ? '+' : '' }}{{ formatMoney(h.pnl_cny) }}
            </span>
            <van-icon
              name="replay"
              size="18"
              :class="['action-refresh', { 'action-refreshing': refreshingCodes.has(h.code) }]"
              @click.stop="$emit('refresh', h)"
            />
          </template>
        </div>
      </div>
      <div class="holding-info">
        <div class="holding-info-row">
          <span class="info-label">市值</span>
          <span class="info-value">{{ formatMoney(h.market_value_cny) }}</span>
        </div>
        <div class="holding-info-row">
          <span class="info-label">最新价</span>
          <span class="info-value">{{ h.latest_price ?? '--' }} {{ h.price_currency === 'HKD' ? 'HKD' : '' }}</span>
        </div>
        <div class="holding-info-row">
          <span class="info-label">累计收益率</span>
          <span :class="['info-value', pnlColorClass(h.pnl_rate)]">
            {{ h.pnl_rate !== null && h.pnl_rate !== undefined ? formatPercent(h.pnl_rate) : '--' }}
          </span>
        </div>
        <div class="holding-info-row">
          <span class="info-label">数量</span>
          <span class="info-value">{{ h.quantity }}</span>
        </div>
        <div class="holding-info-row">
          <span class="info-label">{{ growthRateLabel(h.price_date) }}</span>
          <span :class="['info-value', pnlColorClass(h.growth_rate)]">
            {{ h.growth_rate !== null && h.growth_rate !== undefined ? formatPercent(h.growth_rate) : '--' }}
          </span>
        </div>
        <div class="holding-info-row">
          <span class="info-label">收益</span>
          <span :class="['info-value', pnlColorClass(h.growth_pnl_cny)]">
            {{ h.growth_pnl_cny !== null && h.growth_pnl_cny !== undefined ? formatMoney(h.growth_pnl_cny) : '--' }}
          </span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { formatMoney, formatMonthDay, formatPercent, pnlColorClass } from '@/utils/format'

const props = defineProps<{
  holdings: any[]
  refreshingCodes: Set<string>
  sortMode: boolean
}>()

const emit = defineEmits<{
  edit: [holding: any]
  refresh: [holding: any]
  enterSortMode: [holding: any]
  moveUp: [holding: any]
  moveDown: [holding: any]
}>()

let longPressTimer: number | null = null

function startLongPress(holding: any) {
  if (longPressTimer !== null) {
    window.clearTimeout(longPressTimer)
  }
  longPressTimer = window.setTimeout(() => {
    emit('enterSortMode', holding)
    longPressTimer = null
  }, 2000)
}

function cancelLongPress() {
  if (longPressTimer !== null) {
    window.clearTimeout(longPressTimer)
    longPressTimer = null
  }
}

function handleItemClick(holding: any) {
  cancelLongPress()
  if (!props.sortMode) {
    emit('edit', holding)
  }
}

function growthRateLabel(priceDate?: string | null) {
  const monthDay = formatMonthDay(priceDate)
  return monthDay === '--' ? '收益率' : `${monthDay}收益率`
}

function marketLabel(market?: string | null) {
  if (market === 'A_STOCK') {
    return 'A股'
  }
  if (market === 'HK_STOCK') {
    return '港股'
  }
  if (market === 'FUND') {
    return '基金'
  }
  return '--'
}
</script>

<style scoped>
.holding-item {
  background: white;
  border-radius: 12px;
  padding: 14px;
  margin-bottom: 8px;
  position: relative;
  user-select: none;
}

.holding-item-sort-mode {
  border: 1px solid #c9d8f5;
  box-shadow: inset 0 0 0 1px rgba(25, 137, 250, 0.08);
}

.holding-header {
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

.holding-name {
  font-size: 16px;
  font-weight: 600;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
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

.market-badge-default {
  background: #f2f3f5;
  color: #666;
}

.ignored-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 2px 7px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 600;
  line-height: 1;
  color: #8c6d1f;
  background: #fff7e6;
  flex-shrink: 0;
}

.holding-pnl {
  font-size: 15px;
  font-weight: 600;
  white-space: nowrap;
  flex-shrink: 0;
}

.holding-info {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 4px 12px;
}

.holding-info-row {
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

.holding-actions {
  display: flex;
  gap: 8px;
  align-items: center;
  flex-shrink: 0;
}

.action-refresh {
  color: #1989fa;
  cursor: pointer;
}

.action-sort {
  color: #1989fa;
  cursor: pointer;
}

.action-disabled {
  color: #c8c9cc;
  cursor: not-allowed;
}

.action-refreshing {
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
</style>

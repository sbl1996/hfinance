<template>
  <div class="holding-list">
    <div v-for="h in holdings" :key="h.id" class="holding-item" @click="$emit('edit', h)">
      <div class="holding-header">
        <div class="header-left">
          <span class="holding-name">{{ h.name }}</span>
          <van-tag v-if="h.is_stale" type="warning" size="medium" class="stale-tag">数据陈旧</van-tag>
        </div>
        <span :class="['holding-pnl', pnlColorClass(h.pnl_cny)]">
          {{ h.pnl_cny > 0 ? '+' : '' }}{{ formatMoney(h.pnl_cny) }}
        </span>
        <div class="holding-actions">
          <van-icon
            name="replay"
            size="18"
            :class="['action-refresh', { 'action-refreshing': refreshingCodes.has(h.code) }]"
            @click.stop="$emit('refresh', h)"
          />
        </div>
      </div>
      <div class="holding-info">
        <div class="holding-info-row">
          <span class="info-label">代码</span>
          <span class="info-value">{{ h.code }}</span>
        </div>
        <div class="holding-info-row">
          <span class="info-label">数量</span>
          <span class="info-value">{{ h.quantity }}</span>
        </div>
        <div class="holding-info-row">
          <span class="info-label">最新价</span>
          <span class="info-value">{{ h.latest_price ?? '--' }} {{ h.price_currency === 'HKD' ? 'HKD' : '' }}</span>
        </div>
        <div class="holding-info-row">
          <span class="info-label">日增长率</span>
          <span :class="['info-value', pnlColorClass(h.growth_rate)]">
            {{ h.growth_rate !== null && h.growth_rate !== undefined ? formatPercent(h.growth_rate) : '--' }}
          </span>
        </div>
        <div class="holding-info-row">
          <span class="info-label">市值(CNY)</span>
          <span class="info-value">{{ formatMoney(h.market_value_cny) }}</span>
        </div>
        <div class="holding-info-row">
          <span class="info-label">收益率</span>
          <span :class="['info-value', pnlColorClass(h.pnl_rate)]">
            {{ h.pnl_rate !== null && h.pnl_rate !== undefined ? formatPercent(h.pnl_rate) : '--' }}
          </span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { formatMoney, formatPercent, pnlColorClass } from '@/utils/format'

defineProps<{
  holdings: any[]
  refreshingCodes: Set<string>
}>()

defineEmits<{
  edit: [holding: any]
  refresh: [holding: any]
}>()
</script>

<style scoped>
.holding-item {
  background: white;
  border-radius: 12px;
  padding: 14px;
  margin-bottom: 8px;
  position: relative;
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

.stale-tag {
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

.action-refreshing {
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
</style>

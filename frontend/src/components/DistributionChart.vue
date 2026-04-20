<template>
  <div class="distribution-card" v-if="distribution">
    <h3 class="card-title">资产分布</h3>
    <div class="chart-container">
      <div class="ring-chart" :style="ringStyle">
        <div class="ring-inner">
          <div class="ring-total">{{ formatMoney(totalValue) }}</div>
          <div class="ring-label">总资产</div>
        </div>
      </div>
      <div class="chart-legend">
        <div v-for="item in distribution.items" :key="item.name" class="legend-item">
          <span class="legend-dot" :style="{ background: colorMap[item.name] }"></span>
          <span class="legend-name">{{ item.name }}</span>
          <span class="legend-value">{{ formatMoney(item.value_cny) }}</span>
          <span class="legend-percent">{{ item.percent.toFixed(1) }}%</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { formatMoney } from '@/utils/format'

const props = defineProps<{
  distribution: any
}>()

const colorMap: Record<string, string> = {
  '现金': '#1989fa',
  '投资': '#ff976a',
  '负债': '#ee0a24',
}

const totalValue = computed(() => {
  if (!props.distribution?.items) return 0
  return props.distribution.items.reduce((sum: number, i: any) => sum + (i.name === '负债' ? 0 : i.value_cny), 0)
})

const ringStyle = computed(() => {
  if (!props.distribution?.items) return {}
  const items = props.distribution.items
  const total = items.reduce((s: number, i: any) => s + i.percent, 0)
  let gradParts: string[] = []
  let current = 0
  for (const item of items) {
    const pct = (item.percent / total) * 100
    const color = colorMap[item.name] || '#ccc'
    gradParts.push(`${color} ${current}% ${current + pct}%`)
    current += pct
  }
  return {
    background: `conic-gradient(${gradParts.join(', ')})`,
  }
})
</script>

<style scoped>
.distribution-card {
  background: white;
  border-radius: 12px;
  padding: 16px;
  margin-bottom: 12px;
}

.card-title {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 16px;
}

.chart-container {
  display: flex;
  align-items: center;
  gap: 24px;
}

.ring-chart {
  width: 120px;
  height: 120px;
  border-radius: 50%;
  flex-shrink: 0;
  position: relative;
}

.ring-inner {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 72px;
  height: 72px;
  border-radius: 50%;
  background: white;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

.ring-total {
  font-size: 14px;
  font-weight: 700;
}

.ring-label {
  font-size: 10px;
  color: #999;
}

.chart-legend {
  flex: 1;
}

.legend-item {
  display: flex;
  align-items: center;
  margin-bottom: 8px;
  font-size: 13px;
}

.legend-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  margin-right: 6px;
  flex-shrink: 0;
}

.legend-name {
  flex: 1;
  color: #666;
}

.legend-value {
  margin-right: 8px;
  font-weight: 500;
}

.legend-percent {
  color: #999;
  width: 48px;
  text-align: right;
}
</style>

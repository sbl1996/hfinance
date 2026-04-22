<template>
  <div class="distribution-card" v-if="distribution">
    <h3 class="card-title">资产分布</h3>
    <div class="chart-content">
      <div class="ring-wrapper">
        <div class="ring-chart" :style="ringStyle">
          <div class="ring-inner">
            <div :class="['ring-total', { 'small-font': totalValueStr.length > 10 }]">
              {{ totalValueStr }}
            </div>
            <div class="ring-label">总资产</div>
          </div>
        </div>
      </div>
      <div class="chart-legend">
        <div v-for="item in distribution.items" :key="item.name" class="legend-item">
          <div class="legend-left">
            <span class="legend-dot" :style="{ background: colorMap[item.name] }"></span>
            <span class="legend-name">{{ item.name }}</span>
          </div>
          <div class="legend-right">
            <span class="legend-value">{{ formatMoney(item.value_cny) }}</span>
            <span class="legend-percent">{{ item.percent.toFixed(1) }}%</span>
          </div>
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

// 饼图中间的数字，如果是整数则不显示小数
const totalValueStr = computed(() => {
  const val = totalValue.value
  return formatMoney(val, '¥', val % 1 === 0 ? 0 : 2)
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

.chart-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 24px;
  padding: 8px 0;
}

.ring-wrapper {
  flex-shrink: 0;
}

.ring-chart {
  width: 170px;
  height: 170px;
  border-radius: 50%;
  position: relative;
}

.ring-inner {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 120px;
  height: 120px;
  border-radius: 50%;
  background: white;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 8px;
  box-shadow: inset 0 0 8px rgba(0, 0, 0, 0.05);
}

.ring-total {
  font-size: 20px;
  font-weight: 700;
  color: #323233;
  width: 110%; /* 允许轻微超出 ring-inner 容器以利用视觉边缘 */
  text-align: center;
  white-space: nowrap;
  letter-spacing: -0.5px;
}

.ring-total.small-font {
  font-size: 16px;
}

.ring-label {
  font-size: 12px;
  color: #969799;
  margin-top: 2px;
}

.chart-legend {
  width: 100%;
  min-width: 0;
  padding: 0 4px;
}

.legend-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  padding-bottom: 8px;
  border-bottom: 1px solid #f7f8fa;
}

.legend-item:last-child {
  margin-bottom: 0;
  padding-bottom: 0;
  border-bottom: none;
}

.legend-left {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
}

.legend-right {
  display: flex;
  align-items: baseline;
  gap: 8px;
}

.legend-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  flex-shrink: 0;
}

.legend-name {
  font-size: 14px;
  color: #646566;
}

.legend-value {
  font-size: 15px;
  font-weight: 600;
  color: #323233;
}

.legend-percent {
  font-size: 12px;
  color: #969799;
  min-width: 42px;
  text-align: right;
}
</style>

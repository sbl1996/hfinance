<template>
  <div class="detail-page">
    <van-nav-bar
      :title="pageTitle"
      left-arrow
      @click-left="router.back()"
    />

    <van-loading v-if="loading" class="page-loading" />
    <van-empty v-else-if="error" description="加载失败" />

    <template v-else-if="data">
      <!-- 走势图区域 -->
      <div class="chart-section">
        <div ref="chartContainerRef" class="chart-container"></div>
        <div v-if="data.empty" class="chart-empty">暂无历史数据</div>
        <div class="range-bar">
          <button
            v-for="r in RANGES"
            :key="r.key"
            :class="['range-btn', { 'range-btn-active': activeRange === r.key }]"
            @click="handleRangeChange(r.key)"
          >
            {{ r.label }}
          </button>
        </div>
      </div>

      <div class="info-card">
        <div class="info-header">
          <span :class="['market-badge', `market-badge-${data.market?.toLowerCase?.() ?? 'default'}`]">
            {{ marketLabel(data.market) }}
          </span>
          <span class="info-name">{{ data.name }}</span>
          <span class="info-code">{{ data.code }}</span>
        </div>
        <div class="info-grid">
          <div class="info-row">
            <span class="info-label">最新价</span>
            <span class="info-value">{{ data.latest_price ?? '--' }} {{ data.price_currency ?? '' }}</span>
          </div>
          <div class="info-row">
            <span class="info-label">{{ growthRateLabel(data.price_date) }}</span>
            <span :class="['info-value', pnlColorClass(data.growth_rate)]">
              {{ data.growth_rate !== null ? formatPercent(data.growth_rate) : '--' }}
            </span>
          </div>
          <div class="info-row info-row-full">
            <span class="info-label">加入时间</span>
            <span class="info-value">{{ data.created_at }}</span>
          </div>
        </div>
      </div>

      <div class="action-bar">
        <van-button block round type="primary" @click="openEditForm">编辑自选</van-button>
        <van-button
          v-if="supportsHistoryImport(data.market)"
          block
          round
          plain
          type="primary"
          :loading="importingHistory"
          @click="handleImportHistory(data)"
        >
          全量导入净值
        </van-button>
        <van-button block round plain type="danger" @click="handleDelete">删除自选</van-button>
      </div>
    </template>

    <WatchlistForm
      v-model:show="showForm"
      :item="editingItem"
      :importing-history="importingHistory"
      @submit="handleFormSubmit"
      @delete="handleDeleteFromForm"
      @import-history="handleImportHistory"
    />
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onUnmounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { showConfirmDialog } from 'vant'
import { createChart, ColorType, AreaSeries, LineSeries } from 'lightweight-charts'
import { useWatchlistStore } from '@/stores/watchlist'
import { formatMonthDay, formatPercent, pnlColorClass } from '@/utils/format'
import type { WatchlistItem } from '@/types/watchlist'
import WatchlistForm from '@/components/WatchlistForm.vue'

const route = useRoute()
const router = useRouter()
const watchlistStore = useWatchlistStore()

const watchlistId = Number(route.params.id)
const loading = ref(true)
const error = ref(false)
const data = ref<any | null>(null)

const RANGES = [
  { key: '1M', label: '1月', days: 30 },
  { key: '3M', label: '3月', days: 90 },
  { key: '6M', label: '6月', days: 180 },
  { key: '1Y', label: '1年', days: 365 },
  { key: 'ALL', label: '全部', days: Infinity },
] as const

const chartContainerRef = ref<HTMLDivElement | null>(null)
const activeRange = ref<string>('1Y')
let chart: ReturnType<typeof createChart> | null = null

const showForm = ref(false)
const editingItem = ref<WatchlistItem | null>(null)
const importingHistory = ref(false)

const pageTitle = computed(() => data.value?.name ?? '自选详情')

function marketLabel(market?: string | null) {
  if (market === 'A_STOCK') return 'A股'
  if (market === 'HK_STOCK') return '港股'
  if (market === 'FUND') return '基金'
  if (market === 'US_STOCK') return '美股'
  return '--'
}

function growthRateLabel(priceDate?: string | null) {
  const monthDay = formatMonthDay(priceDate)
  return monthDay === '--' ? '涨跌幅' : `${monthDay}涨跌幅`
}

function supportsHistoryImport(market?: string | null) {
  return market === 'FUND' || market === 'US_STOCK'
}

function formatDateToEST(date: Date): string {
  const y = date.getFullYear()
  const m = String(date.getMonth() + 1).padStart(2, '0')
  const d = String(date.getDate()).padStart(2, '0')
  return `${y}-${m}-${d}`
}

function handleRangeChange(key: string) {
  activeRange.value = key
  if (!chart || !data.value || data.value.history.length === 0) return

  if (key === 'ALL') {
    chart.timeScale().fitContent()
    return
  }

  const range = RANGES.find((r) => r.key === key)
  if (!range) return

  const now = new Date()
  const from = new Date(now.getTime() - range.days * 24 * 60 * 60 * 1000)
  const fromStr = formatDateToEST(from)

  const lastItem = data.value.history[data.value.history.length - 1]
  chart.timeScale().setVisibleRange({
    from: fromStr,
    to: lastItem.date,
  })
}

function initChart() {
  if (!chartContainerRef.value || !data.value || data.value.empty) return

  if (chart) {
    chart.remove()
    chart = null
  }

  const container = chartContainerRef.value
  
  // 价格货币格式化配置：如 $ 或者 HKD 等
  const currency = data.value.price_currency
  let priceFormat: any = { type: 'price', precision: 2 }
  
  if (currency === 'USD') {
    priceFormat = {
      type: 'custom',
      formatter: (price: number) => `$${price.toFixed(2)}`,
    }
  } else if (currency === 'HKD') {
    priceFormat = {
      type: 'custom',
      formatter: (price: number) => `${price.toFixed(2)} HKD`,
    }
  }

  chart = createChart(container, {
    layout: {
      background: { type: ColorType.Solid, color: '#ffffff' },
      textColor: '#999',
      attributionLogo: false,
    },
    width: container.clientWidth,
    height: 320,
    leftPriceScale: { visible: true, borderColor: '#e5e5e5' },
    rightPriceScale: { visible: true, borderColor: '#e5e5e5' },
    grid: {
      vertLines: { color: '#f5f5f5' },
      horzLines: { color: '#f5f5f5' },
    },
    timeScale: { borderColor: '#e5e5e5' },
  })

  const priceSeries = chart.addSeries(AreaSeries, {
    priceScaleId: 'left',
    lineColor: '#1989fa',
    topColor: 'rgba(25, 137, 250, 0.2)',
    bottomColor: 'rgba(25, 137, 250, 0.02)',
    lineWidth: 2,
    priceFormat,
  })

  const yieldSeries = chart.addSeries(LineSeries, {
    priceScaleId: 'right',
    color: '#07c160',
    lineWidth: 1,
    lastValueVisible: true,
    priceFormat: { type: 'percent' },
  })

  const priceData = data.value.history.map((item: any) => ({
    time: item.date,
    value: item.price,
  }))

  const yieldData = data.value.history
    .filter((item: any) => item.yield_rate !== null && item.yield_rate !== undefined)
    .map((item: any) => ({
      time: item.date,
      value: item.yield_rate,
    }))

  priceSeries.setData(priceData)
  if (yieldData.length > 0) {
    yieldSeries.setData(yieldData)
  }
  chart.timeScale().fitContent()
}

watch([loading, data], async ([isLoading, newData]) => {
  if (isLoading || !newData || newData.empty) return

  await nextTick()
  initChart()
}, { flush: 'post' })

onUnmounted(() => {
  if (chart) {
    chart.remove()
    chart = null
  }
})

async function fetchData() {
  loading.value = true
  error.value = false
  try {
    data.value = await watchlistStore.fetchPriceHistory(watchlistId)
  } catch {
    error.value = true
  } finally {
    loading.value = false
  }
}

function openEditForm() {
  editingItem.value = data.value ? { ...data.value } : null
  showForm.value = true
}

async function handleFormSubmit(formData: { code: string; name: string; market: any }) {
  await watchlistStore.updateWatchlistItem(watchlistId, formData)
  showForm.value = false
  editingItem.value = null
  await fetchData()
}

async function handleDelete() {
  try {
    await showConfirmDialog({ title: '确认删除', message: `确定删除自选「${data.value?.name}」？` })
    await watchlistStore.deleteWatchlistItem(watchlistId)
    router.back()
  } catch { /* cancelled */ }
}

async function handleDeleteFromForm(item: WatchlistItem) {
  try {
    await showConfirmDialog({ title: '确认删除', message: `确定删除自选「${item.name}」？` })
    await watchlistStore.deleteWatchlistItem(item.id)
    showForm.value = false
    router.back()
  } catch { /* cancelled */ }
}

async function handleImportHistory(item: WatchlistItem) {
  importingHistory.value = true
  try {
    await watchlistStore.importFundHistory(item.id)
    await fetchData()
  } finally {
    importingHistory.value = false
  }
}

fetchData()
</script>

<style scoped>
.detail-page {
  min-height: 100vh;
  background: #f7f8fa;
  padding-bottom: 24px;
}

.page-loading {
  display: flex;
  justify-content: center;
  padding: 80px 0;
}

.chart-section {
  background: white;
  margin: 0 0 12px;
  padding: 12px;
  position: relative;
}

.chart-container {
  width: 100%;
  height: 320px;
}

.chart-empty {
  height: 320px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #999;
  font-size: 15px;
}

.range-bar {
  display: flex;
  gap: 8px;
  justify-content: center;
  margin-top: 8px;
}

.range-btn {
  padding: 4px 14px;
  border: 1px solid #e5e5e5;
  border-radius: 999px;
  background: white;
  color: #666;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.15s;
}

.range-btn-active {
  background: #1989fa;
  color: white;
  border-color: #1989fa;
}

.info-card {
  background: white;
  margin: 0 12px 12px;
  border-radius: 12px;
  padding: 16px;
}

.info-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
}

.info-name {
  font-size: 16px;
  font-weight: 600;
}

.info-code {
  font-size: 13px;
  color: #999;
}

.info-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px 16px;
}

.info-row {
  display: flex;
  justify-content: space-between;
  font-size: 13px;
  gap: 12px;
}

.info-row-full {
  grid-column: 1 / -1;
}

.info-label {
  color: #999;
}

.info-value {
  color: #333;
  font-weight: 500;
  text-align: right;
  word-break: break-all;
}

.action-bar {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 0 12px;
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
</style>

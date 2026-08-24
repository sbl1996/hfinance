<template>
  <div class="detail-page">
    <!-- 顶部导航栏 -->
    <van-nav-bar
      :title="pageTitle"
      left-arrow
      @click-left="router.back()"
    />

    <!-- 加载状态 -->
    <van-loading v-if="loading" class="page-loading" />

    <!-- 错误状态 -->
    <van-empty v-else-if="error" description="加载失败" />

    <!-- 正常内容 -->
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

      <!-- 持仓信息卡片 -->
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
            <span class="info-value">{{ formattedPrice(data.current_price_native ?? data.current_price, data.price_currency) }}</span>
          </div>
          <div class="info-row">
            <span class="info-label">持有数量</span>
            <span class="info-value">{{ data.quantity }}</span>
          </div>
          <div class="info-row">
            <span class="info-label">成本总额</span>
            <span class="info-value">{{ formatMoney(data.cost_total_cny) }}</span>
          </div>
          <div class="info-row">
            <span class="info-label">单位成本{{ unitCostCurrencySuffix }}</span>
            <button
              :class="['info-value', 'cost-toggle', { 'cost-toggle-enabled': canToggleUnitCost }]"
              type="button"
              :disabled="!canToggleUnitCost"
              @click="toggleUnitCostCurrency"
            >
              {{ displayedUnitCost }}
              <span v-if="canToggleUnitCost" class="cost-toggle-hint">点按切换</span>
            </button>
          </div>
          <div class="info-row">
            <span class="info-label">市值</span>
            <span class="info-value">{{ formatMoney(data.market_value_cny) }}</span>
          </div>
          <div class="info-row">
            <span class="info-label">累计盈亏</span>
            <span :class="['info-value', pnlColorClass(data.pnl_cny)]">
              {{ formatSignedMoney(data.pnl_cny) }}
              <span v-if="data.pnl_rate !== null" class="pnl-percent">
                ({{ formatPercent(data.pnl_rate) }})
              </span>
            </span>
          </div>
          <div class="info-row">
            <span class="info-label">{{ growthRateLabel(data.price_date) }}</span>
            <span :class="['info-value', pnlColorClass(data.growth_rate)]">
              {{ data.growth_rate !== null ? formatPercent(data.growth_rate) : '--' }}
            </span>
          </div>
          <div class="info-row">
            <span class="info-label">当日盈亏</span>
            <span :class="['info-value', pnlColorClass(data.growth_pnl_cny)]">
              {{ data.growth_pnl_cny !== null ? formatSignedMoney(data.growth_pnl_cny) : '--' }}
            </span>
          </div>
        </div>
      </div>

      <!-- 卖出预警 -->
      <div v-if="!authStore.isGuest || data.alert_enabled || data.warning_active" class="alert-card">
        <div class="alert-header">
          <div>
            <div class="alert-title">卖出预警</div>
            <div class="alert-subtitle">每个持仓每天最多触发一次</div>
          </div>
          <van-switch
            v-if="!authStore.isGuest"
            v-model="alertForm.enabled"
            size="22px"
          />
          <span v-else class="alert-readonly-state">{{ data.alert_enabled ? '已启用' : '未启用' }}</span>
        </div>

        <template v-if="!authStore.isGuest">
          <van-field
            v-model="alertForm.takeProfitPercent"
            type="number"
            inputmode="decimal"
            label="止盈收益率"
            placeholder="例如 20"
            right-icon="percentage"
          />
          <van-field
            v-model="alertForm.stopLossPercent"
            type="number"
            inputmode="decimal"
            label="止损收益率"
            placeholder="例如 -10"
            right-icon="percentage"
          />
        </template>

        <div class="alert-status-row">
          <span>当前状态</span>
          <span :class="['alert-status', { 'alert-status-active': data.warning_active }]">
            {{ alertStatusText }}
          </span>
        </div>
        <div v-if="data.warning_triggered_at" class="alert-status-row">
          <span>触发时间</span>
          <span>{{ data.warning_triggered_at }}</span>
        </div>
        <div v-if="data.last_webhook_status" class="alert-status-row">
          <span>飞书通知</span>
          <span>{{ webhookStatusText }}</span>
        </div>
        <div v-if="data.last_webhook_status === 'FAILED' && data.last_webhook_error" class="alert-webhook-error">
          {{ data.last_webhook_error }}
        </div>

        <div v-if="!authStore.isGuest" class="alert-actions">
          <van-button
            block
            round
            type="primary"
            :loading="savingAlert"
            @click="handleSaveAlert"
          >
            保存预警设置
          </van-button>
          <van-button
            v-if="data.warning_active"
            block
            round
            plain
            type="warning"
            :loading="acknowledgingAlert"
            @click="handleAcknowledgeAlert"
          >
            我知道了，关闭本次警告
          </van-button>
          <van-button
            block
            round
            plain
            size="small"
            :loading="resettingAlert"
            @click="handleResetAlert"
          >
            调试：重置今日触发限制
          </van-button>
        </div>
      </div>

      <!-- 操作按钮 -->
      <div class="action-bar">
        <van-button block round type="primary" @click="openEditForm">编辑持仓</van-button>
        <van-button
          v-if="data.market === 'FUND'"
          block
          round
          plain
          type="primary"
          :loading="importingHistory"
          @click="handleImportHistory"
        >
          全量导入净值
        </van-button>
        <van-button
          block
          round
          plain
          type="warning"
          :loading="updatingIgnored"
          @click="handleToggleIgnored"
        >
          {{ data.ignored ? '取消忽略盈亏统计' : '忽略盈亏统计' }}
        </van-button>
        <van-button block round plain type="danger" @click="handleDelete">删除持仓</van-button>
      </div>
    </template>

    <!-- 编辑持仓弹窗 -->
    <HoldingForm
      v-model:show="showForm"
      :holding="editingHolding"
      @submit="handleFormSubmit"
    />
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { showConfirmDialog, showSuccessToast, showToast } from 'vant'
import { createChart, ColorType, LineStyle, AreaSeries, LineSeries } from 'lightweight-charts'
import { useHoldingStore } from '@/stores/holding'
import { useAuthStore } from '@/stores/auth'
import { formatMoney, formatPercent, formatMonthDay, pnlColorClass } from '@/utils/format'
import type { HoldingAlertSettings, HoldingWarningType, PriceHistoryResponse } from '@/types/holding'
import HoldingForm from '@/components/HoldingForm.vue'

type HoldingDetailData = PriceHistoryResponse & {
  ignored: boolean
  alert_enabled: boolean
  take_profit_rate: number | null
  stop_loss_rate: number | null
  warning_active: boolean
  warning_type: HoldingWarningType | null
  warning_triggered_at: string | null
  last_trigger_date: string | null
  last_webhook_status: string | null
  last_webhook_error: string | null
}

const route = useRoute()
const router = useRouter()
const holdingStore = useHoldingStore()
const authStore = useAuthStore()

const RANGES = [
  { key: '1M', label: '1月', days: 30 },
  { key: '3M', label: '3月', days: 90 },
  { key: '6M', label: '6月', days: 180 },
  { key: '1Y', label: '1年', days: 365 },
  { key: 'ALL', label: '全部', days: Infinity },
] as const

const chartContainerRef = ref<HTMLDivElement | null>(null)
const loading = ref(true)
const error = ref(false)
const data = ref<HoldingDetailData | null>(null)
const activeRange = ref<string>('1Y')

const showForm = ref(false)
const editingHolding = ref<any>(null)
const importingHistory = ref(false)
const updatingIgnored = ref(false)
const savingAlert = ref(false)
const acknowledgingAlert = ref(false)
const resettingAlert = ref(false)
const showNativeUnitCost = ref(true)
const alertForm = reactive({
  enabled: false,
  takeProfitPercent: '',
  stopLossPercent: '',
})

let chart: ReturnType<typeof createChart> | null = null

const holdingId = Number(route.params.id)
const pageTitle = computed(() => data.value?.name ?? '持仓详情')
const alertStatusText = computed(() => {
  if (data.value?.warning_active) {
    return data.value.warning_type === 'STOP_LOSS' ? '止损已触发' : '止盈已触发'
  }
  return data.value?.alert_enabled ? '监控中' : '未启用'
})
const webhookStatusText = computed(() => {
  const status = data.value?.last_webhook_status
  if (status === 'SUCCESS') return '发送成功'
  if (status === 'FAILED') return '发送失败'
  if (status === 'DISABLED') return '未配置 Webhook'
  return '--'
})

function marketLabel(market?: string | null) {
  if (market === 'A_STOCK') return 'A股'
  if (market === 'HK_STOCK') return '港股'
  if (market === 'FUND') return '基金'
  return '--'
}

function growthRateLabel(priceDate?: string | null) {
  const monthDay = formatMonthDay(priceDate)
  return monthDay === '--' ? '涨跌幅' : `${monthDay}涨跌幅`
}

function formatSignedMoney(value: number | null | undefined) {
  const amount = value ?? 0
  return `${amount > 0 ? '+' : ''}${formatMoney(amount)}`
}

function formattedPrice(price?: number | null, currency?: string | null) {
  if (price === null || price === undefined) {
    return '--'
  }
  const displayPrice = price.toFixed(4).replace(/\.?0+$/, '')
  if (currency === 'USD') {
    return `$${displayPrice}`
  }
  if (currency === 'HKD') {
    return `${displayPrice} HKD`
  }
  return displayPrice
}

function formattedCurrencyAmount(value?: number | null, currency?: string | null) {
  if (value === null || value === undefined) return '--'
  if (currency === 'CNY' || !currency) return formatMoney(value)
  return formattedPrice(value, currency)
}

const nativeCostCurrency = computed(() => data.value?.unit_cost_native_currency)
const canToggleUnitCost = computed(() => (
  nativeCostCurrency.value !== null
  && nativeCostCurrency.value !== undefined
  && nativeCostCurrency.value !== 'CNY'
  && data.value?.unit_cost_native !== null
  && data.value?.unit_cost_native !== undefined
))
const unitCostCurrencySuffix = computed(() => {
  if (showNativeUnitCost.value && canToggleUnitCost.value) {
    return `（${nativeCostCurrency.value}）`
  }
  return '（CNY）'
})
const displayedUnitCost = computed(() => {
  if (showNativeUnitCost.value && canToggleUnitCost.value) {
    return formattedCurrencyAmount(data.value?.unit_cost_native, nativeCostCurrency.value)
  }
  return formatMoney(data.value?.unit_cost ?? null)
})

function toggleUnitCostCurrency() {
  if (canToggleUnitCost.value) showNativeUnitCost.value = !showNativeUnitCost.value
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

watch([loading, data], async ([isLoading, newData]) => {
  if (isLoading || !newData || newData.empty) return

  await nextTick()
  initChart()
}, { flush: 'post' })

async function fetchData() {
  loading.value = true
  error.value = false
  try {
    const [detail, alert] = await Promise.all([
      holdingStore.fetchPriceHistory(holdingId),
      holdingStore.fetchHoldingAlert(holdingId),
    ])
    if (holdingStore.holdings.length === 0) {
      await holdingStore.fetchHoldings()
    }
    const holding = holdingStore.holdings.find((item: any) => item.id === holdingId)
    data.value = {
      ...detail,
      ignored: holding?.ignored ?? false,
      alert_enabled: alert.enabled,
      take_profit_rate: alert.take_profit_rate,
      stop_loss_rate: alert.stop_loss_rate,
      warning_active: alert.warning_active,
      warning_type: alert.warning_type,
      warning_triggered_at: alert.warning_triggered_at,
      last_trigger_date: alert.last_trigger_date,
      last_webhook_status: alert.last_webhook_status,
      last_webhook_error: alert.last_webhook_error,
    }
    applyAlertForm(alert)
    showNativeUnitCost.value = true
  } catch {
    error.value = true
  } finally {
    loading.value = false
  }
}

function percentInput(value: number | null) {
  return value === null ? '' : Number((value * 100).toFixed(4)).toString()
}

function applyAlertForm(alert: HoldingAlertSettings) {
  alertForm.enabled = alert.enabled
  alertForm.takeProfitPercent = percentInput(alert.take_profit_rate)
  alertForm.stopLossPercent = percentInput(alert.stop_loss_rate)
}

function parseOptionalPercent(value: string): number | null {
  if (!value.trim()) return null
  const parsed = Number(value)
  return Number.isFinite(parsed) ? parsed / 100 : null
}

async function handleSaveAlert() {
  const takeProfitRate = parseOptionalPercent(alertForm.takeProfitPercent)
  const stopLossRate = parseOptionalPercent(alertForm.stopLossPercent)
  if (alertForm.takeProfitPercent.trim() && takeProfitRate === null) {
    showToast('请输入有效的止盈收益率')
    return
  }
  if (alertForm.stopLossPercent.trim() && stopLossRate === null) {
    showToast('请输入有效的止损收益率')
    return
  }
  if (takeProfitRate !== null && takeProfitRate <= 0) {
    showToast('止盈收益率必须大于 0')
    return
  }
  if (stopLossRate !== null && stopLossRate >= 0) {
    showToast('止损收益率必须小于 0')
    return
  }
  if (alertForm.enabled && takeProfitRate === null && stopLossRate === null) {
    showToast('启用预警时至少填写一条预警线')
    return
  }

  savingAlert.value = true
  try {
    await holdingStore.updateHoldingAlert(holdingId, {
      enabled: alertForm.enabled,
      take_profit_rate: takeProfitRate,
      stop_loss_rate: stopLossRate,
    })
    await fetchData()
    showSuccessToast('预警设置已保存')
  } finally {
    savingAlert.value = false
  }
}

async function handleAcknowledgeAlert() {
  acknowledgingAlert.value = true
  try {
    await holdingStore.acknowledgeHoldingAlert(holdingId)
    await fetchData()
    showSuccessToast('本次警告已关闭')
  } finally {
    acknowledgingAlert.value = false
  }
}

async function handleResetAlert() {
  resettingAlert.value = true
  try {
    await holdingStore.resetHoldingAlert(holdingId)
    await fetchData()
    showSuccessToast('已重置，下次刷新可再次触发')
  } finally {
    resettingAlert.value = false
  }
}

function initChart() {
  if (!chartContainerRef.value || !data.value || data.value.empty) return

  if (chart) {
    chart.remove()
    chart = null
  }

  const container = chartContainerRef.value
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
  })

  const costLine = chart.addSeries(LineSeries, {
    priceScaleId: 'left',
    color: '#ff8c00',
    lineWidth: 1,
    lineStyle: LineStyle.Dashed,
    lastValueVisible: false,
  })

  const yieldSeries = chart.addSeries(LineSeries, {
    priceScaleId: 'right',
    color: '#07c160',
    lineWidth: 1,
    lastValueVisible: true,
    priceFormat: { type: 'percent' },
  })

  const history = data.value.history
  const priceData: { time: string; value: number }[] = []
  const yieldData: { time: string; value: number }[] = []
  const hasYield = history.some((h) => h.yield_rate !== null)

  for (const item of history) {
    priceData.push({ time: item.date, value: item.price })
    if (hasYield && item.yield_rate !== null) {
      yieldData.push({ time: item.date, value: item.yield_rate })
    }
  }

  priceSeries.setData(priceData)
  costLine.setData([
    { time: priceData[0].time, value: data.value.unit_cost },
    { time: priceData[priceData.length - 1].time, value: data.value.unit_cost },
  ])
  if (yieldData.length > 0) {
    yieldSeries.setData(yieldData)
  }

  chart.timeScale().fitContent()
}

async function openEditForm() {
  // 确保 holdings 已加载，以获取 ignored 等字段
  if (holdingStore.holdings.length === 0) {
    await holdingStore.fetchHoldings()
  }
  const holding = holdingStore.holdings.find((h: any) => h.id === holdingId)
  editingHolding.value = data.value ? {
    id: holdingId,
    code: data.value.code,
    name: data.value.name,
    market: data.value.market,
    currency: data.value.currency,
    quantity: data.value.quantity,
    cost_total_cny: data.value.cost_total_cny,
    ignored: holding?.ignored ?? false,
  } : null
  showForm.value = true
}

async function handleFormSubmit(formData: any) {
  await holdingStore.updateHolding(holdingId, formData)
  editingHolding.value = null
  await fetchData()
}

async function handleDelete() {
  try {
    await showConfirmDialog({ title: '确认删除', message: `确定删除持仓「${data.value?.name}」？` })
    await holdingStore.deleteHolding(holdingId)
    router.back()
  } catch { /* cancelled */ }
}

async function handleImportHistory() {
  importingHistory.value = true
  try {
    await holdingStore.importFundHistory(holdingId)
    await fetchData()
  } finally {
    importingHistory.value = false
  }
}

async function handleToggleIgnored() {
  if (!data.value) return
  updatingIgnored.value = true
  try {
    await holdingStore.updateHoldingIgnored(holdingId, !data.value.ignored)
    await fetchData()
  } finally {
    updatingIgnored.value = false
  }
}

onMounted(() => {
  fetchData()
})

onUnmounted(() => {
  if (chart) {
    chart.remove()
    chart = null
  }
})
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

.alert-card {
  background: white;
  margin: 0 12px 12px;
  border-radius: 12px;
  padding: 16px;
}

.alert-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
}

.alert-title {
  font-size: 16px;
  font-weight: 600;
}

.alert-subtitle,
.alert-readonly-state {
  margin-top: 2px;
  color: #969799;
  font-size: 12px;
}

.alert-status-row {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  padding: 8px 0;
  color: #646566;
  font-size: 13px;
}

.alert-status {
  color: #969799;
  font-weight: 600;
}

.alert-status-active {
  color: #ed6a0c;
}

.alert-actions {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-top: 10px;
}

.alert-webhook-error {
  padding: 8px 10px;
  border-radius: 8px;
  color: #ee0a24;
  background: #fff1f0;
  font-size: 12px;
  word-break: break-word;
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
}

.info-label {
  color: #999;
}

.info-value {
  color: #333;
  font-weight: 500;
  text-align: right;
}

.cost-toggle {
  appearance: none;
  border: 0;
  background: transparent;
  padding: 0;
  font: inherit;
  color: inherit;
  text-align: right;
}

.cost-toggle-enabled {
  cursor: pointer;
}

.cost-toggle-hint {
  display: block;
  margin-top: 2px;
  color: #969799;
  font-size: 11px;
  font-weight: normal;
}

.pnl-percent {
  font-size: 12px;
  color: #999;
}

.action-bar {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 0 12px;
}

</style>

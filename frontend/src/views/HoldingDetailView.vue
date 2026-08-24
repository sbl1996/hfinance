<template>
  <div :class="['detail-page', { 'detail-page-warning': data?.warning_active }]">
    <van-nav-bar
      title="持仓详情"
      left-arrow
      @click-left="router.back()"
      @click-right="showActionSheet = true"
    >
      <template v-if="!authStore.isGuest" #right>
        <van-icon name="ellipsis" size="22" color="#323233" />
      </template>
    </van-nav-bar>

    <van-loading v-if="loading" class="page-loading" />
    <van-empty v-else-if="error" description="加载失败" />

    <template v-else-if="data">
      <div class="detail-content">
        <section :class="['summary-card', { 'summary-card-warning': data.warning_active }]">
          <div class="security-header">
            <span :class="['market-badge', `market-badge-${data.market?.toLowerCase?.() ?? 'default'}`]">
              {{ marketLabel(data.market) }}
            </span>
            <div class="security-title-wrap">
              <h1>{{ data.name }}</h1>
              <span>{{ data.code }}</span>
            </div>
          </div>

          <div class="summary-pnl-label">累计盈亏</div>
          <div :class="['summary-pnl', pnlColorClass(data.pnl_cny)]">
            <strong>{{ formatSignedMoney(data.pnl_cny) }}</strong>
            <span v-if="data.pnl_rate !== null">
              <b v-if="data.warning_active" class="summary-warning-tag">[{{ warningShortLabel }}]</b>{{ formatSignedPercent(data.pnl_rate) }}
            </span>
          </div>

          <div class="summary-metrics">
            <div class="summary-metric">
              <span>市值</span>
              <strong>{{ formatMoney(data.market_value_cny) }}</strong>
            </div>
            <div class="summary-metric">
              <span>持仓成本</span>
              <strong>{{ formatMoney(data.cost_total_cny) }}</strong>
            </div>
            <div class="summary-metric">
              <span>最新价</span>
              <strong>{{ formattedPrice(data.current_price_native ?? data.current_price, data.price_currency) }}</strong>
            </div>
            <div class="summary-metric">
              <span>当日盈亏</span>
              <strong :class="pnlColorClass(data.growth_pnl_cny)">
                {{ data.growth_pnl_cny !== null ? formatSignedMoney(data.growth_pnl_cny) : '--' }}
              </strong>
            </div>
          </div>
        </section>

        <section class="chart-card">
          <div class="section-heading">
            <strong>收益走势</strong>
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
          <div v-if="!data.empty" ref="chartContainerRef" class="chart-container"></div>
          <div v-else class="chart-empty">暂无历史数据</div>
        </section>

        <section
          v-if="!authStore.isGuest || data.alert_enabled || data.warning_active"
          :class="['alert-summary-card', { 'alert-summary-card-active': data.warning_active }]"
        >
          <div class="alert-summary-header">
            <div class="alert-summary-icon">
              <van-icon :name="data.warning_active ? 'warning-o' : 'bullhorn-o'" size="18" />
            </div>
            <div class="alert-summary-heading">
              <strong>卖出预警</strong>
              <span>{{ alertSubtitle }}</span>
            </div>
            <span :class="['alert-status-pill', { 'alert-status-pill-active': data.warning_active }]">
              {{ alertStatusText }}
            </span>
          </div>

          <div class="alert-thresholds">
            <div>
              <span>止盈线</span>
              <strong>{{ configuredRate(data.take_profit_rate) }}</strong>
            </div>
            <div>
              <span>止损线</span>
              <strong>{{ configuredRate(data.stop_loss_rate) }}</strong>
            </div>
          </div>

          <template v-if="data.alert_enabled && data.take_profit_rate !== null && data.pnl_rate !== null">
            <div class="alert-progress-labels">
              <span>当前 {{ formatSignedPercent(data.pnl_rate) }}</span>
              <span>目标 {{ formatSignedPercent(data.take_profit_rate) }}</span>
            </div>
            <div class="alert-progress-track">
              <div :style="{ width: `${takeProfitProgress}%` }"></div>
            </div>
          </template>

          <div v-if="data.last_webhook_status === 'FAILED' && data.last_webhook_error" class="alert-webhook-error">
            飞书发送失败：{{ data.last_webhook_error }}
          </div>

          <button v-if="!authStore.isGuest" type="button" class="alert-adjust-button" @click="openAlertEditor">
            调整预警
          </button>
        </section>

        <section class="details-card">
          <button type="button" class="details-toggle" @click="detailsExpanded = !detailsExpanded">
            <span>
              <strong>持仓明细</strong>
              <small>数量、单位成本及统计设置</small>
            </span>
            <van-icon :name="detailsExpanded ? 'arrow-up' : 'arrow-down'" color="#969799" />
          </button>
          <div v-if="detailsExpanded" class="details-grid">
            <div>
              <span>持有数量</span>
              <strong>{{ data.quantity }}</strong>
            </div>
            <div>
              <span>单位成本{{ unitCostCurrencySuffix }}</span>
              <button
                :class="['detail-cost-value', { 'detail-cost-value-enabled': canToggleUnitCost }]"
                type="button"
                :disabled="!canToggleUnitCost"
                @click="toggleUnitCostCurrency"
              >
                {{ displayedUnitCost }}
              </button>
            </div>
            <div>
              <span>{{ growthRateLabel(data.price_date) }}</span>
              <strong :class="pnlColorClass(data.growth_rate)">
                {{ data.growth_rate !== null ? formatPercent(data.growth_rate) : '--' }}
              </strong>
            </div>
            <div>
              <span>盈亏统计</span>
              <strong>{{ data.ignored ? '已忽略' : '已计入' }}</strong>
            </div>
          </div>
        </section>
      </div>

      <div v-if="!authStore.isGuest" class="primary-action-bar">
        <van-button
          block
          round
          :type="data.warning_active ? 'warning' : 'primary'"
          :loading="data.warning_active ? acknowledgingAlert : false"
          @click="data.warning_active ? handleAcknowledgeAlert() : openEditForm()"
        >
          {{ data.warning_active ? '我知道了，关闭本次警告' : '编辑持仓' }}
        </van-button>
      </div>

      <van-action-sheet
        v-model:show="showActionSheet"
        :actions="actionSheetActions"
        cancel-text="取消"
        close-on-click-action
        @select="handleActionSelect"
      />

      <van-popup
        v-model:show="showAlertEditor"
        position="bottom"
        round
        :style="{ maxHeight: '82vh' }"
      >
        <div class="alert-editor">
          <div class="alert-editor-header">
            <div>
              <h3>卖出预警</h3>
              <p>每个持仓每天最多触发一次</p>
            </div>
            <van-switch v-model="alertForm.enabled" size="22px" />
          </div>

          <van-field
            v-model="alertForm.takeProfitPercent"
            type="number"
            inputmode="decimal"
            label="止盈收益率"
            placeholder="例如 20"
          >
            <template #right-icon>%</template>
          </van-field>
          <van-field
            v-model="alertForm.stopLossPercent"
            type="number"
            inputmode="decimal"
            label="止损收益率"
            placeholder="例如 -10"
          >
            <template #right-icon>%</template>
          </van-field>

          <div class="alert-editor-status">
            <span>当前状态</span>
            <strong :class="{ 'alert-editor-status-active': data.warning_active }">{{ alertStatusText }}</strong>
          </div>
          <div v-if="data.warning_triggered_at" class="alert-editor-status">
            <span>触发时间</span>
            <strong>{{ data.warning_triggered_at }}</strong>
          </div>
          <div v-if="data.last_webhook_status" class="alert-editor-status">
            <span>飞书通知</span>
            <strong>{{ webhookStatusText }}</strong>
          </div>

          <div class="alert-editor-actions">
            <van-button block round type="primary" :loading="savingAlert" @click="handleSaveAlert">
              保存预警设置
            </van-button>
            <van-button block plain round :loading="resettingAlert" @click="handleResetAlert">
              调试：重置今日触发限制
            </van-button>
          </div>
        </div>
      </van-popup>
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
const showActionSheet = ref(false)
const showAlertEditor = ref(false)
const detailsExpanded = ref(false)
const alertForm = reactive({
  enabled: false,
  takeProfitPercent: '',
  stopLossPercent: '',
})

let chart: ReturnType<typeof createChart> | null = null

const holdingId = Number(route.params.id)
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
const warningShortLabel = computed(() => (
  data.value?.warning_type === 'STOP_LOSS' ? '止损' : '止盈'
))
const alertSubtitle = computed(() => {
  if (data.value?.warning_active) {
    return data.value.last_webhook_status === 'SUCCESS'
      ? '已发送飞书提醒，等待处理'
      : '预警已触发，等待处理'
  }
  return data.value?.alert_enabled ? '每日最多提醒一次' : '设置止盈止损卖出线'
})
const takeProfitProgress = computed(() => {
  const currentRate = data.value?.pnl_rate
  const targetRate = data.value?.take_profit_rate
  if (currentRate === null || currentRate === undefined || !targetRate || targetRate <= 0) return 0
  return Math.max(0, Math.min(100, (currentRate / targetRate) * 100))
})
const actionSheetActions = computed(() => {
  if (!data.value) return []
  const actions: Array<{ name: string; key: string; color?: string; loading?: boolean }> = [
    { name: '编辑持仓', key: 'edit' },
  ]
  if (data.value.market === 'FUND') {
    actions.push({ name: '全量导入净值', key: 'import', loading: importingHistory.value })
  }
  actions.push({
    name: data.value.ignored ? '取消忽略盈亏统计' : '忽略盈亏统计',
    key: 'ignored',
    loading: updatingIgnored.value,
  })
  actions.push({ name: '删除持仓', key: 'delete', color: '#ee0a24' })
  return actions
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

function formatSignedPercent(value: number | null | undefined) {
  if (value === null || value === undefined) return '--'
  return `${value > 0 ? '+' : ''}${formatPercent(value)}`
}

function configuredRate(value: number | null) {
  return value === null ? '未设置' : formatSignedPercent(value)
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
    showAlertEditor.value = false
    showSuccessToast('预警设置已保存')
  } finally {
    savingAlert.value = false
  }
}

function openAlertEditor() {
  if (!data.value) return
  alertForm.enabled = data.value.alert_enabled
  alertForm.takeProfitPercent = percentInput(data.value.take_profit_rate)
  alertForm.stopLossPercent = percentInput(data.value.stop_loss_rate)
  showAlertEditor.value = true
}

function handleActionSelect(action: { key: string }) {
  if (action.key === 'edit') {
    void openEditForm()
  } else if (action.key === 'import') {
    void handleImportHistory()
  } else if (action.key === 'ignored') {
    void handleToggleIgnored()
  } else if (action.key === 'delete') {
    void handleDelete()
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
    height: 190,
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
  padding-bottom: 12px;
  background: #f5f6f8;
}

.page-loading {
  display: flex;
  justify-content: center;
  padding: 80px 0;
}

.detail-content {
  padding: 12px 12px 8px;
}

.summary-card,
.chart-card,
.alert-summary-card,
.details-card {
  overflow: hidden;
  margin-bottom: 10px;
  border: 1px solid #ebedf0;
  border-radius: 16px;
  background: #fff;
  box-shadow: 0 3px 12px rgba(32, 44, 64, 0.035);
}

.summary-card {
  padding: 16px;
  transition: border-color 0.2s, background 0.2s;
}

.summary-card-warning {
  border-color: #ffd1c7;
  background: #fffaf8;
}

.security-header {
  display: flex;
  align-items: flex-start;
  gap: 9px;
  min-width: 0;
}

.security-title-wrap {
  min-width: 0;
}

.security-title-wrap h1 {
  overflow: hidden;
  margin: 0;
  color: #202124;
  font-size: 17px;
  font-weight: 650;
  line-height: 1.35;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.security-title-wrap span {
  color: #969799;
  font-size: 12px;
}

.summary-pnl-label {
  margin-top: 20px;
  color: #7d8490;
  font-size: 12px;
}

.summary-pnl {
  display: flex;
  align-items: baseline;
  gap: 9px;
  margin-top: 2px;
}

.summary-pnl strong {
  font-size: 29px;
  font-weight: 700;
  letter-spacing: -0.7px;
}

.summary-pnl > span {
  font-size: 15px;
  font-weight: 650;
}

.summary-warning-tag {
  margin-right: 2px;
  color: #ed6a0c;
}

.summary-metrics {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 14px 16px;
  margin-top: 20px;
  padding-top: 15px;
  border-top: 1px solid #edf0f4;
}

.summary-metric {
  display: flex;
  flex-direction: column;
  gap: 3px;
  min-width: 0;
}

.summary-metric span {
  color: #8a919c;
  font-size: 11px;
}

.summary-metric strong {
  overflow: hidden;
  color: #323233;
  font-size: 14px;
  font-weight: 600;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.chart-card {
  padding: 14px 12px 6px;
}

.section-heading {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.section-heading > strong {
  flex-shrink: 0;
  font-size: 15px;
}

.range-bar {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 12px;
}

.range-btn {
  border: 0;
  padding: 2px 0;
  color: #969799;
  background: transparent;
  font-size: 11px;
  cursor: pointer;
}

.range-btn-active {
  color: #1989fa;
  font-weight: 650;
}

.chart-container {
  width: 100%;
  height: 190px;
  margin-top: 4px;
}

.chart-empty {
  height: 120px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #969799;
  font-size: 13px;
}

.alert-summary-card {
  padding: 14px;
  transition: border-color 0.2s, background 0.2s;
}

.alert-summary-card-active {
  border-color: #ffb7a8;
  background: #fff8f5;
  box-shadow: inset 4px 0 0 #f06a4f;
}

.alert-summary-header {
  display: flex;
  align-items: center;
  gap: 10px;
}

.alert-summary-icon {
  display: grid;
  place-items: center;
  flex: 0 0 34px;
  width: 34px;
  height: 34px;
  border-radius: 10px;
  color: #1989fa;
  background: #eef5ff;
}

.alert-summary-card-active .alert-summary-icon {
  color: #d84a32;
  background: #ffebe6;
}

.alert-summary-heading {
  display: flex;
  flex: 1;
  flex-direction: column;
  min-width: 0;
}

.alert-summary-heading strong {
  font-size: 15px;
}

.alert-summary-heading span {
  overflow: hidden;
  color: #969799;
  font-size: 10px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.alert-status-pill {
  flex-shrink: 0;
  padding: 4px 8px;
  border-radius: 999px;
  color: #2374d8;
  background: #eef5ff;
  font-size: 11px;
  font-weight: 650;
}

.alert-status-pill-active {
  color: #c83e28;
  background: #ffebe6;
}

.alert-thresholds {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
  margin-top: 14px;
}

.alert-thresholds > div {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  padding: 10px 11px;
  border-radius: 10px;
  background: #f7f8fa;
}

.alert-thresholds span {
  color: #838b96;
  font-size: 11px;
}

.alert-thresholds strong {
  font-size: 13px;
}

.alert-progress-labels {
  display: flex;
  justify-content: space-between;
  margin-top: 12px;
  color: #818995;
  font-size: 10px;
}

.alert-progress-track {
  overflow: hidden;
  height: 5px;
  margin-top: 5px;
  border-radius: 99px;
  background: #e9edf2;
}

.alert-progress-track > div {
  height: 100%;
  border-radius: inherit;
  background: #1989fa;
  transition: width 0.2s;
}

.alert-summary-card-active .alert-progress-track > div {
  background: #e95f43;
}

.alert-adjust-button {
  width: 100%;
  margin-top: 13px;
  border: 0;
  border-top: 1px solid #edf0f4;
  padding: 11px 0 0;
  color: #1989fa;
  background: transparent;
  cursor: pointer;
  font-size: 13px;
  font-weight: 600;
}

.alert-webhook-error {
  margin-top: 10px;
  padding: 8px 10px;
  border-radius: 8px;
  color: #ee0a24;
  background: #fff1f0;
  font-size: 12px;
  word-break: break-word;
}

.details-card {
  padding: 0;
}

.details-toggle {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  border: 0;
  padding: 14px 15px;
  color: #323233;
  background: transparent;
  cursor: pointer;
}

.details-toggle > span {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 2px;
}

.details-toggle strong {
  font-size: 14px;
}

.details-toggle small {
  color: #969799;
  font-size: 10px;
}

.details-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 14px 16px;
  padding: 2px 15px 15px;
  border-top: 1px solid #f2f3f5;
}

.details-grid > div {
  display: flex;
  flex-direction: column;
  gap: 3px;
  padding-top: 12px;
}

.details-grid span {
  color: #969799;
  font-size: 11px;
}

.details-grid strong,
.detail-cost-value {
  color: #323233;
  font-size: 13px;
  font-weight: 600;
  text-align: left;
}

.detail-cost-value {
  width: fit-content;
  border: 0;
  padding: 0;
  background: transparent;
}

.detail-cost-value-enabled {
  color: #1989fa;
  cursor: pointer;
}

.primary-action-bar {
  padding: 0 12px 12px;
}

.alert-editor {
  overflow-y: auto;
  padding: 20px 16px calc(20px + env(safe-area-inset-bottom));
}

.alert-editor-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}

.alert-editor-header h3 {
  margin: 0;
  font-size: 18px;
}

.alert-editor-header p {
  margin: 3px 0 0;
  color: #999;
  font-size: 12px;
}

.alert-editor-status {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 10px 16px;
  color: #646566;
  font-size: 13px;
}

.alert-editor-status strong {
  text-align: right;
}

.alert-editor-status-active {
  color: #ed6a0c;
}

.alert-editor-actions {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-top: 14px;
}

@media screen and (max-width: 360px) {
  .summary-pnl strong {
    font-size: 26px;
  }

  .range-bar {
    gap: 9px;
  }
}
</style>

<template>
  <div class="investment-page">
    <!-- 持仓汇总 -->
    <div class="summary-card">
      <div class="summary-row">
        <div
          :class="['summary-item', 'summary-item-clickable', { 'summary-item-active': activeBreakdownMetric === 'marketValue' }]"
          role="button"
          tabindex="0"
          @click="toggleBreakdown('marketValue')"
          @keydown.enter="toggleBreakdown('marketValue')"
          @keydown.space.prevent="toggleBreakdown('marketValue')"
        >
          <div class="summary-label">持仓市值</div>
          <div class="summary-value">{{ formatMoney(holdingStore.summary.total_market_value_cny) }}</div>
        </div>
        <div
          :class="['summary-item', 'summary-item-clickable', { 'summary-item-active': activeBreakdownMetric === 'totalPnl' }]"
          role="button"
          tabindex="0"
          @click="toggleBreakdown('totalPnl')"
          @keydown.enter="toggleBreakdown('totalPnl')"
          @keydown.space.prevent="toggleBreakdown('totalPnl')"
        >
          <div class="summary-label">累计盈亏</div>
          <div :class="['summary-value', pnlColorClass(holdingStore.summary.total_pnl_cny)]">
            {{ formatSignedMoney(holdingStore.summary.total_pnl_cny) }}
          </div>
        </div>
        <div
          :class="['summary-item', 'summary-item-clickable', { 'summary-item-active': activeBreakdownMetric === 'dailyPnl' }]"
          role="button"
          tabindex="0"
          @click="toggleBreakdown('dailyPnl')"
          @keydown.enter="toggleBreakdown('dailyPnl')"
          @keydown.space.prevent="toggleBreakdown('dailyPnl')"
        >
          <div class="summary-label">当日盈亏</div>
          <div :class="['summary-value', pnlColorClass(holdingStore.summary.daily_pnl_cny)]">
            {{ formatSignedMoney(holdingStore.summary.daily_pnl_cny) }}
          </div>
        </div>
      </div>
    </div>

    <transition name="breakdown-card">
      <div v-if="activeBreakdownMetric" class="breakdown-card">
        <div class="breakdown-grid">
          <div
            v-for="item in activeBreakdownItems"
            :key="item.market"
            class="breakdown-item"
          >
            <div class="breakdown-label">
              <span :class="['market-badge', `market-badge-${item.market.toLowerCase()}`]">
                {{ item.label }}
              </span>
            </div>
            <div :class="['breakdown-value', metricPnlClass(item.value)]">
              {{ formatMetricMoney(item.value) }}
            </div>
          </div>
        </div>
      </div>
    </transition>

    <!-- 操作栏 -->
    <div class="action-bar">
      <template v-if="!sortMode">
        <van-button size="small" type="primary" icon="plus" @click="showInvestmentForm = true">新增投资</van-button>
        <van-button
          size="small"
          icon="replay"
          :loading="holdingStore.refreshing"
          @click="handleRefreshMarket"
        >
          刷新行情
        </van-button>
        <van-button
          size="small"
          plain
          icon="warning-o"
          :loading="holdingStore.invalidatingFundNavCache"
          @click="handleInvalidateFundNavCache"
        >
          失效基金缓存
        </van-button>
      </template>
      <template v-else>
        <div class="sort-mode-banner">排序模式</div>
        <van-button
          size="small"
          type="primary"
          :loading="savingSort"
          @click="handleSaveSort"
        >
          完成排序
        </van-button>
        <van-button size="small" plain @click="handleExitSortMode">退出排序</van-button>
      </template>
    </div>

    <div class="watch-section">
      <button type="button" class="watch-section-header" @click="watchlistExpanded = !watchlistExpanded">
        <div class="watch-section-title">
          <span>自选列表</span>
        </div>
        <van-icon :name="watchlistExpanded ? 'arrow-up' : 'arrow-down'" size="16" color="#969799" />
      </button>

      <transition name="watchlist-collapse">
        <div v-if="watchlistExpanded" class="watch-section-body">
          <van-loading v-if="watchlistStore.loading" class="page-loading" />
          <div v-else-if="watchlistStore.items.length === 0" class="empty-tip empty-tip-watch">
            暂无自选，点击「新增投资」添加
          </div>
          <Watchlist
            v-else
            :items="watchlistStore.items"
            :refreshing-codes="watchlistStore.refreshingCodes"
            @view="handleViewWatchItem"
            @refresh="handleRefreshWatchItem"
          />
        </div>
      </transition>
    </div>

    <!-- 持仓列表 -->
    <van-loading v-if="holdingStore.loading" class="page-loading" />
    <div v-else-if="holdingStore.holdings.length === 0" class="empty-tip">
      暂无持仓，点击「新增投资」添加
    </div>
    <div v-else class="holding-list">
      <HoldingList
        :holdings="displayHoldings"
        :refreshing-codes="holdingStore.refreshingCodes"
        :sort-mode="sortMode"
        @view="handleViewHolding"
        @refresh="handleRefreshSingle"
        @enter-sort-mode="handleEnterSortMode"
        @move-up="handleMoveUp"
        @move-down="handleMoveDown"
      />
    </div>

    <InvestmentForm
      v-model:show="showInvestmentForm"
      @submit="handleCreateInvestment"
    />
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { showSuccessToast, showToast } from 'vant'
import { useHoldingStore } from '@/stores/holding'
import { useWatchlistStore } from '@/stores/watchlist'
import { formatMoney, pnlColorClass } from '@/utils/format'
import HoldingList from '@/components/HoldingList.vue'
import Watchlist from '@/components/Watchlist.vue'
import InvestmentForm from '@/components/InvestmentForm.vue'

const router = useRouter()
const holdingStore = useHoldingStore()
const watchlistStore = useWatchlistStore()
const showInvestmentForm = ref(false)
const sortMode = ref(false)
const savingSort = ref(false)
const sortDraft = ref<any[]>([])
const watchlistExpanded = ref(false)
type BreakdownMetric = 'marketValue' | 'totalPnl' | 'dailyPnl'
const activeBreakdownMetric = ref<BreakdownMetric | null>(null)

const displayHoldings = computed(() => (sortMode.value ? sortDraft.value : holdingStore.holdings))
const breakdownByMarket = computed(() => {
  const initial = {
    FUND: { marketValue: 0, totalPnl: 0, dailyPnl: 0 },
    HK_STOCK: { marketValue: 0, totalPnl: 0, dailyPnl: 0 },
    A_STOCK: { marketValue: 0, totalPnl: 0, dailyPnl: 0 },
  }

  return holdingStore.holdings.reduce<Record<string, Record<BreakdownMetric, number>>>((acc, item) => {
    if (!acc[item.market]) {
      acc[item.market] = { marketValue: 0, totalPnl: 0, dailyPnl: 0 }
    }
    acc[item.market].marketValue += Number(item.market_value_cny) || 0
    if (item.ignored) {
      return acc
    }
    acc[item.market].totalPnl += Number(item.pnl_cny) || 0
    acc[item.market].dailyPnl += Number(item.growth_pnl_cny) || 0
    return acc
  }, initial)
})
const activeBreakdownItems = computed(() => {
  if (!activeBreakdownMetric.value) {
    return []
  }
  return marketBreakdownOrder.map((item) => ({
    ...item,
    value: breakdownByMarket.value[item.market]?.[activeBreakdownMetric.value!] ?? 0,
  }))
})
const marketBreakdownOrder = [
  { market: 'HK_STOCK', label: '港股' },
  { market: 'FUND', label: '基金' },
  { market: 'A_STOCK', label: 'A股' },
]

onMounted(() => {
  holdingStore.fetchHoldings()
  watchlistStore.fetchWatchlist()
})

function handleViewHolding(holding: any) {
  router.push(`/investment/${holding.id}`)
}

function handleViewWatchItem(item: any) {
  router.push(`/watchlist/${item.id}`)
}


function toggleBreakdown(metric: BreakdownMetric) {
  activeBreakdownMetric.value = activeBreakdownMetric.value === metric ? null : metric
}

function formatSignedMoney(value: number | null | undefined) {
  const amount = value ?? 0
  return `${amount > 0 ? '+' : ''}${formatMoney(amount)}`
}

function formatMetricMoney(value: number) {
  if (activeBreakdownMetric.value === 'marketValue') {
    return formatMoney(value)
  }
  return formatSignedMoney(value)
}

function metricPnlClass(value: number) {
  return activeBreakdownMetric.value === 'marketValue' ? '' : pnlColorClass(value)
}

async function handleCreateInvestment(payload: any) {
  if (payload.type === 'WATCH') {
    await watchlistStore.createWatchlistItem(payload.data)
  } else {
    await holdingStore.createHolding(payload.data)
  }
  showInvestmentForm.value = false
}

async function handleRefreshSingle(holding: any) {
  if (sortMode.value) {
    return
  }
  await holdingStore.refreshSingle(holding.code, holding.market)
}

async function handleRefreshWatchItem(item: any) {
  await watchlistStore.refreshSingle(item.code, item.market)
}

async function handleRefreshMarket() {
  await holdingStore.refreshMarket()
  await watchlistStore.fetchWatchlist()
}

async function handleInvalidateFundNavCache() {
  await holdingStore.invalidateFundNavCache()
  showSuccessToast('基金净值缓存已失效')
}

function handleEnterSortMode() {
  if (sortMode.value) {
    return
  }
  sortDraft.value = holdingStore.holdings.map((item) => ({ ...item }))
  sortMode.value = true
  showToast('已进入排序模式')
}

function handleMoveUp(holding: any) {
  moveHolding(holding.id, -1)
}

function handleMoveDown(holding: any) {
  moveHolding(holding.id, 1)
}

function moveHolding(id: number, offset: number) {
  const index = sortDraft.value.findIndex((item) => item.id === id)
  const targetIndex = index + offset
  if (index < 0 || targetIndex < 0 || targetIndex >= sortDraft.value.length) {
    return
  }
  const next = [...sortDraft.value]
  ;[next[index], next[targetIndex]] = [next[targetIndex], next[index]]
  sortDraft.value = next
}

async function handleSaveSort() {
  savingSort.value = true
  try {
    await holdingStore.reorderHoldings(
      sortDraft.value.map((item, index) => ({
        id: item.id,
        sort_order: index + 1,
      })),
    )
    sortMode.value = false
    sortDraft.value = []
    showSuccessToast('排序已保存')
  } finally {
    savingSort.value = false
  }
}

async function handleExitSortMode() {
  const changed = hasSortChanged()
  if (changed) {
    try {
      await showConfirmDialog({
        title: '退出排序',
        message: '当前排序尚未保存，确定放弃本次调整？',
      })
    } catch {
      return
    }
  }
  sortMode.value = false
  sortDraft.value = []
}

function hasSortChanged() {
  if (sortDraft.value.length !== holdingStore.holdings.length) {
    return false
  }
  return sortDraft.value.some((item, index) => item.id !== holdingStore.holdings[index]?.id)
}
</script>

<style scoped>
.investment-page {
  padding: 12px;
}

.summary-card {
  background: white;
  border-radius: 12px;
  padding: 16px;
  margin-bottom: 12px;
}

.summary-row {
  display: flex;
  justify-content: space-between;
}

.summary-item {
  flex: 1;
  text-align: center;
}

.summary-item-clickable {
  cursor: pointer;
  border-radius: 10px;
  padding: 6px 2px;
  margin: -6px 0;
  transition: background-color 0.18s ease, transform 0.18s ease;
}

.summary-item-clickable:active {
  background: #f2f6ff;
  transform: scale(0.98);
}

.summary-item-clickable:focus-visible {
  outline: 2px solid rgba(25, 137, 250, 0.35);
  outline-offset: 2px;
}

.summary-item-active {
  background: linear-gradient(135deg, #edf6ff 0%, #f7fbff 100%);
  box-shadow: inset 0 0 0 1px rgba(25, 137, 250, 0.14);
}

.summary-label {
  font-size: 13px;
  color: #999;
  margin-bottom: 4px;
}

.summary-value {
  font-size: 17px;
  font-weight: 600;
}

.breakdown-card {
  background: linear-gradient(135deg, #ffffff 0%, #f7fbff 100%);
  border: 1px solid rgba(25, 137, 250, 0.1);
  border-radius: 12px;
  box-shadow: 0 8px 24px rgba(25, 137, 250, 0.08);
  padding: 6px;
  margin: -4px 0 12px;
  overflow: hidden;
}

.breakdown-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px;
}

.breakdown-item {
  background: rgba(255, 255, 255, 0.78);
  border-radius: 10px;
  padding: 10px 6px;
  text-align: center;
}

.breakdown-label {
  display: flex;
  justify-content: center;
  margin-bottom: 6px;
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

.breakdown-value {
  color: #323233;
  font-size: 15px;
  font-weight: 700;
  word-break: break-word;
}

.breakdown-card-enter-active,
.breakdown-card-leave-active {
  transition: opacity 0.18s ease, transform 0.18s ease, max-height 0.18s ease;
}

.breakdown-card-enter-from,
.breakdown-card-leave-to {
  opacity: 0;
  max-height: 0;
  transform: translateY(-8px);
}

.breakdown-card-enter-to,
.breakdown-card-leave-from {
  opacity: 1;
  max-height: 160px;
  transform: translateY(0);
}

.action-bar {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 12px;
}

.watch-section {
  margin-bottom: 12px;
}

.watch-section-header {
  width: 100%;
  border: none;
  background: white;
  border-radius: 12px;
  padding: 14px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  font: inherit;
}

.watch-section-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 15px;
  font-weight: 600;
  color: #323233;
}

.watch-section-count {
  min-width: 20px;
  padding: 2px 8px;
  border-radius: 999px;
  background: #f2f3f5;
  color: #646566;
  font-size: 12px;
  font-weight: 600;
  text-align: center;
}

.watch-section-body {
  margin-top: 8px;
}

.sort-mode-banner {
  color: #1989fa;
  font-size: 14px;
  font-weight: 600;
  margin-right: auto;
}

.page-loading {
  display: flex;
  justify-content: center;
  padding: 40px;
}

.empty-tip {
  text-align: center;
  color: #999;
  padding: 40px 0;
  font-size: 15px;
}

.empty-tip-watch {
  padding: 28px 0;
}

.watchlist-collapse-enter-active,
.watchlist-collapse-leave-active {
  transition: all 0.2s ease;
}

.watchlist-collapse-enter-from,
.watchlist-collapse-leave-to {
  opacity: 0;
  transform: translateY(-4px);
}
</style>

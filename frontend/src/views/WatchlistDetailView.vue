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
import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { showConfirmDialog } from 'vant'
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
const data = ref<WatchlistItem | null>(null)

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

async function fetchData() {
  loading.value = true
  error.value = false
  try {
    data.value = await watchlistStore.fetchWatchlistItem(watchlistId)
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

.info-card {
  background: white;
  margin: 12px;
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

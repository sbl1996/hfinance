<template>
  <div class="investment-page">
    <!-- 持仓汇总 -->
    <div class="summary-card">
      <div class="summary-row">
        <div class="summary-item">
          <div class="summary-label">持仓市值</div>
          <div class="summary-value">{{ formatMoney(holdingStore.summary.total_market_value_cny) }}</div>
        </div>
        <div class="summary-item">
          <div class="summary-label">累计盈亏</div>
          <div :class="['summary-value', pnlColorClass(holdingStore.summary.total_pnl_cny)]">
            {{ holdingStore.summary.total_pnl_cny > 0 ? '+' : '' }}{{ formatMoney(holdingStore.summary.total_pnl_cny) }}
          </div>
        </div>
        <div class="summary-item">
          <div class="summary-label">当日盈亏</div>
          <div :class="['summary-value', pnlColorClass(holdingStore.summary.daily_pnl_cny)]">
            {{ holdingStore.summary.daily_pnl_cny > 0 ? '+' : '' }}{{ formatMoney(holdingStore.summary.daily_pnl_cny) }}
          </div>
        </div>
      </div>
    </div>

    <!-- 操作栏 -->
    <div class="action-bar">
      <template v-if="!sortMode">
        <van-button size="small" type="primary" icon="plus" @click="showForm = true">新增持仓</van-button>
        <van-button
          size="small"
          icon="replay"
          :loading="holdingStore.refreshing"
          @click="holdingStore.refreshMarket()"
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

    <!-- 持仓列表 -->
    <van-loading v-if="holdingStore.loading" class="page-loading" />
    <div v-else-if="holdingStore.holdings.length === 0" class="empty-tip">
      暂无持仓，点击「新增持仓」添加
    </div>
    <div v-else class="holding-list">
      <HoldingList
        :holdings="displayHoldings"
        :refreshing-codes="holdingStore.refreshingCodes"
        :sort-mode="sortMode"
        @edit="openEditForm"
        @refresh="handleRefreshSingle"
        @enter-sort-mode="handleEnterSortMode"
        @move-up="handleMoveUp"
        @move-down="handleMoveDown"
      />
    </div>

    <!-- 新增/编辑弹窗 -->
    <HoldingForm
      v-model:show="showForm"
      :holding="editingHolding"
      :importing-history="importingHistory"
      :updating-ignored="updatingIgnored"
      @submit="handleFormSubmit"
      @delete="handleDelete"
      @import-history="handleImportHistory"
      @toggle-ignored="handleToggleIgnored"
    />
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { showConfirmDialog, showSuccessToast, showToast } from 'vant'
import { useHoldingStore } from '@/stores/holding'
import { formatMoney, pnlColorClass } from '@/utils/format'
import HoldingList from '@/components/HoldingList.vue'
import HoldingForm from '@/components/HoldingForm.vue'

const holdingStore = useHoldingStore()
const showForm = ref(false)
const editingHolding = ref<any>(null)
const importingHistory = ref(false)
const updatingIgnored = ref(false)
const sortMode = ref(false)
const savingSort = ref(false)
const sortDraft = ref<any[]>([])

const displayHoldings = computed(() => (sortMode.value ? sortDraft.value : holdingStore.holdings))

onMounted(() => {
  holdingStore.fetchHoldings()
})

function openEditForm(holding: any) {
  editingHolding.value = { ...holding }
  showForm.value = true
}

async function handleFormSubmit(data: any) {
  if (editingHolding.value) {
    await holdingStore.updateHolding(editingHolding.value.id, data)
  } else {
    await holdingStore.createHolding(data)
  }
  showForm.value = false
  editingHolding.value = null
}

async function handleDelete(holding: any) {
  try {
    await showConfirmDialog({ title: '确认删除', message: `确定删除持仓「${holding.name}」？` })
    await holdingStore.deleteHolding(holding.id)
  } catch { /* cancelled */ }
}

async function handleRefreshSingle(holding: any) {
  if (sortMode.value) {
    return
  }
  await holdingStore.refreshSingle(holding.code, holding.market)
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

async function handleImportHistory(holding: any) {
  importingHistory.value = true
  try {
    await holdingStore.importFundHistory(holding.id)
    editingHolding.value = holdingStore.holdings.find((item) => item.id === holding.id) || editingHolding.value
  } finally {
    importingHistory.value = false
  }
}

async function handleToggleIgnored(holding: any) {
  updatingIgnored.value = true
  try {
    await holdingStore.updateHoldingIgnored(holding.id, !holding.ignored)
    editingHolding.value = holdingStore.holdings.find((item) => item.id === holding.id) || editingHolding.value
  } finally {
    updatingIgnored.value = false
  }
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

.summary-label {
  font-size: 13px;
  color: #999;
  margin-bottom: 4px;
}

.summary-value {
  font-size: 17px;
  font-weight: 600;
}

.action-bar {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 12px;
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
</style>

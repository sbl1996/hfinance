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
      <van-button size="small" type="primary" icon="plus" @click="showForm = true">新增持仓</van-button>
      <van-button
        size="small"
        icon="replay"
        :loading="holdingStore.refreshing"
        @click="holdingStore.refreshMarket()"
      >
        刷新行情
      </van-button>
    </div>

    <!-- 持仓列表 -->
    <van-loading v-if="holdingStore.loading" class="page-loading" />
    <div v-else-if="holdingStore.holdings.length === 0" class="empty-tip">
      暂无持仓，点击「新增持仓」添加
    </div>
    <div v-else class="holding-list">
      <HoldingList
        :holdings="holdingStore.holdings"
        :refreshing-codes="holdingStore.refreshingCodes"
        @edit="openEditForm"
        @refresh="handleRefreshSingle"
      />
    </div>

    <!-- 新增/编辑弹窗 -->
    <HoldingForm
      v-model:show="showForm"
      :holding="editingHolding"
      @submit="handleFormSubmit"
      @delete="handleDelete"
    />
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { showConfirmDialog } from 'vant'
import { useHoldingStore } from '@/stores/holding'
import { formatMoney, pnlColorClass } from '@/utils/format'
import HoldingList from '@/components/HoldingList.vue'
import HoldingForm from '@/components/HoldingForm.vue'

const holdingStore = useHoldingStore()
const showForm = ref(false)
const editingHolding = ref<any>(null)

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
  await holdingStore.refreshSingle(holding.code, holding.market)
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
  font-size: 12px;
  color: #999;
  margin-bottom: 4px;
}

.summary-value {
  font-size: 16px;
  font-weight: 600;
}

.action-bar {
  display: flex;
  gap: 8px;
  margin-bottom: 12px;
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
  font-size: 14px;
}
</style>

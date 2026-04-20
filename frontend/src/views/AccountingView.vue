<template>
  <div class="accounting-page">
    <!-- 现金账户 -->
    <div class="section">
      <div class="section-header">
        <h3 class="section-title">现金与理财</h3>
        <van-button size="mini" type="primary" icon="plus" @click="openCashForm()">新增</van-button>
      </div>
      <div class="section-total">合计：{{ formatMoney(cashStore.totalBalance) }}</div>
      <CashAccountList
        :accounts="cashStore.accounts"
        :loading="cashStore.loading"
        @edit="openCashForm"
        @delete="handleDeleteCash"
      />
    </div>

    <!-- 负债 -->
    <div class="section">
      <div class="section-header">
        <h3 class="section-title">负债</h3>
        <van-button size="mini" type="danger" icon="plus" @click="openLiabilityForm()">新增</van-button>
      </div>
      <div class="section-total">合计：{{ formatMoney(liabilityStore.totalAmount) }}</div>
      <LiabilityList
        :liabilities="liabilityStore.liabilities"
        :loading="liabilityStore.loading"
        @edit="openLiabilityForm"
        @delete="handleDeleteLiability"
      />
    </div>

    <!-- 现金账户编辑弹窗 -->
    <CashAccountForm
      v-model:show="showCashForm"
      :account="editingCash"
      @submit="handleCashSubmit"
    />

    <!-- 负债编辑弹窗 -->
    <LiabilityForm
      v-model:show="showLiabilityForm"
      :liability="editingLiability"
      @submit="handleLiabilitySubmit"
    />
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { showConfirmDialog } from 'vant'
import { useCashStore } from '@/stores/cash'
import { useLiabilityStore } from '@/stores/liability'
import { formatMoney } from '@/utils/format'
import CashAccountList from '@/components/CashAccountList.vue'
import CashAccountForm from '@/components/CashAccountForm.vue'
import LiabilityList from '@/components/LiabilityList.vue'
import LiabilityForm from '@/components/LiabilityForm.vue'

const cashStore = useCashStore()
const liabilityStore = useLiabilityStore()

const showCashForm = ref(false)
const editingCash = ref<any>(null)
const showLiabilityForm = ref(false)
const editingLiability = ref<any>(null)

onMounted(() => {
  cashStore.fetchAccounts()
  liabilityStore.fetchLiabilities()
})

function openCashForm(account?: any) {
  editingCash.value = account ? { ...account } : null
  showCashForm.value = true
}

function openLiabilityForm(liability?: any) {
  editingLiability.value = liability ? { ...liability } : null
  showLiabilityForm.value = true
}

async function handleCashSubmit(data: any) {
  if (editingCash.value) {
    await cashStore.updateAccount(editingCash.value.id, data)
  } else {
    await cashStore.createAccount(data)
  }
  showCashForm.value = false
  editingCash.value = null
}

async function handleLiabilitySubmit(data: any) {
  if (editingLiability.value) {
    await liabilityStore.updateLiability(editingLiability.value.id, data)
  } else {
    await liabilityStore.createLiability(data)
  }
  showLiabilityForm.value = false
  editingLiability.value = null
}

async function handleDeleteCash(account: any) {
  try {
    await showConfirmDialog({ title: '确认删除', message: `确定删除「${account.name}」？` })
    await cashStore.deleteAccount(account.id)
  } catch { /* cancelled */ }
}

async function handleDeleteLiability(liability: any) {
  try {
    await showConfirmDialog({ title: '确认删除', message: `确定删除「${liability.name}」？` })
    await liabilityStore.deleteLiability(liability.id)
  } catch { /* cancelled */ }
}
</script>

<style scoped>
.accounting-page {
  padding: 12px;
}

.section {
  margin-bottom: 24px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.section-title {
  font-size: 17px;
  font-weight: 600;
}

.section-total {
  font-size: 14px;
  color: #666;
  margin-bottom: 8px;
  padding-left: 4px;
}
</style>

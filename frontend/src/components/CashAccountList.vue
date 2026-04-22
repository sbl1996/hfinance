<template>
  <div class="account-list">
    <van-loading v-if="loading" class="list-loading" />
    <div v-else-if="accounts.length === 0" class="empty-tip">暂无现金账户</div>
    <div v-else class="list-items">
      <van-swipe-cell v-for="acc in accounts" :key="acc.id" class="swipe-item">
        <div class="account-card" @click="$emit('edit', acc)">
          <div class="card-main">
            <div class="card-info">
              <span class="account-name">{{ acc.name }}</span>
              <span :class="['account-tag', acc.type.toLowerCase()]">
                {{ acc.type === 'FUND' ? '理财' : '现金' }}
              </span>
            </div>
            <div class="account-balance">{{ formatMoney(acc.balance_cny) }}</div>
          </div>
          <van-icon name="arrow" class="card-arrow" />
        </div>
        <template #right>
          <van-button square type="danger" text="删除" class="delete-button" @click="$emit('delete', acc)" />
        </template>
      </van-swipe-cell>
    </div>
  </div>
</template>

<script setup lang="ts">
import { formatMoney } from '@/utils/format'

defineProps<{
  accounts: any[]
  loading: boolean
}>()

defineEmits<{
  edit: [account: any]
  delete: [account: any]
}>()
</script>

<style scoped>
.account-list {
  width: 100%;
}

.list-loading {
  display: flex;
  justify-content: center;
  padding: 20px;
}

.empty-tip {
  text-align: center;
  color: #999;
  padding: 20px 0;
  font-size: 14px;
}

.list-items {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.swipe-item {
  border-radius: 8px;
  overflow: hidden;
}

.account-card {
  background: white;
  padding: 12px 14px;
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  transition: background-color 0.2s;
}

.account-card:active {
  background-color: #f2f3f5;
}

.card-main {
  flex: 1;
  display: flex;
  justify-content: space-between;
  align-items: center;
  min-width: 0;
}

.card-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

.account-name {
  font-size: 15px;
  font-weight: 500;
  color: #323233;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.account-tag {
  font-size: 11px;
  padding: 0 4px;
  border-radius: 4px;
  width: fit-content;
}

.account-tag.cash {
  background: #e8f3ff;
  color: #1989fa;
}

.account-tag.fund {
  background: #edf8ee;
  color: #07c160;
}

.account-balance {
  font-size: 16px;
  font-weight: 600;
  color: #323233;
  flex-shrink: 0;
}

.card-arrow {
  color: #c8c9cc;
  font-size: 14px;
}

.delete-button {
  height: 100%;
}
</style>

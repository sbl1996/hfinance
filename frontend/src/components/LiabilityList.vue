<template>
  <div class="liability-list">
    <van-loading v-if="loading" class="list-loading" />
    <div v-else-if="liabilities.length === 0" class="empty-tip">暂无负债</div>
    <div v-else class="list-items">
      <van-swipe-cell v-for="item in liabilities" :key="item.id" class="swipe-item">
        <div class="liability-card" @click="$emit('edit', item)">
          <div class="card-main">
            <div class="card-info">
              <span class="liability-name">{{ item.name }}</span>
              <span class="liability-tag">
                {{ typeLabels[item.type] || item.type }}
              </span>
            </div>
            <div class="liability-amount">{{ formatMoney(item.amount_cny) }}</div>
          </div>
          <van-icon name="arrow" class="card-arrow" />
        </div>
        <template #right>
          <van-button square type="danger" text="删除" class="delete-button" @click="$emit('delete', item)" />
        </template>
      </van-swipe-cell>
    </div>
  </div>
</template>

<script setup lang="ts">
import { formatMoney } from '@/utils/format'

defineProps<{
  liabilities: any[]
  loading: boolean
}>()

defineEmits<{
  edit: [liability: any]
  delete: [liability: any]
}>()

const typeLabels: Record<string, string> = {
  CREDIT_CARD: '信用卡',
  MORTGAGE: '房贷',
  OTHER: '其他',
}
</script>

<style scoped>
.liability-list {
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

.liability-card {
  background: white;
  padding: 12px 14px;
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  transition: background-color 0.2s;
}

.liability-card:active {
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

.liability-name {
  font-size: 15px;
  font-weight: 500;
  color: #323233;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.liability-tag {
  font-size: 11px;
  padding: 0 4px;
  border-radius: 4px;
  width: fit-content;
  background: #fff1e8;
  color: #fa8c16;
}

.liability-amount {
  font-size: 16px;
  font-weight: 600;
  color: #ee0a24;
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

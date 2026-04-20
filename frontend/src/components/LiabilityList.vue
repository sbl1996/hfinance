<template>
  <div>
    <van-loading v-if="loading" class="list-loading" />
    <div v-else-if="liabilities.length === 0" class="empty-tip">暂无负债</div>
    <van-cell-group v-else inset>
      <van-swipe-cell v-for="item in liabilities" :key="item.id">
        <van-cell
          :title="item.name"
          :value="formatMoney(item.amount_cny)"
          :label="typeLabels[item.type] || item.type"
          is-link
          @click="$emit('edit', item)"
        />
        <template #right>
          <van-button square type="danger" text="删除" @click="$emit('delete', item)" />
        </template>
      </van-swipe-cell>
    </van-cell-group>
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
.list-loading {
  display: flex;
  justify-content: center;
  padding: 20px;
}

.empty-tip {
  text-align: center;
  color: #999;
  padding: 20px 0;
  font-size: 13px;
}
</style>

<template>
  <div>
    <van-loading v-if="loading" class="list-loading" />
    <div v-else-if="accounts.length === 0" class="empty-tip">暂无现金账户</div>
    <van-cell-group v-else inset>
      <van-swipe-cell v-for="acc in accounts" :key="acc.id">
        <van-cell
          :title="acc.name"
          :value="formatMoney(acc.balance_cny)"
          :label="acc.type === 'FUND' ? '理财' : '现金'"
          is-link
          @click="$emit('edit', acc)"
        />
        <template #right>
          <van-button square type="danger" text="删除" @click="$emit('delete', acc)" />
        </template>
      </van-swipe-cell>
    </van-cell-group>
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

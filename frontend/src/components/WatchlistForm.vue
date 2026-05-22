<template>
  <van-popup v-model:show="visible" position="bottom" round :style="{ maxHeight: '80vh' }">
    <div class="form-container">
      <h3 class="form-title">{{ item ? '编辑观察标的' : '新增观察标的' }}</h3>
      <van-field v-model="form.code" label="代码" placeholder="如 510300、00700、TSLA" required />
      <van-field v-model="form.name" label="名称" placeholder="标的名称" required />
      <van-field
        v-model="form.market"
        is-link
        readonly
        label="市场"
        placeholder="选择市场"
        @click="showMarketPicker = true"
      />
      <div class="form-actions">
        <van-button block type="primary" round @click="handleSubmit">确认</van-button>
        <van-button
          v-if="item && isFundItem"
          block
          round
          plain
          type="primary"
          class="import-btn"
          :loading="importingHistory"
          @click="handleImport"
        >
          全量导入净值
        </van-button>
        <van-button
          v-if="item"
          block
          type="danger"
          round
          plain
          class="delete-btn"
          @click="handleDelete"
        >
          删除观察标的
        </van-button>
      </div>
    </div>
    <van-popup v-model:show="showMarketPicker" position="bottom" round>
      <van-picker
        :columns="marketColumns"
        @confirm="onMarketConfirm"
        @cancel="showMarketPicker = false"
      />
    </van-popup>
  </van-popup>
</template>

<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue'
import { showConfirmDialog, showToast } from 'vant'
import type { WatchMarket, WatchlistItem } from '@/types/watchlist'

const props = defineProps<{
  show: boolean
  item: WatchlistItem | null
  importingHistory?: boolean
}>()

const emit = defineEmits<{
  'update:show': [value: boolean]
  submit: [data: { code: string; name: string; market: WatchMarket }]
  delete: [item: WatchlistItem]
  importHistory: [item: WatchlistItem]
}>()

const visible = ref(props.show)
watch(() => props.show, (v) => { visible.value = v })
watch(visible, (v) => { emit('update:show', v) })

const showMarketPicker = ref(false)
const marketColumns = [
  { text: 'A股', value: 'A_STOCK' },
  { text: '港股', value: 'HK_STOCK' },
  { text: '基金', value: 'FUND' },
  { text: '美股', value: 'US_STOCK' },
]
const marketLabels: Record<WatchMarket, string> = {
  A_STOCK: 'A股',
  HK_STOCK: '港股',
  FUND: '基金',
  US_STOCK: '美股',
}

const form = reactive({
  code: '',
  name: '',
  market: 'A股',
})

const isFundItem = computed(() => props.item?.market === 'FUND')
const importingHistory = computed(() => Boolean(props.importingHistory))

watch(() => props.item, (item) => {
  if (item) {
    form.code = item.code || ''
    form.name = item.name || ''
    form.market = marketLabels[item.market] || item.market || 'A股'
  } else {
    form.code = ''
    form.name = ''
    form.market = 'A股'
  }
}, { immediate: true })

function onMarketConfirm({ selectedValues }: any) {
  const value = selectedValues[0] as WatchMarket
  form.market = marketLabels[value] || value
  showMarketPicker.value = false
}

function handleSubmit() {
  if (!form.code.trim()) {
    showToast('请输入代码')
    return
  }
  if (!form.name.trim()) {
    showToast('请输入名称')
    return
  }
  const marketValue = Object.entries(marketLabels).find(([_, label]) => label === form.market)?.[0] || 'A_STOCK'
  emit('submit', {
    code: form.code.trim(),
    name: form.name.trim(),
    market: marketValue as WatchMarket,
  })
}

async function handleDelete() {
  if (!props.item) return
  try {
    await showConfirmDialog({ title: '确认删除', message: `确定删除观察标的「${props.item.name}」？此操作不可撤销。` })
    emit('delete', props.item)
    visible.value = false
  } catch { /* cancelled */ }
}

function handleImport() {
  if (!props.item || importingHistory.value) return
  emit('importHistory', props.item)
}
</script>

<style scoped>
.form-container {
  padding: 24px 16px;
}

.form-title {
  text-align: center;
  font-size: 16px;
  margin-bottom: 16px;
}

.form-actions {
  margin-top: 16px;
}

.form-actions > * + * {
  margin-top: 8px;
}
</style>

<template>
  <van-popup v-model:show="visible" position="bottom" round :style="{ maxHeight: '80vh' }">
    <div class="form-container">
      <h3 class="form-title">{{ item ? '编辑自选' : '新增自选' }}</h3>
      <van-field v-model="form.code" label="代码" placeholder="如 510300、00700、TSLA、H30269" required />
      <van-field v-model="form.name" label="名称" placeholder="标的名称" required />
      <van-field
        v-model="form.market"
        is-link
        readonly
        label="市场"
        placeholder="选择市场"
        @click="showMarketPicker = true"
      />
      <van-field
        v-if="form.market === '基金'"
        v-model="form.currency"
        is-link
        readonly
        label="币种"
        placeholder="选择基金币种"
        @click="showCurrencyPicker = true"
      />
      <div class="form-actions">
        <van-button block type="primary" round @click="handleSubmit">确认</van-button>
        <van-button
          v-if="item && supportsHistoryImport"
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
          删除自选
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
    <van-popup v-model:show="showCurrencyPicker" position="bottom" round>
      <van-picker
        :columns="currencyColumns"
        @confirm="onCurrencyConfirm"
        @cancel="showCurrencyPicker = false"
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
  submit: [data: { code: string; name: string; market: WatchMarket; currency: string }]
  delete: [item: WatchlistItem]
  importHistory: [item: WatchlistItem]
}>()

const visible = ref(props.show)
watch(() => props.show, (v) => { visible.value = v })
watch(visible, (v) => { emit('update:show', v) })

const showMarketPicker = ref(false)
const showCurrencyPicker = ref(false)
const marketColumns = [
  { text: 'A股', value: 'A_STOCK' },
  { text: '港股', value: 'HK_STOCK' },
  { text: '基金', value: 'FUND' },
  { text: '美股', value: 'US_STOCK' },
  { text: '指数', value: 'CN_INDEX' },
]
const marketLabels: Record<WatchMarket, string> = {
  A_STOCK: 'A股',
  HK_STOCK: '港股',
  FUND: '基金',
  US_STOCK: '美股',
  CN_INDEX: '指数',
}
const currencyColumns = [
  { text: '人民币', value: 'CNY' },
  { text: '港币', value: 'HKD' },
  { text: '美元', value: 'USD' },
]
const currencyLabels: Record<string, string> = {
  CNY: '人民币',
  HKD: '港币',
  USD: '美元',
}

const form = reactive({
  code: '',
  name: '',
  market: 'A股',
  currency: '人民币',
})

const supportsHistoryImport = computed(() => (
  props.item?.market === 'FUND'
  || props.item?.market === 'US_STOCK'
  || props.item?.market === 'CN_INDEX'
))
const importingHistory = computed(() => Boolean(props.importingHistory))

watch(() => props.item, (item) => {
  if (item) {
    form.code = item.code || ''
    form.name = item.name || ''
    form.market = marketLabels[item.market] || item.market || 'A股'
    form.currency = currencyLabels[item.currency] || item.currency || '人民币'
  } else {
    form.code = ''
    form.name = ''
    form.market = 'A股'
    form.currency = '人民币'
  }
}, { immediate: true })

watch(() => form.market, (market) => {
  if (market !== '基金') {
    form.currency = '人民币'
  }
})

function onMarketConfirm({ selectedValues }: any) {
  const value = selectedValues[0] as WatchMarket
  form.market = marketLabels[value] || value
  showMarketPicker.value = false
}

function onCurrencyConfirm({ selectedValues }: any) {
  const value = selectedValues[0] as string
  form.currency = currencyLabels[value] || value
  showCurrencyPicker.value = false
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
    currency: marketValue === 'FUND' ? (Object.entries(currencyLabels).find(([_, label]) => label === form.currency)?.[0] || 'CNY') : 'CNY',
  })
}

async function handleDelete() {
  if (!props.item) return
  try {
    await showConfirmDialog({ title: '确认删除', message: `确定删除自选「${props.item.name}」？此操作不可撤销。` })
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

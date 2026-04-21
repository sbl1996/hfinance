<template>
  <van-popup v-model:show="visible" position="bottom" round :style="{ maxHeight: '80vh' }">
    <div class="form-container">
      <h3 class="form-title">{{ holding ? '编辑持仓' : '新增持仓' }}</h3>
      <van-field v-model="form.code" label="代码" placeholder="如 510300、00700" required />
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
        v-model="form.quantity"
        label="数量"
        type="number"
        placeholder="持有数量"
        inputmode="decimal"
        required
      />
      <van-field
        v-model="form.cost_total_cny"
        label="成本总额(CNY)"
        type="number"
        placeholder="人民币总额"
        inputmode="decimal"
        required
      />
      <div class="form-actions">
        <van-button block type="primary" round @click="handleSubmit">确认</van-button>
        <van-button
          v-if="holding && isFundHolding"
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
        <van-button v-if="holding" block type="danger" round plain class="delete-btn" @click="handleDelete">删除持仓</van-button>
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
import { computed, ref, reactive, watch } from 'vue'
import { showConfirmDialog } from 'vant'

const props = defineProps<{
  show: boolean
  holding: any
  importingHistory?: boolean
}>()

const emit = defineEmits<{
  'update:show': [value: boolean]
  submit: [data: any]
  delete: [holding: any]
  importHistory: [holding: any]
}>()

const visible = ref(props.show)
watch(() => props.show, (v) => { visible.value = v })
watch(visible, (v) => { emit('update:show', v) })

const showMarketPicker = ref(false)
const marketColumns = [
  { text: 'A股', value: 'A_STOCK' },
  { text: '港股', value: 'HK_STOCK' },
  { text: '基金', value: 'FUND' },
]

const marketLabels: Record<string, string> = { A_STOCK: 'A股', HK_STOCK: '港股', FUND: '基金' }
const isFundHolding = computed(() => {
  if (!props.holding) return false
  return props.holding.market === 'FUND'
})
const importingHistory = computed(() => Boolean(props.importingHistory))

const form = reactive({
  code: '',
  name: '',
  market: 'A股',
  quantity: '',
  cost_total_cny: '',
})

// 编辑时回填
watch(() => props.holding, (h) => {
  if (h) {
    form.code = h.code || ''
    form.name = h.name || ''
    form.market = marketLabels[h.market] || h.market || 'A股'
    form.quantity = String(h.quantity ?? '')
    form.cost_total_cny = String(h.cost_total_cny ?? '')
  } else {
    form.code = ''
    form.name = ''
    form.market = 'A股'
    form.quantity = ''
    form.cost_total_cny = ''
  }
}, { immediate: true })

function onMarketConfirm({ selectedValues }: any) {
  const val = selectedValues[0]
  form.market = marketLabels[val] || val
  showMarketPicker.value = false
}

function handleSubmit() {
  const marketValue = Object.entries(marketLabels).find(([_, label]) => label === form.market)?.[0] || 'A_STOCK'
  emit('submit', {
    code: form.code,
    name: form.name,
    market: marketValue,
    quantity: parseFloat(form.quantity) || 0,
    cost_total_cny: parseFloat(form.cost_total_cny) || 0,
  })
}

async function handleDelete() {
  if (!props.holding) return
  try {
    await showConfirmDialog({ title: '确认删除', message: `确定删除持仓「${props.holding.name}」？此操作不可撤销。` })
    emit('delete', props.holding)
    visible.value = false
  } catch { /* cancelled */ }
}

async function handleImport() {
  if (!props.holding || importingHistory.value) return
  emit('importHistory', props.holding)
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

.delete-btn {
  margin-top: 8px;
}
</style>

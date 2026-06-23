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
        v-if="form.market === '基金'"
        v-model="form.currency"
        is-link
        readonly
        label="币种"
        placeholder="选择基金币种"
        @click="showCurrencyPicker = true"
      />
      <van-field
        v-model="form.quantity"
        label="数量"
        type="number"
        placeholder="持有数量"
        inputmode="decimal"
        required
        @focus="activePriceField = 'quantity'"
      />
      <van-field
        v-model="form.unit_price"
        label="单价(CNY)"
        type="number"
        placeholder="按成本总额自动换算"
        inputmode="decimal"
        @focus="activePriceField = 'unit_price'"
      />
      <van-field
        v-model="form.cost_total_cny"
        label="成本总额(CNY)"
        type="number"
        placeholder="人民币总额"
        inputmode="decimal"
        required
        @focus="activePriceField = 'cost_total_cny'"
      />
      <div class="form-actions">
        <van-button block type="primary" round @click="handleSubmit">确认</van-button>
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
import { ref, reactive, watch } from 'vue'
import { showToast } from 'vant'

const props = defineProps<{
  show: boolean
  holding: any
}>()

const emit = defineEmits<{
  'update:show': [value: boolean]
  submit: [data: any]
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
]

const marketLabels: Record<string, string> = { A_STOCK: 'A股', HK_STOCK: '港股', FUND: '基金' }
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
  quantity: '',
  unit_price: '',
  cost_total_cny: '',
})
const activePriceField = ref<'quantity' | 'unit_price' | 'cost_total_cny' | null>(null)
const syncingPriceFields = ref(false)

function parsePositiveNumber(value: string) {
  const parsed = parseFloat(value)
  return Number.isFinite(parsed) && parsed > 0 ? parsed : null
}

function formatInputNumber(value: number) {
  return Number(value.toFixed(6)).toString()
}

function syncUnitPriceFromQuantity() {
  const costTotal = parsePositiveNumber(form.cost_total_cny)
  const quantity = parsePositiveNumber(form.quantity)
  if (!costTotal || !quantity) {
    form.unit_price = ''
    return
  }
  form.unit_price = formatInputNumber(costTotal / quantity)
}

function syncQuantityFromUnitPrice() {
  const costTotal = parsePositiveNumber(form.cost_total_cny)
  const unitPrice = parsePositiveNumber(form.unit_price)
  if (!costTotal || !unitPrice) {
    form.quantity = ''
    return
  }
  form.quantity = formatInputNumber(costTotal / unitPrice)
}

// 编辑时回填
watch(() => props.holding, (h) => {
  if (h) {
    form.code = h.code || ''
    form.name = h.name || ''
    form.market = marketLabels[h.market] || h.market || 'A股'
    form.currency = currencyLabels[h.currency] || h.currency || '人民币'
    form.quantity = String(h.quantity ?? '')
    form.cost_total_cny = String(h.cost_total_cny ?? '')
    syncUnitPriceFromQuantity()
  } else {
    form.code = ''
    form.name = ''
    form.market = 'A股'
    form.currency = '人民币'
    form.quantity = ''
    form.unit_price = ''
    form.cost_total_cny = ''
  }
}, { immediate: true })

watch(() => form.market, (market) => {
  if (market !== '基金') {
    form.currency = '人民币'
  }
})

watch(() => form.quantity, () => {
  if (syncingPriceFields.value || activePriceField.value !== 'quantity') return
  const costTotal = parsePositiveNumber(form.cost_total_cny)
  if (!costTotal) return
  syncingPriceFields.value = true
  syncUnitPriceFromQuantity()
  syncingPriceFields.value = false
})

watch(() => form.unit_price, () => {
  if (syncingPriceFields.value || activePriceField.value !== 'unit_price') return
  const costTotal = parsePositiveNumber(form.cost_total_cny)
  if (!costTotal) return
  syncingPriceFields.value = true
  syncQuantityFromUnitPrice()
  syncingPriceFields.value = false
})

watch(() => form.cost_total_cny, () => {
  if (syncingPriceFields.value) return
  const costTotal = parsePositiveNumber(form.cost_total_cny)
  if (!costTotal) return

  syncingPriceFields.value = true
  if (activePriceField.value === 'unit_price') {
    syncQuantityFromUnitPrice()
  } else {
    syncUnitPriceFromQuantity()
  }
  syncingPriceFields.value = false
})

function onMarketConfirm({ selectedValues }: any) {
  const val = selectedValues[0]
  form.market = marketLabels[val] || val
  showMarketPicker.value = false
}

function onCurrencyConfirm({ selectedValues }: any) {
  const val = selectedValues[0]
  form.currency = currencyLabels[val] || val
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
  if (!parsePositiveNumber(form.quantity)) {
    showToast('请输入正确的持有数量')
    return
  }
  if (!parsePositiveNumber(form.cost_total_cny)) {
    showToast('请输入正确的成本总额')
    return
  }
  const marketValue = Object.entries(marketLabels).find(([_, label]) => label === form.market)?.[0] || 'A_STOCK'
  const currencyValue = Object.entries(currencyLabels).find(([_, label]) => label === form.currency)?.[0] || 'CNY'
  emit('submit', {
    code: form.code.trim(),
    name: form.name.trim(),
    market: marketValue,
    currency: marketValue === 'FUND' ? currencyValue : 'CNY',
    quantity: parseFloat(form.quantity),
    cost_total_cny: parseFloat(form.cost_total_cny),
  })
  visible.value = false
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

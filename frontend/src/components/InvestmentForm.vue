<template>
  <van-popup v-model:show="visible" position="bottom" round :style="{ maxHeight: '80vh' }">
    <div class="form-container">
      <h3 class="form-title">新增投资</h3>

      <div class="type-switch">
        <button
          type="button"
          :class="['type-chip', { 'type-chip-active': investmentType === 'HOLDING' }]"
          @click="investmentType = 'HOLDING'"
        >
          持仓
        </button>
        <button
          type="button"
          :class="['type-chip', { 'type-chip-active': investmentType === 'WATCH' }]"
          @click="investmentType = 'WATCH'"
        >
          自选
        </button>
      </div>

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

      <template v-if="investmentType === 'HOLDING'">
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
      </template>

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
import { computed, reactive, ref, watch } from 'vue'
import { showToast } from 'vant'
import type { WatchMarket } from '@/types/watchlist'

type InvestmentType = 'HOLDING' | 'WATCH'

const props = defineProps<{
  show: boolean
}>()

const emit = defineEmits<{
  'update:show': [value: boolean]
  submit: [payload: { type: InvestmentType; data: Record<string, unknown> }]
}>()

const visible = ref(props.show)
watch(() => props.show, (value) => {
  visible.value = value
  if (value) {
    resetForm()
  }
})
watch(visible, (value) => emit('update:show', value))

const investmentType = ref<InvestmentType>('HOLDING')
const showMarketPicker = ref(false)
const showCurrencyPicker = ref(false)
const allMarketColumns = [
  { text: 'A股', value: 'A_STOCK' },
  { text: '港股', value: 'HK_STOCK' },
  { text: '基金', value: 'FUND' },
  { text: '美股', value: 'US_STOCK' },
  { text: '指数', value: 'CN_INDEX' },
]
const holdingMarketValues = new Set(['A_STOCK', 'HK_STOCK', 'FUND'])
const marketColumns = computed(() => (
  investmentType.value === 'HOLDING'
    ? allMarketColumns.filter((item) => holdingMarketValues.has(item.value))
    : allMarketColumns
))
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
  quantity: '',
  unit_price: '',
  cost_total_cny: '',
})
const activePriceField = ref<'quantity' | 'unit_price' | 'cost_total_cny' | null>(null)
const syncingPriceFields = ref(false)

watch(investmentType, (type) => {
  if (type === 'HOLDING' && ['美股', '指数'].includes(form.market)) {
    form.market = 'A股'
  }
})

watch(() => form.market, (market) => {
  if (market !== '基金') {
    form.currency = '人民币'
  }
})

watch(() => form.quantity, () => {
  if (investmentType.value !== 'HOLDING' || syncingPriceFields.value || activePriceField.value !== 'quantity') return
  const costTotal = parsePositiveNumber(form.cost_total_cny)
  if (!costTotal) return
  syncingPriceFields.value = true
  syncUnitPriceFromQuantity()
  syncingPriceFields.value = false
})

watch(() => form.unit_price, () => {
  if (investmentType.value !== 'HOLDING' || syncingPriceFields.value || activePriceField.value !== 'unit_price') return
  const costTotal = parsePositiveNumber(form.cost_total_cny)
  if (!costTotal) return
  syncingPriceFields.value = true
  syncQuantityFromUnitPrice()
  syncingPriceFields.value = false
})

watch(() => form.cost_total_cny, () => {
  if (investmentType.value !== 'HOLDING' || syncingPriceFields.value) return
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

function resetForm() {
  investmentType.value = 'HOLDING'
  form.code = ''
  form.name = ''
  form.market = 'A股'
  form.currency = '人民币'
  form.quantity = ''
  form.unit_price = ''
  form.cost_total_cny = ''
  activePriceField.value = null
}

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

function onMarketConfirm({ selectedValues }: any) {
  const value = selectedValues[0] as WatchMarket
  if (investmentType.value === 'HOLDING' && ['US_STOCK', 'CN_INDEX'].includes(value)) {
    showToast('持仓暂不支持该类型，请使用自选')
    showMarketPicker.value = false
    return
  }
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
  const currencyValue = Object.entries(currencyLabels).find(([_, label]) => label === form.currency)?.[0] || 'CNY'

  if (investmentType.value === 'WATCH') {
    emit('submit', {
      type: 'WATCH',
      data: {
        code: form.code.trim(),
        name: form.name.trim(),
        market: marketValue,
        currency: marketValue === 'FUND' ? currencyValue : 'CNY',
      },
    })
    return
  }

  emit('submit', {
    type: 'HOLDING',
    data: {
      code: form.code.trim(),
      name: form.name.trim(),
      market: marketValue,
      currency: marketValue === 'FUND' ? currencyValue : 'CNY',
      quantity: parseFloat(form.quantity) || 0,
      cost_total_cny: parseFloat(form.cost_total_cny) || 0,
    },
  })
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

.type-switch {
  display: flex;
  gap: 8px;
  margin-bottom: 16px;
}

.type-chip {
  flex: 1;
  border: none;
  background: #f2f3f5;
  color: #646566;
  padding: 10px 0;
  border-radius: 999px;
  font-size: 14px;
  font-weight: 600;
}

.type-chip-active {
  background: #1989fa;
  color: #fff;
}

.form-actions {
  margin-top: 16px;
}
</style>

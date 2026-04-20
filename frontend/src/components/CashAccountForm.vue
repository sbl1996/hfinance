<template>
  <van-popup v-model:show="visible" position="bottom" round :style="{ maxHeight: '70vh' }">
    <div class="form-container">
      <h3 class="form-title">{{ account ? '编辑' : '新增' }}现金账户</h3>
      <van-field v-model="form.name" label="名称" placeholder="如：招行卡、微信零钱" required />
      <van-field
        v-model="form.balance_cny"
        label="余额(CNY)"
        type="number"
        placeholder="0.00"
        inputmode="decimal"
        required
      />
      <van-field
        v-model="form.type_label"
        is-link
        readonly
        label="类型"
        @click="showTypePicker = true"
      />
      <div class="form-actions">
        <van-button block type="primary" round @click="handleSubmit">确认</van-button>
      </div>
    </div>
    <van-popup v-model:show="showTypePicker" position="bottom" round>
      <van-picker :columns="typeColumns" @confirm="onTypeConfirm" @cancel="showTypePicker = false" />
    </van-popup>
  </van-popup>
</template>

<script setup lang="ts">
import { ref, reactive, watch } from 'vue'

const props = defineProps<{
  show: boolean
  account: any
}>()

const emit = defineEmits<{
  'update:show': [value: boolean]
  submit: [data: any]
}>()

const visible = ref(props.show)
watch(() => props.show, (v) => { visible.value = v })
watch(visible, (v) => { emit('update:show', v) })

const showTypePicker = ref(false)
const typeColumns = [
  { text: '现金', value: 'CASH' },
  { text: '理财', value: 'FUND' },
]
const typeLabels: Record<string, string> = { CASH: '现金', FUND: '理财' }

const form = reactive({
  name: '',
  balance_cny: '',
  type_label: '现金',
})

watch(() => props.account, (a) => {
  if (a) {
    form.name = a.name || ''
    form.balance_cny = String(a.balance_cny ?? '')
    form.type_label = typeLabels[a.type] || '现金'
  } else {
    form.name = ''
    form.balance_cny = ''
    form.type_label = '现金'
  }
}, { immediate: true })

function onTypeConfirm({ selectedValues }: any) {
  const val = selectedValues[0]
  form.type_label = typeLabels[val] || val
  showTypePicker.value = false
}

function handleSubmit() {
  const typeValue = Object.entries(typeLabels).find(([_, label]) => label === form.type_label)?.[0] || 'CASH'
  emit('submit', {
    name: form.name,
    balance_cny: parseFloat(form.balance_cny) || 0,
    type: typeValue,
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

.form-actions {
  margin-top: 16px;
}
</style>

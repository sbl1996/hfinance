<template>
  <van-popup v-model:show="visible" position="bottom" round :style="{ maxHeight: '70vh' }">
    <div class="form-container">
      <h3 class="form-title">{{ liability ? '编辑' : '新增' }}负债</h3>
      <van-field v-model="form.name" label="名称" placeholder="如：招行信用卡、房贷" required />
      <van-field
        v-model="form.amount_cny"
        label="金额(CNY)"
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
  liability: any
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
  { text: '信用卡', value: 'CREDIT_CARD' },
  { text: '房贷', value: 'MORTGAGE' },
  { text: '其他', value: 'OTHER' },
]
const typeLabels: Record<string, string> = { CREDIT_CARD: '信用卡', MORTGAGE: '房贷', OTHER: '其他' }

const form = reactive({
  name: '',
  amount_cny: '',
  type_label: '其他',
})

watch(() => props.liability, (l) => {
  if (l) {
    form.name = l.name || ''
    form.amount_cny = String(l.amount_cny ?? '')
    form.type_label = typeLabels[l.type] || '其他'
  } else {
    form.name = ''
    form.amount_cny = ''
    form.type_label = '其他'
  }
}, { immediate: true })

function onTypeConfirm({ selectedValues }: any) {
  const val = selectedValues[0]
  form.type_label = typeLabels[val] || val
  showTypePicker.value = false
}

function handleSubmit() {
  const typeValue = Object.entries(typeLabels).find(([_, label]) => label === form.type_label)?.[0] || 'OTHER'
  emit('submit', {
    name: form.name,
    amount_cny: parseFloat(form.amount_cny) || 0,
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

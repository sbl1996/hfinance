<template>
  <van-popup :show="show" position="bottom" round @update:show="emit('update:show', $event)">
    <div class="task-form">
      <div class="task-form-title">{{ task ? '编辑任务' : '新建任务' }}</div>

      <div class="task-form-section">
        <label class="task-form-label">拉取标的</label>
        <select v-model="selectedCode" class="task-form-select" @change="handleHoldingChange">
          <option disabled value="">请选择标的</option>
          <option v-for="holding in holdings" :key="holding.id" :value="holding.code">
            {{ holding.name }} ({{ holding.code }})
          </option>
        </select>
      </div>

      <div class="task-form-section">
        <label class="task-form-label">拉取时间</label>
        <input v-model="runTime" class="task-form-time" type="time" />
      </div>

      <div class="task-form-section">
        <label class="task-form-label">重复频率</label>
        <div class="weekday-grid">
          <button
            v-for="day in weekdayOptions"
            :key="day.value"
            type="button"
            :class="['weekday-chip', { 'weekday-chip-active': weekdays.includes(day.value) }]"
            @click="toggleWeekday(day.value)"
          >
            {{ day.label }}
          </button>
        </div>
      </div>

      <div class="task-form-section task-form-switch">
        <span class="task-form-label">启用任务</span>
        <van-switch v-model="enabled" size="22px" />
      </div>

      <div class="task-form-actions">
        <van-button block plain @click="emit('update:show', false)">取消</van-button>
        <van-button block type="primary" @click="handleSubmit">保存</van-button>
      </div>
    </div>
  </van-popup>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { showToast } from 'vant'
import type { FetchTask, FetchTaskCreatePayload } from '@/types/fetchTask'

const props = defineProps<{
  show: boolean
  task?: FetchTask | null
  holdings: Array<{ id: number; code: string; name: string; market: 'A_STOCK' | 'HK_STOCK' | 'FUND' }>
}>()

const emit = defineEmits<{
  (e: 'update:show', value: boolean): void
  (e: 'submit', payload: FetchTaskCreatePayload): void
}>()

const selectedCode = ref('')
const selectedName = ref('')
const selectedMarket = ref<'A_STOCK' | 'HK_STOCK' | 'FUND'>('A_STOCK')
const runTime = ref('19:30')
const weekdays = ref<number[]>([0, 1, 2, 3, 4])
const enabled = ref(true)

const weekdayOptions = [
  { value: 0, label: '一' },
  { value: 1, label: '二' },
  { value: 2, label: '三' },
  { value: 3, label: '四' },
  { value: 4, label: '五' },
  { value: 5, label: '六' },
  { value: 6, label: '日' },
]

const holdingMap = computed(() => {
  return new Map(props.holdings.map((holding) => [holding.code, holding]))
})

watch(
  () => [props.show, props.task, props.holdings],
  () => {
    if (props.task) {
      selectedCode.value = props.task.code
      selectedName.value = props.task.name
      selectedMarket.value = props.task.market
      runTime.value = props.task.run_time
      weekdays.value = [...props.task.weekdays]
      enabled.value = props.task.enabled
      return
    }

    const firstHolding = props.holdings[0]
    selectedCode.value = firstHolding?.code ?? ''
    selectedName.value = firstHolding?.name ?? ''
    selectedMarket.value = firstHolding?.market ?? 'A_STOCK'
    runTime.value = '19:30'
    weekdays.value = [0, 1, 2, 3, 4]
    enabled.value = true
  },
  { immediate: true, deep: true },
)

function handleHoldingChange() {
  const holding = holdingMap.value.get(selectedCode.value)
  if (!holding) {
    return
  }
  selectedName.value = holding.name
  selectedMarket.value = holding.market
}

function toggleWeekday(day: number) {
  if (weekdays.value.includes(day)) {
    weekdays.value = weekdays.value.filter((item) => item !== day)
    return
  }
  weekdays.value = [...weekdays.value, day].sort((a, b) => a - b)
}

function handleSubmit() {
  if (!selectedCode.value) {
    showToast('请选择标的')
    return
  }
  if (!runTime.value) {
    showToast('请选择拉取时间')
    return
  }
  if (weekdays.value.length === 0) {
    showToast('请至少选择一天')
    return
  }

  emit('submit', {
    code: selectedCode.value,
    name: selectedName.value,
    market: selectedMarket.value,
    enabled: enabled.value,
    run_time: runTime.value,
    weekdays: [...weekdays.value],
  })
}
</script>

<style scoped>
.task-form {
  padding: 20px 16px calc(20px + env(safe-area-inset-bottom));
}

.task-form-title {
  font-size: 18px;
  font-weight: 700;
  margin-bottom: 16px;
}

.task-form-section {
  margin-bottom: 16px;
}

.task-form-label {
  display: block;
  font-size: 13px;
  color: #666;
  margin-bottom: 8px;
}

.task-form-select,
.task-form-time {
  width: 100%;
  border: 1px solid #dcdee0;
  border-radius: 10px;
  padding: 10px 12px;
  background: #fff;
  font-size: 15px;
}

.weekday-grid {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 8px;
}

.weekday-chip {
  border: 1px solid #dcdfe6;
  border-radius: 10px;
  background: #fff;
  padding: 8px 0;
  font-size: 14px;
}

.weekday-chip-active {
  color: #1989fa;
  border-color: #1989fa;
  background: rgba(25, 137, 250, 0.08);
}

.task-form-switch {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.task-form-switch .task-form-label {
  margin-bottom: 0;
}

.task-form-actions {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
  margin-top: 20px;
}
</style>

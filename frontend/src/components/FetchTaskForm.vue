<template>
  <van-popup :show="show" position="bottom" round @update:show="emit('update:show', $event)">
    <div class="task-form">
      <div class="task-form-title">{{ task ? '编辑任务' : '新建任务' }}</div>

      <div class="form-content">
        <!-- Vant Field form list -->
        <van-cell-group :border="false" class="form-group">
          <!-- 拉取标的 Picker -->
          <van-field
            v-model="selectedHoldingLabel"
            is-link
            readonly
            label="拉取标的"
            placeholder="请选择拉取标的"
            label-class="form-label-text"
            input-align="right"
            @click="showPicker = true"
          />

          <!-- 拉取时间 Picker -->
          <van-field
            v-model="runTime"
            is-link
            readonly
            label="拉取时间"
            placeholder="请选择拉取时间"
            label-class="form-label-text"
            input-align="right"
            @click="showTimePicker = true"
          />
        </van-cell-group>

        <!-- 重复频率 -->
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

        <!-- 启用任务 -->
        <div class="task-form-section task-form-switch">
          <span class="task-form-label-switch">启用任务</span>
          <van-switch v-model="enabled" size="22px" />
        </div>
      </div>

      <div class="task-form-actions">
        <van-button block plain round @click="emit('update:show', false)">取消</van-button>
        <van-button block type="primary" round @click="handleSubmit">保存</van-button>
      </div>
    </div>

    <!-- 标的选择弹窗 -->
    <van-popup :show="showPicker" position="bottom" round @update:show="showPicker = $event">
      <van-picker
        :columns="pickerColumns"
        title="选择标的"
        @confirm="onPickerConfirm"
        @cancel="showPicker = false"
      />
    </van-popup>

    <!-- 时间选择弹窗 -->
    <van-popup :show="showTimePicker" position="bottom" round @update:show="showTimePicker = $event">
      <van-time-picker
        v-model="timeValue"
        title="选择时间"
        @confirm="onTimeConfirm"
        @cancel="showTimePicker = false"
      />
    </van-popup>
  </van-popup>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { showToast } from 'vant'
import type { FetchTask, FetchTaskCreatePayload, FetchTaskMarket } from '@/types/fetchTask'

const props = defineProps<{
  show: boolean
  task?: FetchTask | null
  targets: Array<{
    code: string
    name: string
    market: FetchTaskMarket
    sourceLabels: string[]
  }>
}>()

const emit = defineEmits<{
  (e: 'update:show', value: boolean): void
  (e: 'submit', payload: FetchTaskCreatePayload): void
}>()

const selectedCode = ref('')
const selectedName = ref('')
const selectedMarket = ref<FetchTaskMarket>('A_STOCK')
const runTime = ref('19:30')
const weekdays = ref<number[]>([0, 1, 2, 3, 4])
const enabled = ref(true)

const showPicker = ref(false)
const showTimePicker = ref(false)
const timeValue = ref<string[]>(['19', '30'])

const weekdayOptions = [
  { value: 0, label: '一' },
  { value: 1, label: '二' },
  { value: 2, label: '三' },
  { value: 3, label: '四' },
  { value: 4, label: '五' },
  { value: 5, label: '六' },
  { value: 6, label: '日' },
]

type FetchTaskTargetOption = {
  code: string
  name: string
  market: FetchTaskMarket
  sourceLabels: string[]
}

function buildTargetKey(code: string, market: FetchTaskMarket) {
  return `${market}::${code}`
}

const targetMap = computed(() => {
  return new Map(props.targets.map((target) => [buildTargetKey(target.code, target.market), target]))
})

const selectedHoldingLabel = computed(() => {
  const selected = targetMap.value.get(buildTargetKey(selectedCode.value, selectedMarket.value))
  if (selected) {
    return formatTargetLabel(selected)
  }
  if (!selectedCode.value) {
    return ''
  }
  return `${selectedName.value} (${selectedCode.value})`
})

const pickerColumns = computed(() => {
  return props.targets.map((target) => ({
    text: formatTargetLabel(target),
    value: buildTargetKey(target.code, target.market),
  }))
})

watch(
  () => [props.show, props.task, props.targets],
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

    const firstTarget = props.targets[0]
    selectedCode.value = firstTarget?.code ?? ''
    selectedName.value = firstTarget?.name ?? ''
    selectedMarket.value = firstTarget?.market ?? 'A_STOCK'
    runTime.value = '19:30'
    weekdays.value = [0, 1, 2, 3, 4]
    enabled.value = true
  },
  { immediate: true, deep: true },
)

watch(runTime, (val) => {
  if (val) {
    timeValue.value = val.split(':').slice(0, 2)
  }
}, { immediate: true })

function formatTargetLabel(target: FetchTaskTargetOption) {
  const sourceLabel = target.sourceLabels.join('/')
  return `${target.name} (${target.code}) · ${marketLabel(target.market)} · ${sourceLabel}`
}

function marketLabel(market: FetchTaskMarket) {
  if (market === 'HK_STOCK') return '港股'
  if (market === 'FUND') return '基金'
  if (market === 'US_STOCK') return '美股'
  if (market === 'CN_INDEX') return '指数'
  return 'A股'
}

function handleTargetChange(targetKey: string) {
  const target = targetMap.value.get(targetKey)
  if (!target) {
    return
  }
  selectedCode.value = target.code
  selectedName.value = target.name
  selectedMarket.value = target.market
}

function onPickerConfirm({ selectedOptions }: any) {
  const option = selectedOptions[0]
  if (option) {
    handleTargetChange(option.value)
  }
  showPicker.value = false
}

function onTimeConfirm({ selectedValues }: any) {
  runTime.value = selectedValues.join(':')
  showTimePicker.value = false
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
  background: #fff;
}

.task-form-title {
  font-size: 18px;
  font-weight: 700;
  margin-bottom: 16px;
  text-align: center;
  color: #323233;
}

.form-content {
  display: flex;
  flex-direction: column;
  gap: 16px;
  margin-bottom: 24px;
}

.form-group {
  border-radius: 12px;
  overflow: hidden;
  border: 1px solid #f2f3f5;
}

.form-label-text {
  font-weight: 500;
  color: #646566;
}

.task-form-section {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.task-form-label {
  font-size: 13px;
  color: #646566;
  font-weight: 500;
  padding-left: 4px;
}

.weekday-grid {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 8px;
}

.weekday-chip {
  border: 1px solid #ebedf0;
  border-radius: 8px;
  background: #f7f8fa;
  padding: 8px 0;
  font-size: 13px;
  font-weight: 500;
  color: #646566;
  transition: all 0.2s cubic-bezier(0.18, 0.89, 0.32, 1.28);
  cursor: pointer;
}

.weekday-chip:active {
  transform: scale(0.92);
}

.weekday-chip-active {
  color: #1989fa;
  border-color: #1989fa;
  background: rgba(25, 137, 250, 0.06);
  font-weight: 600;
  box-shadow: 0 2px 6px rgba(25, 137, 250, 0.1);
}

.task-form-switch {
  flex-direction: row;
  align-items: center;
  justify-content: space-between;
  padding: 4px 4px;
}

.task-form-label-switch {
  font-size: 14px;
  color: #646566;
  font-weight: 500;
}

.task-form-actions {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
  margin-top: 20px;
}
</style>

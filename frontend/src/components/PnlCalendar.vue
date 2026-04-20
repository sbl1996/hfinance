<template>
  <div class="pnl-calendar-card">
    <div class="calendar-header">
      <van-icon name="arrow-left" class="calendar-nav" @click="prevMonth" />
      <span class="calendar-title">{{ currentYear }}年{{ currentMonth }}月</span>
      <van-icon name="arrow" class="calendar-nav" @click="nextMonth" />
    </div>
    <div class="calendar-weekdays">
      <span v-for="d in weekdays" :key="d" class="weekday">{{ d }}</span>
    </div>
    <div class="calendar-grid">
      <!-- 月初空白 -->
      <div v-for="n in firstDayOffset" :key="'e' + n" class="calendar-cell empty"></div>
      <!-- 日期格子 -->
      <div
        v-for="day in daysInMonth"
        :key="day"
        class="calendar-cell"
        :class="{ today: isToday(day) }"
        @click="handleClickDay(day)"
      >
        <div class="cell-day">{{ day }}</div>
        <div
          v-if="getDayPnl(day) !== null"
          :class="['cell-pnl', getDayPnl(day)! > 0 ? 'pnl-positive' : getDayPnl(day)! < 0 ? 'pnl-negative' : '']"
        >
          {{ formatPnl(getDayPnl(day)!) }}
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'

const props = defineProps<{
  calendarData: any
}>()

const emit = defineEmits<{
  'change-month': [year: number, month: number]
  'click-day': [date: string]
}>()

const weekdays = ['一', '二', '三', '四', '五', '六', '日']
const currentYear = ref(new Date().getFullYear())
const currentMonth = ref(new Date().getMonth() + 1)

const daysInMonth = computed(() => {
  return new Date(currentYear.value, currentMonth.value, 0).getDate()
})

const firstDayOffset = computed(() => {
  const d = new Date(currentYear.value, currentMonth.value - 1, 1).getDay()
  return d === 0 ? 6 : d - 1  // 周一为起始
})

function isToday(day: number): boolean {
  const now = new Date()
  return currentYear.value === now.getFullYear() && currentMonth.value === now.getMonth() + 1 && day === now.getDate()
}

function getDayPnl(day: number): number | null {
  if (!props.calendarData?.days) return null
  const dateStr = `${currentYear.value}-${String(currentMonth.value).padStart(2, '0')}-${String(day).padStart(2, '0')}`
  const found = props.calendarData.days.find((d: any) => d.date === dateStr)
  return found ? found.daily_pnl_cny : null
}

function formatPnl(val: number): string {
  if (val === 0) return '0'
  const abs = Math.abs(val)
  if (abs >= 10000) return `${val > 0 ? '+' : '-'}${(abs / 10000).toFixed(1)}万`
  if (abs >= 1000) return `${val > 0 ? '+' : '-'}${(abs / 1000).toFixed(1)}千`
  return `${val > 0 ? '+' : ''}${val.toFixed(0)}`
}

function prevMonth() {
  if (currentMonth.value === 1) {
    currentYear.value--
    currentMonth.value = 12
  } else {
    currentMonth.value--
  }
  emit('change-month', currentYear.value, currentMonth.value)
}

function nextMonth() {
  if (currentMonth.value === 12) {
    currentYear.value++
    currentMonth.value = 1
  } else {
    currentMonth.value++
  }
  emit('change-month', currentYear.value, currentMonth.value)
}

function handleClickDay(day: number) {
  const dateStr = `${currentYear.value}-${String(currentMonth.value).padStart(2, '0')}-${String(day).padStart(2, '0')}`
  emit('click-day', dateStr)
}
</script>

<style scoped>
.pnl-calendar-card {
  background: white;
  border-radius: 12px;
  padding: 16px;
}

.calendar-header {
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 12px;
  gap: 16px;
}

.calendar-title {
  font-size: 16px;
  font-weight: 600;
}

.calendar-nav {
  font-size: 18px;
  cursor: pointer;
  padding: 8px;
  color: #666;
}

.calendar-weekdays {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  margin-bottom: 4px;
}

.weekday {
  text-align: center;
  font-size: 12px;
  color: #999;
  padding: 4px 0;
}

.calendar-grid {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 2px;
}

.calendar-cell {
  min-height: 48px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  border-radius: 4px;
  cursor: pointer;
}

.calendar-cell.today {
  background: #e8f0fe;
}

.calendar-cell.empty {
  cursor: default;
}

.cell-day {
  font-size: 12px;
  color: #333;
}

.cell-pnl {
  font-size: 10px;
  font-weight: 600;
  margin-top: 1px;
}
</style>

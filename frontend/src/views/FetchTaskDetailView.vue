<template>
  <div class="detail-page">
    <!-- 顶部导航栏 -->
    <van-nav-bar
      title="任务详情"
      left-arrow
      @click-left="router.back()"
    />

    <!-- 加载状态 -->
    <van-loading v-if="taskStore.loading" class="page-loading" />

    <!-- 错误状态 -->
    <van-empty v-else-if="!task" description="任务不存在或已被删除" />

    <!-- 正常内容 -->
    <template v-else>
      <!-- 任务详情卡片 -->
      <div class="info-card">
        <div class="info-header">
          <span :class="['market-badge', `market-badge-${task.market.toLowerCase()}`]">
            {{ marketLabel(task.market) }}
          </span>
          <span class="info-name">{{ task.name }}</span>
          <span class="info-code">{{ task.code }}</span>
        </div>

        <div class="info-grid">
          <div class="info-row">
            <span class="info-label">启用状态</span>
            <div class="info-value-container">
              <van-switch
                :model-value="task.enabled"
                size="20px"
                @update:model-value="handleToggle"
              />
            </div>
          </div>
          <div class="info-row">
            <span class="info-label">计划拉取时间</span>
            <span class="info-value">
              <van-icon name="clock-o" class="info-icon" /> {{ task.run_time }}
            </span>
          </div>
          <div class="info-row">
            <span class="info-label">重复频率</span>
            <span class="info-value">
              <van-icon name="calendar-o" class="info-icon" /> {{ weekdaysLabel(task.weekdays) }}
            </span>
          </div>
          <div class="info-row">
            <span class="info-label">创建时间</span>
            <span class="info-value">{{ formatDateTime(task.created_at) }}</span>
          </div>
          <div class="info-row">
            <span class="info-label">更新时间</span>
            <span class="info-value">{{ formatDateTime(task.updated_at) }}</span>
          </div>
        </div>
      </div>

      <!-- 操作按钮区 -->
      <div class="action-bar">
        <van-button
          block
          round
          type="success"
          :loading="runNowLoading"
          :disabled="runNowDisabled"
          @click="handleRunNow"
        >
          {{ runNowText }}
        </van-button>
        <van-button block round type="primary" @click="showForm = true">编辑任务</van-button>
        <van-button block round plain type="danger" @click="handleDelete">删除任务</van-button>
      </div>

      <!-- 运行历史列表 -->
      <div class="history-section">
        <div class="section-title">
          <van-icon name="records-o" class="section-title-icon" />
          <span>执行历史</span>
          <span class="section-subtitle" v-if="taskStore.currentRuns.length > 0">
            (共 {{ taskStore.currentRuns.length }} 条记录)
          </span>
        </div>

        <van-loading v-if="taskStore.runsLoading" class="runs-loading" />
        <div v-else-if="taskStore.currentRuns.length === 0" class="empty-history">
          暂无执行历史记录
        </div>
        <div v-else class="run-list">
          <div
            v-for="run in taskStore.currentRuns"
            :key="run.id"
            class="run-item"
          >
            <div class="run-item-head">
              <span class="run-time">{{ run.scheduled_for }}</span>
              <span :class="['run-status-badge', runStatusClass(run.status)]">
                {{ statusLabel(run.status) }}
              </span>
            </div>

            <div class="run-item-details">
              <!-- 成功状态拉取的价格数据 -->
              <div v-if="run.status === 'SUCCESS'" class="run-price-success">
                <van-icon name="checked" class="success-icon" />
                <span>最新价: <strong class="price-highlight">{{ run.price_value }}</strong></span>
                <span class="price-date" v-if="run.price_date">({{ run.price_date }})</span>
              </div>

              <!-- 失败状态的错误详情 -->
              <div v-if="run.status === 'FAILED' && run.error_message" class="run-error-banner">
                <van-icon name="warning" class="error-icon" />
                <span class="error-msg">{{ run.error_message }}</span>
              </div>

              <!-- 时间元数据 -->
              <div class="run-item-meta" v-if="run.started_at">
                <span>运行耗时: {{ formatDuration(run.started_at, run.finished_at) || '小于 10ms' }}</span>
                <span class="meta-divider" v-if="run.finished_at">|</span>
                <span v-if="run.finished_at">完成时间: {{ formatDateTime(run.finished_at).split(' ')[1] }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </template>

    <!-- 编辑表单弹窗 -->
    <FetchTaskForm
      v-model:show="showForm"
      :task="task"
      :holdings="holdingOptions"
      @submit="handleEditSubmit"
    />
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { showConfirmDialog, showSuccessToast } from 'vant'
import { useFetchTaskStore } from '@/stores/fetchTask'
import { useHoldingStore } from '@/stores/holding'
import FetchTaskForm from '@/components/FetchTaskForm.vue'
import type { FetchTaskCreatePayload, FetchTaskRunStatus } from '@/types/fetchTask'

const route = useRoute()
const router = useRouter()
const taskStore = useFetchTaskStore()
const holdingStore = useHoldingStore()

const taskId = Number(route.params.id)
const showForm = ref(false)
const runNowLoading = ref(false)
let activeRunPollingTimer: number | undefined
let activeRunPolling = false

const task = computed(() => {
  return taskStore.tasks.find((t) => t.id === taskId)
})

const activeRunStatus = computed(() => task.value?.latest_run?.status)
const isTaskActive = computed(() => activeRunStatus.value === 'PENDING' || activeRunStatus.value === 'RUNNING')
const runNowDisabled = computed(() => runNowLoading.value || isTaskActive.value)
const runNowText = computed(() => {
  if (runNowLoading.value) return '提交中'
  if (activeRunStatus.value === 'PENDING') return '排队中'
  if (activeRunStatus.value === 'RUNNING') return '执行中'
  return '立刻执行'
})

const holdingOptions = computed(() => {
  return holdingStore.holdings.map((holding) => ({
    id: holding.id,
    code: holding.code,
    name: holding.name,
    market: holding.market,
  }))
})

onMounted(async () => {
  await Promise.all([
    holdingStore.fetchHoldings(),
    taskStore.fetchTasks(),
    taskStore.fetchRuns(taskId),
  ])
  startActiveRunPolling()
})

onUnmounted(() => {
  stopActiveRunPolling()
})

async function handleToggle(value: boolean) {
  await taskStore.toggleTask(taskId, value)
}

async function handleRunNow() {
  if (runNowDisabled.value) return

  runNowLoading.value = true
  try {
    await taskStore.runNow(taskId)
    showSuccessToast('已加入执行队列')
    await taskStore.fetchRuns(taskId)
    startActiveRunPolling()
  } catch (error: any) {
    if (error?.response?.status === 409) {
      await Promise.all([
        taskStore.fetchTasks(),
        taskStore.fetchRuns(taskId),
      ])
      startActiveRunPolling()
      return
    }
    throw error
  } finally {
    runNowLoading.value = false
  }
}

async function handleEditSubmit(payload: FetchTaskCreatePayload) {
  await taskStore.updateTask(taskId, payload)
  showSuccessToast('任务已更新')
  showForm.value = false
  // Re-fetch runs as the target code/name might have changed
  await taskStore.fetchRuns(taskId)
}

async function handleDelete() {
  try {
    await showConfirmDialog({
      title: '确认删除',
      message: `确定要删除自动拉取任务「${task.value?.name}」吗？`,
    })
    await taskStore.deleteTask(taskId)
    showSuccessToast('任务已删除')
    router.replace('/tasks')
  } catch {
    // cancelled
  }
}

function marketLabel(market?: string) {
  if (market === 'HK_STOCK') return '港股'
  if (market === 'FUND') return '基金'
  if (market === 'A_STOCK') return 'A股'
  return '--'
}

function weekdaysLabel(weekdays?: number[]) {
  if (!weekdays) return ''
  const labels = ['一', '二', '三', '四', '五', '六', '日']
  if (weekdays.length === 7) {
    return '每天'
  }
  if (weekdays.join(',') === '0,1,2,3,4') {
    return '工作日'
  }
  return weekdays.map((day) => `周${labels[day]}`).join(' / ')
}

function statusLabel(status?: FetchTaskRunStatus) {
  if (status === 'SUCCESS') return '成功'
  if (status === 'FAILED') return '失败'
  if (status === 'RUNNING') return '执行中'
  if (status === 'PENDING') return '排队中'
  return '未执行'
}

function startActiveRunPolling() {
  stopActiveRunPolling()
  if (!isTaskActive.value) return
  scheduleNextActiveRunPoll()
}

function scheduleNextActiveRunPoll() {
  activeRunPollingTimer = window.setTimeout(pollActiveRun, 5000)
}

async function pollActiveRun() {
  if (activeRunPolling) return
  activeRunPolling = true

  try {
    await Promise.all([
      taskStore.fetchTasks({ silent: true }),
      taskStore.fetchRuns(taskId, 20, { silent: true }),
    ])
    if (isTaskActive.value) {
      scheduleNextActiveRunPoll()
      return
    }
    await Promise.all([
      taskStore.fetchTasks(),
      taskStore.fetchRuns(taskId),
    ])
  } catch {
    stopActiveRunPolling()
  } finally {
    activeRunPolling = false
  }
}

function stopActiveRunPolling() {
  if (activeRunPollingTimer == null) return
  window.clearTimeout(activeRunPollingTimer)
  activeRunPollingTimer = undefined
  activeRunPolling = false
}

function runStatusClass(status?: FetchTaskRunStatus) {
  if (status === 'SUCCESS') return 'run-status-success'
  if (status === 'FAILED') return 'run-status-failed'
  if (status === 'RUNNING') return 'run-status-running'
  if (status === 'PENDING') return 'run-status-pending'
  return 'run-status-idle'
}

function formatDuration(startedAt?: string | null, finishedAt?: string | null) {
  if (!startedAt || !finishedAt) return ''
  const start = new Date(startedAt).getTime()
  const finish = new Date(finishedAt).getTime()
  const diff = finish - start
  if (isNaN(diff) || diff < 0) return ''
  if (diff < 1000) return `${diff}ms`
  return `${(diff / 1000).toFixed(2)}s`
}

function formatDateTime(dateTimeStr?: string | null) {
  if (!dateTimeStr) return '--'
  const date = new Date(dateTimeStr)
  if (isNaN(date.getTime())) return dateTimeStr
  const y = date.getFullYear()
  const m = String(date.getMonth() + 1).padStart(2, '0')
  const d = String(date.getDate()).padStart(2, '0')
  const hh = String(date.getHours()).padStart(2, '0')
  const mm = String(date.getMinutes()).padStart(2, '0')
  const ss = String(date.getSeconds()).padStart(2, '0')
  return `${y}-${m}-${d} ${hh}:${mm}:${ss}`
}
</script>

<style scoped>
.detail-page {
  min-height: 100vh;
  background: #f7f8fa;
  padding-bottom: 32px;
}

.page-loading {
  display: flex;
  justify-content: center;
  padding: 80px 0;
}

.info-card {
  background: white;
  margin: 12px;
  border-radius: 16px;
  padding: 18px;
  box-shadow: 0 4px 16px rgba(15, 23, 42, 0.03);
  border: 1px solid #f0f0f2;
}

.info-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 16px;
  border-bottom: 1px solid #f2f3f5;
  padding-bottom: 12px;
}

.info-name {
  font-size: 17px;
  font-weight: 600;
  color: #323233;
}

.info-code {
  font-size: 13px;
  color: #969799;
  font-family: monospace;
}

.info-grid {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.info-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 13.5px;
}

.info-label {
  color: #8c8c8c;
  font-weight: 500;
}

.info-value {
  color: #323233;
  font-weight: 600;
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.info-icon {
  color: #1989fa;
  font-size: 14px;
}

.info-value-container {
  display: flex;
  align-items: center;
}

.action-bar {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 0 12px;
  margin-bottom: 24px;
}

/* 市场类型徽章 - 必须与投资持仓页面完全一致 */
.market-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 2px 7px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 600;
  line-height: 1;
  flex-shrink: 0;
}

.market-badge-a_stock {
  background: #e8f3ff;
  color: #1f6fd6;
}

.market-badge-hk_stock {
  background: #fff1e8;
  color: #d46b08;
}

.market-badge-fund {
  background: #edf8ee;
  color: #389e0d;
}

/* 运行历史区 */
.history-section {
  background: white;
  margin: 0 12px;
  border-radius: 16px;
  padding: 18px;
  box-shadow: 0 4px 16px rgba(15, 23, 42, 0.03);
  border: 1px solid #f0f0f2;
}

.section-title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 15px;
  font-weight: 700;
  color: #323233;
  margin-bottom: 16px;
}

.section-title-icon {
  font-size: 16px;
  color: #1989fa;
}

.section-subtitle {
  font-size: 12px;
  font-weight: 400;
  color: #8c8c8c;
  margin-left: 4px;
}

.runs-loading {
  display: flex;
  justify-content: center;
  padding: 24px 0;
}

.empty-history {
  text-align: center;
  padding: 32px 0;
  color: #969799;
  font-size: 13.5px;
}

.run-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.run-item {
  background: #f7f8fa;
  border-radius: 12px;
  padding: 12px 14px;
  border: 1px solid #f0f0f2;
  transition: all 0.2s ease;
}

.run-item:active {
  background: #f2f3f5;
}

.run-item-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 13.5px;
  margin-bottom: 8px;
}

.run-time {
  font-weight: 600;
  color: #323233;
  font-family: monospace;
}

.run-status-badge {
  font-size: 11px;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 999px;
  line-height: 1;
}

.run-status-success { background: #edf8ee; color: #389e0d; }
.run-status-failed { background: #fff0f0; color: #ee0a24; }
.run-status-running { background: #e8f3ff; color: #1989fa; }
.run-status-pending { background: #fff7e6; color: #ff976a; }

.run-item-details {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.run-price-success {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12.5px;
  color: #3c763d;
  background: rgba(7, 193, 96, 0.04);
  padding: 6px 8px;
  border-radius: 6px;
  border: 1px solid rgba(7, 193, 96, 0.1);
}

.success-icon {
  font-size: 14px;
  color: #07c160;
}

.price-highlight {
  font-weight: 700;
  color: #389e0d;
}

.price-date {
  color: #8c8c8c;
  font-size: 11px;
}

.run-error-banner {
  display: flex;
  align-items: flex-start;
  gap: 4px;
  font-size: 12px;
  color: #ee0a24;
  background: rgba(238, 10, 36, 0.04);
  padding: 6px 8px;
  border-radius: 6px;
  border: 1px solid rgba(238, 10, 36, 0.1);
  word-break: break-all;
}

.error-icon {
  font-size: 14px;
  margin-top: 1px;
  flex-shrink: 0;
}

.error-msg {
  line-height: 1.3;
}

.run-item-meta {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 11px;
  color: #8c8c8c;
  padding-left: 2px;
}

.meta-divider {
  color: #d9d9d9;
}
</style>

<template>
  <div class="task-page">
    <div class="task-toolbar">
      <div>
        <div class="task-title">自动拉取任务</div>
      </div>
      <van-button size="small" type="primary" icon="plus" @click="openCreateForm">新建</van-button>
    </div>

    <van-loading v-if="taskStore.loading" class="page-loading" />
    <div v-else-if="taskStore.tasks.length === 0" class="empty-tip">
      暂无任务，点击右上角新建
    </div>
    <div v-else class="task-list">
      <div v-for="task in taskStore.tasks" :key="task.id" class="task-card">
        <div class="task-card-header">
          <div>
            <div class="task-card-title">
              {{ task.name }}
              <span class="task-card-code">{{ task.code }}</span>
            </div>
            <div class="task-card-meta">
              {{ marketLabel(task.market) }} · {{ task.run_time }} · {{ weekdaysLabel(task.weekdays) }}
            </div>
          </div>
          <van-switch
            :model-value="task.enabled"
            size="22px"
            @update:model-value="(value) => handleToggle(task.id, value)"
          />
        </div>

        <div class="task-card-status" @click="openRuns(task)">
          <van-icon :name="statusIcon(task.latest_run?.status)" :class="['task-status-icon', statusClass(task.latest_run?.status)]" />
          <div class="task-status-text">
            <div class="task-status-title">{{ statusLabel(task.latest_run?.status) }}</div>
            <div class="task-status-subtitle">
              {{ task.latest_run ? `最近一次：${task.latest_run.scheduled_for}` : '尚未执行' }}
            </div>
          </div>
          <van-icon name="arrow" class="task-arrow" />
        </div>

        <div class="task-card-actions">
          <van-button size="small" plain @click="openEditForm(task)">编辑</van-button>
          <van-button size="small" plain type="danger" @click="handleDelete(task.id, task.name)">删除</van-button>
        </div>
      </div>
    </div>

    <FetchTaskForm
      v-model:show="showForm"
      :task="editingTask"
      :holdings="holdingOptions"
      @submit="handleSubmit"
    />

    <van-popup :show="showRuns" position="bottom" round @update:show="showRuns = $event">
      <div class="runs-panel">
        <div class="runs-title">{{ selectedTask?.name }} 执行记录</div>
        <van-loading v-if="taskStore.runsLoading" class="page-loading" />
        <div v-else-if="taskStore.currentRuns.length === 0" class="empty-tip">
          暂无执行记录
        </div>
        <div v-else class="run-list">
          <div v-for="run in taskStore.currentRuns" :key="run.id" class="run-item">
            <div class="run-item-head">
              <span>{{ run.scheduled_for }}</span>
              <span :class="['run-status', statusClass(run.status)]">{{ statusLabel(run.status) }}</span>
            </div>
            <div class="run-item-meta">
              {{ run.started_at || '-' }} → {{ run.finished_at || '-' }}
            </div>
            <div v-if="run.price_date || run.price_value != null" class="run-item-meta">
              {{ run.price_date || '-' }} · {{ run.price_value ?? '-' }}
            </div>
            <div v-if="run.error_message" class="run-item-error">{{ run.error_message }}</div>
          </div>
        </div>
      </div>
    </van-popup>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { showConfirmDialog, showSuccessToast } from 'vant'
import FetchTaskForm from '@/components/FetchTaskForm.vue'
import { useFetchTaskStore } from '@/stores/fetchTask'
import { useHoldingStore } from '@/stores/holding'
import type { FetchTask, FetchTaskCreatePayload, FetchTaskRunStatus } from '@/types/fetchTask'

const taskStore = useFetchTaskStore()
const holdingStore = useHoldingStore()

const showForm = ref(false)
const editingTask = ref<FetchTask | null>(null)
const showRuns = ref(false)
const selectedTask = ref<FetchTask | null>(null)

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
  ])
})

function marketLabel(market: FetchTask['market']) {
  if (market === 'HK_STOCK') return '港股'
  if (market === 'FUND') return '基金'
  return 'A股'
}

function weekdaysLabel(weekdays: number[]) {
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
  if (status === 'SUCCESS') return '最近成功'
  if (status === 'FAILED') return '最近失败'
  if (status === 'RUNNING') return '执行中'
  if (status === 'PENDING') return '排队中'
  return '未执行'
}

function statusIcon(status?: FetchTaskRunStatus) {
  if (status === 'SUCCESS') return 'success'
  if (status === 'FAILED') return 'warning-o'
  if (status === 'RUNNING') return 'underway-o'
  if (status === 'PENDING') return 'clock-o'
  return 'question-o'
}

function statusClass(status?: FetchTaskRunStatus) {
  if (status === 'SUCCESS') return 'status-success'
  if (status === 'FAILED') return 'status-failed'
  if (status === 'RUNNING') return 'status-running'
  if (status === 'PENDING') return 'status-pending'
  return 'status-idle'
}

function openCreateForm() {
  editingTask.value = null
  showForm.value = true
}

function openEditForm(task: FetchTask) {
  editingTask.value = task
  showForm.value = true
}

async function handleSubmit(payload: FetchTaskCreatePayload) {
  if (editingTask.value) {
    await taskStore.updateTask(editingTask.value.id, payload)
    showSuccessToast('任务已更新')
  } else {
    await taskStore.createTask(payload)
    showSuccessToast('任务已创建')
  }
  showForm.value = false
  editingTask.value = null
}

async function handleToggle(taskId: number, enabled: boolean) {
  await taskStore.toggleTask(taskId, enabled)
}

async function handleDelete(taskId: number, taskName: string) {
  try {
    await showConfirmDialog({
      title: '确认删除',
      message: `确定删除任务「${taskName}」？`,
    })
    await taskStore.deleteTask(taskId)
    showSuccessToast('任务已删除')
  } catch {
    // cancelled
  }
}

async function openRuns(task: FetchTask) {
  selectedTask.value = task
  showRuns.value = true
  await taskStore.fetchRuns(task.id, 20)
}
</script>

<style scoped>
.task-page {
  padding: 12px;
}

.task-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
  margin-bottom: 12px;
}

.task-title {
  font-size: 20px;
  font-weight: 700;
}

.task-subtitle {
  color: #666;
  font-size: 13px;
  margin-top: 4px;
}

.task-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.task-card {
  background: #fff;
  border-radius: 14px;
  padding: 14px;
  box-shadow: 0 6px 16px rgba(15, 23, 42, 0.06);
}

.task-card-header {
  display: flex;
  justify-content: space-between;
  gap: 12px;
}

.task-card-title {
  font-size: 16px;
  font-weight: 700;
  line-height: 1.4;
}

.task-card-code {
  color: #888;
  font-size: 13px;
  margin-left: 6px;
}

.task-card-meta {
  margin-top: 4px;
  color: #666;
  font-size: 13px;
}

.task-card-status {
  margin-top: 12px;
  border-radius: 12px;
  background: #f7f8fa;
  padding: 10px 12px;
  display: flex;
  align-items: center;
  gap: 10px;
}

.task-status-icon {
  font-size: 20px;
}

.task-status-text {
  flex: 1;
  min-width: 0;
}

.task-status-title {
  font-size: 14px;
  font-weight: 600;
}

.task-status-subtitle {
  color: #666;
  font-size: 12px;
  margin-top: 2px;
}

.task-arrow {
  color: #999;
}

.task-card-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  margin-top: 12px;
}

.status-success {
  color: #07c160;
}

.status-failed {
  color: #ee0a24;
}

.status-running {
  color: #1989fa;
}

.status-pending {
  color: #ff976a;
}

.status-idle {
  color: #969799;
}

.page-loading,
.empty-tip {
  text-align: center;
  padding: 24px 0;
  color: #666;
}

.runs-panel {
  padding: 20px 16px calc(20px + env(safe-area-inset-bottom));
  max-height: 70vh;
  overflow-y: auto;
}

.runs-title {
  font-size: 18px;
  font-weight: 700;
  margin-bottom: 16px;
}

.run-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.run-item {
  background: #f7f8fa;
  border-radius: 12px;
  padding: 12px;
}

.run-item-head {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  font-size: 14px;
}

.run-status {
  font-weight: 600;
}

.run-item-meta {
  margin-top: 6px;
  color: #666;
  font-size: 12px;
}

.run-item-error {
  margin-top: 6px;
  color: #ee0a24;
  font-size: 12px;
  word-break: break-word;
}
</style>

<template>
  <div class="task-page">
    <div class="task-toolbar">
      <div>
        <div class="task-title">自动拉取任务</div>
        <div class="task-stats">
          共 <span class="stat-num">{{ taskStore.tasks.length }}</span> 个任务
          <span class="stat-divider">·</span>
          已启用 <span class="stat-num enabled">{{ taskStore.tasks.filter(t => t.enabled).length }}</span> 个
          <span class="stat-divider">·</span>
          最近失败 <span class="stat-num failed">{{ taskStore.tasks.filter(t => t.enabled && t.latest_run?.status === 'FAILED').length }}</span> 个
        </div>
      </div>
      <van-button size="small" type="primary" icon="plus" @click="openCreateForm">新建</van-button>
    </div>

    <van-loading v-if="taskStore.loading" class="page-loading" />
    <div v-else-if="taskStore.tasks.length === 0" class="empty-tip">
      暂无任务，点击右上角新建
    </div>
    <div v-else class="task-list">
      <!-- 点击整张卡片跳转至详情页 -->
      <div
        v-for="task in taskStore.tasks"
        :key="task.id"
        :class="['task-card', { 'task-card-disabled': !task.enabled }]"
        @click="handleViewTask(task.id)"
      >
        <div class="task-card-header">
          <div>
            <div class="task-card-title">
              {{ task.name }}
              <span class="task-card-code">{{ task.code }}</span>
            </div>
            <div class="task-card-meta">
              <span :class="['market-badge', `market-badge-${task.market.toLowerCase()}`]">
                {{ marketLabel(task.market) }}
              </span>
              <span class="meta-divider">·</span>
              <span class="meta-time"><van-icon name="clock-o" /> {{ task.run_time }}</span>
              <span class="meta-divider">·</span>
              <span class="meta-weekdays"><van-icon name="calendar-o" /> {{ weekdaysLabel(task.weekdays) }}</span>
            </div>
          </div>
          <!-- @click.stop 阻止冒泡跳转 -->
          <van-switch
            :model-value="task.enabled"
            size="22px"
            @click.stop
            @update:model-value="(value) => handleToggle(task.id, value)"
          />
        </div>

        <div :class="['task-card-status', statusBgClass(task.latest_run?.status)]">
          <van-icon :name="statusIcon(task.latest_run?.status)" :class="['task-status-icon', statusClass(task.latest_run?.status), { 'task-icon-spin': task.latest_run?.status === 'RUNNING' }]" />
          <div class="task-status-text">
            <div class="task-status-title">
              {{ statusLabel(task.latest_run?.status) }}
              <span v-if="task.latest_run?.status === 'SUCCESS' && task.latest_run?.price_value != null" class="task-status-price">
                (最新价: {{ task.latest_run.price_value }})
              </span>
            </div>
            <div class="task-status-subtitle">
              {{ task.latest_run ? `最近一次：${task.latest_run.scheduled_for}` : '尚未执行' }}
            </div>
          </div>
          <van-icon name="arrow" class="task-arrow" />
        </div>
      </div>
    </div>

    <!-- 创建任务弹窗 -->
    <FetchTaskForm
      v-model:show="showForm"
      :task="editingTask"
      :holdings="holdingOptions"
      @submit="handleSubmit"
    />
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { showSuccessToast } from 'vant'
import FetchTaskForm from '@/components/FetchTaskForm.vue'
import { useFetchTaskStore } from '@/stores/fetchTask'
import { useHoldingStore } from '@/stores/holding'
import type { FetchTask, FetchTaskCreatePayload, FetchTaskRunStatus } from '@/types/fetchTask'

const taskStore = useFetchTaskStore()
const holdingStore = useHoldingStore()
const router = useRouter()

const showForm = ref(false)
const editingTask = ref<FetchTask | null>(null)

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

function handleViewTask(taskId: number) {
  router.push(`/tasks/${taskId}`)
}

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

function statusBgClass(status?: FetchTaskRunStatus) {
  if (status === 'SUCCESS') return 'status-bg-success'
  if (status === 'FAILED') return 'status-bg-failed'
  if (status === 'RUNNING') return 'status-bg-running'
  if (status === 'PENDING') return 'status-bg-pending'
  return 'status-bg-idle'
}

function openCreateForm() {
  editingTask.value = null
  showForm.value = true
}

async function handleSubmit(payload: FetchTaskCreatePayload) {
  await taskStore.createTask(payload)
  showSuccessToast('任务已创建')
  showForm.value = false
  editingTask.value = null
}

async function handleToggle(taskId: number, enabled: boolean) {
  await taskStore.toggleTask(taskId, enabled)
}
</script>

<style scoped>
.task-page {
  padding: 12px;
}

.task-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.task-title {
  font-size: 20px;
  font-weight: 700;
  color: #323233;
}

.task-stats {
  font-size: 11px;
  color: #8c8c8c;
  margin-top: 4px;
  display: flex;
  align-items: center;
  gap: 4px;
}

.stat-num {
  font-weight: 600;
  color: #323233;
}

.stat-num.enabled {
  color: #1989fa;
}

.stat-num.failed {
  color: #ee0a24;
}

.stat-divider {
  color: #d9d9d9;
}

.task-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.task-card {
  background: #fff;
  border-radius: 14px;
  padding: 14px;
  box-shadow: 0 6px 16px rgba(15, 23, 42, 0.04);
  border: 1px solid #f0f0f2;
  transition: all 0.25s ease;
  cursor: pointer;
}

.task-card:active {
  background: #f7f8fa;
  transform: scale(0.99);
}

.task-card-disabled {
  opacity: 0.6;
}

.task-card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
}

.task-card-title {
  font-size: 16px;
  font-weight: 600;
  color: #323233;
  line-height: 1.4;
  display: flex;
  align-items: center;
  flex-wrap: wrap;
}

.task-card-code {
  color: #999;
  font-size: 13px;
  margin-left: 6px;
  font-weight: 400;
}

.task-card-meta {
  margin-top: 8px;
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 6px;
  color: #666;
  font-size: 12px;
}

.meta-divider {
  color: #e5e5e5;
}

.meta-time,
.meta-weekdays {
  display: inline-flex;
  align-items: center;
  gap: 2px;
}

/* 市场类型徽章 - 对齐投资持仓页面 */
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

/* 最近执行条 */
.task-card-status {
  margin-top: 12px;
  border-radius: 12px;
  padding: 10px 12px;
  display: flex;
  align-items: center;
  gap: 10px;
  border-left: 3px solid transparent;
  background: #f7f8fa;
}

.status-bg-success {
  background: rgba(7, 193, 96, 0.05);
  border-left-color: #07c160;
}

.status-bg-failed {
  background: rgba(238, 10, 36, 0.05);
  border-left-color: #ee0a24;
}

.status-bg-running {
  background: rgba(25, 137, 250, 0.05);
  border-left-color: #1989fa;
}

.status-bg-pending {
  background: rgba(255, 151, 106, 0.05);
  border-left-color: #ff976a;
}

.status-bg-idle {
  background: #f7f8fa;
  border-left-color: #969799;
}

.task-status-icon {
  font-size: 18px;
}

.status-success { color: #07c160; }
.status-failed { color: #ee0a24; }
.status-running { color: #1989fa; }
.status-pending { color: #ff976a; }
.status-idle { color: #969799; }

.task-status-text {
  flex: 1;
  min-width: 0;
}

.task-status-title {
  font-size: 13px;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 4px;
}

.task-status-price {
  font-size: 11px;
  font-weight: 500;
  color: #389e0d;
}

.task-status-subtitle {
  color: #8c8c8c;
  font-size: 11px;
  margin-top: 2px;
}

.task-arrow {
  color: #c8c9cc;
  font-size: 14px;
}

.task-icon-spin {
  animation: spin 1.2s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.page-loading,
.empty-tip {
  text-align: center;
  padding: 36px 0;
  color: #969799;
  font-size: 14px;
}
</style>

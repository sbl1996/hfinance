<template>
  <div class="auth-page">
    <div class="auth-card">
      <h1 class="auth-title">💰 HFinance</h1>
      <p class="auth-subtitle">个人资产管理记账系统</p>
      <van-field
        v-model="password"
        type="password"
        label="访问密码"
        placeholder="请输入访问密码"
        @keyup.enter="handleLogin"
      />
      <van-button
        type="primary"
        block
        round
        class="auth-btn"
        :loading="loading"
        @click="handleLogin"
      >
        登录
      </van-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()
const password = ref('')
const loading = ref(false)

async function handleLogin() {
  if (!password.value) return
  loading.value = true
  try {
    await authStore.login(password.value)
    router.push('/dashboard')
  } catch {
    password.value = ''
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.auth-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 24px;
}

.auth-card {
  width: 100%;
  max-width: 360px;
  background: white;
  border-radius: 16px;
  padding: 40px 24px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
}

.auth-title {
  text-align: center;
  font-size: 28px;
  margin-bottom: 8px;
}

.auth-subtitle {
  text-align: center;
  color: #999;
  font-size: 15px;
  margin-bottom: 32px;
}

.auth-btn {
  margin-top: 24px;
}
</style>

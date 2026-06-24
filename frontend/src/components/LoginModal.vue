<script setup lang="ts">
import { ref } from 'vue'

const emit = defineEmits<{
  login: [user: { token: string; user_id: number; username: string; nickname: string }]
  close: []
}>()

const mode = ref<'login' | 'register'>('login')
const username = ref('')
const password = ref('')
const nickname = ref('')
const loading = ref(false)
const error = ref('')

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const handleSubmit = async () => {
  if (!username.value || !password.value) {
    error.value = '请填写用户名和密码'
    return
  }

  loading.value = true
  error.value = ''

  try {
    const endpoint = mode.value === 'login' ? '/api/auth/login' : '/api/auth/register'
    const body = mode.value === 'login'
      ? { username: username.value, password: password.value }
      : { username: username.value, password: password.value, nickname: nickname.value }

    const res = await fetch(`${API_BASE}${endpoint}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    })

    if (!res.ok) {
      const data = await res.json()
      throw new Error(data.detail || '操作失败')
    }

    const data = await res.json()
    localStorage.setItem('mh_token', data.token)
    localStorage.setItem('mh_user', JSON.stringify(data))
    emit('login', data)
  } catch (e: any) {
    error.value = e.message || '网络错误'
  } finally {
    loading.value = false
  }
}

const switchMode = () => {
  mode.value = mode.value === 'login' ? 'register' : 'login'
  error.value = ''
}
</script>

<template>
  <div class="login-overlay" @click.self="emit('close')">
    <div class="login-panel">
      <button class="close-btn" @click="emit('close')">✕</button>

      <div class="panel-header">
        <div class="panel-icon">🧠</div>
        <h2>{{ mode === 'login' ? '登录' : '注册' }}</h2>
        <p class="panel-subtitle">{{ mode === 'login' ? '继续你的记忆修复之旅' : '开始新的旅程' }}</p>
      </div>

      <form @submit.prevent="handleSubmit" class="login-form">
        <div class="form-group">
          <label>用户名</label>
          <input
            v-model="username"
            type="text"
            placeholder="3-20位字母或数字"
            autocomplete="username"
          />
        </div>

        <div class="form-group" v-if="mode === 'register'">
          <label>昵称</label>
          <input
            v-model="nickname"
            type="text"
            placeholder="可选，默认为用户名"
          />
        </div>

        <div class="form-group">
          <label>密码</label>
          <input
            v-model="password"
            type="password"
            placeholder="至少6位"
            autocomplete="current-password"
          />
        </div>

        <div class="error-msg" v-if="error">{{ error }}</div>

        <button type="submit" class="submit-btn" :disabled="loading">
          {{ loading ? '处理中...' : (mode === 'login' ? '登录' : '注册') }}
        </button>
      </form>

      <div class="switch-mode">
        <span>{{ mode === 'login' ? '还没有账号？' : '已有账号？' }}</span>
        <button @click="switchMode" class="switch-btn">
          {{ mode === 'login' ? '去注册' : '去登录' }}
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.login-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 200;
  backdrop-filter: blur(8px);
}

.login-panel {
  background: linear-gradient(135deg, #1a1a3e, #2a2a5e);
  border: 1px solid rgba(100, 150, 255, 0.3);
  border-radius: 16px;
  padding: 40px;
  width: 380px;
  max-width: 90vw;
  position: relative;
  box-shadow: 0 0 60px rgba(58, 95, 205, 0.2);
}

.close-btn {
  position: absolute;
  top: 16px;
  right: 16px;
  background: none;
  border: none;
  color: rgba(150, 170, 220, 0.6);
  font-size: 18px;
  cursor: pointer;
}

.panel-header {
  text-align: center;
  margin-bottom: 32px;
}

.panel-icon {
  font-size: 48px;
  margin-bottom: 12px;
}

.panel-header h2 {
  font-size: 24px;
  color: #e0e0ff;
  margin: 0 0 8px;
}

.panel-subtitle {
  font-size: 14px;
  color: rgba(150, 170, 220, 0.6);
  margin: 0;
}

.login-form {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.form-group label {
  font-size: 13px;
  color: rgba(150, 170, 220, 0.7);
}

.form-group input {
  padding: 12px 16px;
  border-radius: 8px;
  border: 1px solid rgba(100, 150, 255, 0.2);
  background: rgba(0, 0, 0, 0.3);
  color: #e0e0ff;
  font-size: 14px;
  font-family: 'Noto Serif SC', serif;
  outline: none;
  transition: border-color 0.2s;
}

.form-group input:focus {
  border-color: rgba(58, 95, 205, 0.5);
}

.form-group input::placeholder {
  color: rgba(150, 170, 220, 0.3);
}

.error-msg {
  color: #f87171;
  font-size: 13px;
  text-align: center;
  padding: 8px;
  background: rgba(248, 113, 113, 0.1);
  border-radius: 6px;
}

.submit-btn {
  padding: 14px;
  border-radius: 8px;
  border: none;
  background: linear-gradient(135deg, #3a5fcd, #5078e0);
  color: white;
  font-size: 16px;
  font-family: 'Noto Serif SC', serif;
  cursor: pointer;
  transition: all 0.2s;
}

.submit-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 4px 20px rgba(58, 95, 205, 0.4);
}

.submit-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.switch-mode {
  text-align: center;
  margin-top: 24px;
  font-size: 13px;
  color: rgba(150, 170, 220, 0.6);
}

.switch-btn {
  background: none;
  border: none;
  color: #60a5fa;
  cursor: pointer;
  font-size: 13px;
  font-family: 'Noto Serif SC', serif;
  text-decoration: underline;
}
</style>

<script setup lang="ts">
import { ref } from 'vue'
import type { AuthUser } from '../types/game'

const emit = defineEmits<{
  login: [user: AuthUser]
  close: []
}>()

const mode = ref<'login' | 'register'>('login')
const username = ref('')
const password = ref('')
const nickname = ref('')
const loading = ref(false)
const error = ref('')

const handleSubmit = async () => {
  if (!username.value || !password.value) {
    error.value = '请填写用户名和密码'
    return
  }

  loading.value = true
  error.value = ''

  try {
    const endpoint = mode.value === 'login' ? '/api/auth/login' : '/api/auth/register'
    const body =
      mode.value === 'login'
        ? { username: username.value, password: password.value }
        : { username: username.value, password: password.value, nickname: nickname.value }

    const res = await fetch(endpoint, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
      credentials: 'include',
    })

    if (!res.ok) {
      const data = await res.json()
      throw new Error(data.error?.message || data.detail || '操作失败')
    }

    const data = await res.json()
    localStorage.setItem('mh_user', JSON.stringify(data))
    emit('login', data)
  } catch (caught: unknown) {
    error.value = caught instanceof Error ? caught.message : '网络错误'
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
  <div
    class="login-overlay"
    role="dialog"
    aria-modal="true"
    :aria-label="mode === 'login' ? '登录拾忆' : '注册拾忆'"
    @click.self="emit('close')"
  >
    <section class="login-panel">
      <button class="close-btn" type="button" aria-label="关闭登录窗口" @click="emit('close')">
        关闭
      </button>

      <header class="panel-header">
        <span class="panel-index">IDENTITY / MEMORY HEALER</span>
        <h2>{{ mode === 'login' ? '重返记忆场' : '建立修复师档案' }}</h2>
        <p>{{ mode === 'login' ? '连接你的记忆档案与云端存档' : '从这里开始第一段记忆' }}</p>
      </header>

      <form class="login-form" @submit.prevent="handleSubmit">
        <div class="form-group">
          <label for="auth-username">用户名</label>
          <input
            id="auth-username"
            v-model="username"
            type="text"
            placeholder="3–20 位字母或数字"
            autocomplete="username"
          />
        </div>

        <div v-if="mode === 'register'" class="form-group">
          <label for="auth-nickname">昵称 <small>可选</small></label>
          <input
            id="auth-nickname"
            v-model="nickname"
            type="text"
            placeholder="记忆场中显示的名字"
            autocomplete="nickname"
          />
        </div>

        <div class="form-group">
          <label for="auth-password">密码</label>
          <input
            id="auth-password"
            v-model="password"
            type="password"
            placeholder="8–128 位"
            :autocomplete="mode === 'register' ? 'new-password' : 'current-password'"
          />
        </div>

        <p v-if="error" class="error-msg" role="alert">{{ error }}</p>

        <button type="submit" class="submit-btn" :disabled="loading">
          <span>{{ loading ? '正在连接' : mode === 'login' ? '进入档案' : '创建档案' }}</span>
          <span aria-hidden="true">→</span>
        </button>
      </form>

      <footer class="switch-mode">
        <span>{{ mode === 'login' ? '第一次进入拾忆？' : '已经拥有档案？' }}</span>
        <button type="button" class="switch-btn" @click="switchMode">
          {{ mode === 'login' ? '创建账号' : '返回登录' }}
        </button>
      </footer>
    </section>
  </div>
</template>

<style scoped>
.login-overlay {
  position: fixed;
  z-index: 500;
  inset: 0;
  display: grid;
  place-items: center;
  padding: 1.25rem;
  background: rgba(3, 4, 3, 0.76);
  backdrop-filter: blur(24px) saturate(0.7);
}

.login-panel {
  position: relative;
  width: min(29rem, 100%);
  padding: clamp(2rem, 5vw, 3.8rem);
  border: 1px solid rgba(214, 173, 102, 0.26);
  background:
    linear-gradient(140deg, rgba(185, 73, 54, 0.07), transparent 42%), rgba(10, 11, 10, 0.97);
  box-shadow: 0 3rem 8rem rgba(0, 0, 0, 0.68);
}

.login-panel::before {
  position: absolute;
  top: 0.75rem;
  left: 0.75rem;
  width: 2.8rem;
  height: 2.8rem;
  border-top: 1px solid var(--gold-300);
  border-left: 1px solid var(--gold-300);
  content: '';
  pointer-events: none;
}

.close-btn {
  position: absolute;
  top: 1rem;
  right: 1rem;
  min-height: 2.4rem;
  padding: 0 0.75rem;
  border: 1px solid rgba(215, 196, 162, 0.12);
  color: rgba(241, 229, 206, 0.5);
  background: transparent;
  font-size: 0.65rem;
  letter-spacing: 0.15em;
  cursor: pointer;
}

.panel-header {
  margin-bottom: 2rem;
}

.panel-index {
  color: var(--gold-300);
  font:
    600 0.52rem/1.2 ui-monospace,
    monospace;
  letter-spacing: 0.2em;
}

.panel-header h2 {
  margin: 0.9rem 0 0.55rem;
  font-size: clamp(1.6rem, 5vw, 2.1rem);
  font-weight: 500;
  letter-spacing: 0.12em;
}

.panel-header p {
  margin: 0;
  color: rgba(215, 196, 162, 0.54);
  font-size: 0.78rem;
  letter-spacing: 0.08em;
}

.login-form {
  display: flex;
  flex-direction: column;
  gap: 1.2rem;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.45rem;
}

.form-group label {
  display: flex;
  justify-content: space-between;
  color: rgba(241, 229, 206, 0.68);
  font-size: 0.7rem;
  letter-spacing: 0.14em;
}

.form-group label small {
  color: rgba(215, 196, 162, 0.38);
}

.form-group input {
  min-height: 3rem;
  padding: 0 0.9rem;
  border: 1px solid rgba(215, 196, 162, 0.14);
  border-radius: 0;
  color: var(--paper-100);
  background: rgba(0, 0, 0, 0.25);
  outline: none;
  transition:
    border-color 180ms ease,
    background 180ms ease;
}

.form-group input:focus {
  border-color: rgba(214, 173, 102, 0.58);
  background: rgba(166, 109, 44, 0.06);
}

.form-group input::placeholder {
  color: rgba(215, 196, 162, 0.26);
}

.error-msg {
  margin: 0;
  padding: 0.7rem 0.85rem;
  border-left: 2px solid var(--cinnabar-400);
  color: #d88778;
  background: rgba(185, 73, 54, 0.08);
  font-size: 0.72rem;
}

.submit-btn {
  display: flex;
  align-items: center;
  justify-content: space-between;
  min-height: 3.2rem;
  padding: 0 1rem;
  border: 1px solid rgba(214, 173, 102, 0.52);
  color: var(--paper-100);
  background: linear-gradient(90deg, rgba(166, 109, 44, 0.24), transparent), rgba(8, 8, 7, 0.8);
  cursor: pointer;
}

.submit-btn:hover:not(:disabled) {
  border-color: var(--gold-300);
}

.submit-btn:disabled {
  opacity: 0.5;
  cursor: wait;
}

.switch-mode {
  display: flex;
  justify-content: flex-end;
  gap: 0.7rem;
  margin-top: 1.6rem;
  color: rgba(215, 196, 162, 0.48);
  font-size: 0.7rem;
}

.switch-btn {
  padding: 0;
  border: 0;
  border-bottom: 1px solid rgba(214, 173, 102, 0.4);
  color: var(--gold-300);
  background: transparent;
  cursor: pointer;
}

@media (max-width: 520px) {
  .login-overlay {
    align-items: end;
    padding: 0;
  }

  .login-panel {
    width: 100%;
    padding: 2.5rem 1.3rem max(1.6rem, calc(env(safe-area-inset-bottom) + 1rem));
    border-right: 0;
    border-bottom: 0;
    border-left: 0;
  }
}
</style>

<script setup lang="ts">
/**
 * 登录/注册页面 — 皮影戏风格
 */
import { ref } from 'vue'
import { useAuth } from '../composables/useAuth'

const emit = defineEmits<{
  success: []
  cancel: []
}>()

const { register, login, loading, error } = useAuth()
const mode = ref<'login' | 'register'>('login')
const username = ref('')
const password = ref('')
const nickname = ref('')

async function handleSubmit() {
  if (!username.value || !password.value) return
  let ok: boolean
  if (mode.value === 'login') {
    ok = await login(username.value, password.value)
  } else {
    ok = await register(username.value, password.value, nickname.value)
  }
  if (ok) emit('success')
}

function toggleMode() {
  mode.value = mode.value === 'login' ? 'register' : 'login'
}
</script>

<template>
  <div class="auth-overlay" @click.self="emit('cancel')">
    <div class="auth-scroll">
      <!-- 卷轴顶 -->
      <div class="scrl-top">
        <div class="rod"></div>
        <div class="orn">卷</div>
        <div class="rod"></div>
      </div>

      <div class="auth-body">
        <div class="auth-icon">🧠</div>
        <h2 class="auth-title">{{ mode === 'login' ? '登录 · 拾忆' : '注册 · 拾忆' }}</h2>

        <form @submit.prevent="handleSubmit" class="auth-form">
          <div class="field">
            <label>用户名</label>
            <input
              v-model="username"
              type="text"
              placeholder="输入用户名"
              autocomplete="username"
              maxlength="20"
            />
          </div>

          <div class="field" v-if="mode === 'register'">
            <label>昵称（可选）</label>
            <input
              v-model="nickname"
              type="text"
              placeholder="游戏内显示的名字"
              maxlength="20"
            />
          </div>

          <div class="field">
            <label>密码</label>
            <input
              v-model="password"
              type="password"
              :placeholder="mode === 'register' ? '密码长度4-50' : '输入密码'"
              autocomplete="current-password"
              maxlength="50"
            />
          </div>

          <div v-if="error" class="auth-error">{{ error }}</div>

          <button type="submit" class="auth-btn" :disabled="loading || !username || !password">
            <span v-if="loading" class="auth-spinner"></span>
            <span v-else>{{ mode === 'login' ? '拾忆之门' : '开启旅程' }}</span>
          </button>
        </form>

        <div class="auth-toggle">
          <span v-if="mode === 'login'">还没有账号？</span>
          <span v-else>已有账号？</span>
          <button class="toggle-btn" @click="toggleMode">
            {{ mode === 'login' ? '注册' : '去登录' }}
          </button>
        </div>

        <button class="skip-btn" @click="emit('success')">
          跳过登录，直接开始
        </button>
      </div>

      <div class="scrl-top">
        <div class="rod"></div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.auth-overlay {
  position: fixed;
  inset: 0;
  z-index: 200;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0,0,0,0.7);
  backdrop-filter: blur(4px);
}

.auth-scroll {
  width: 400px;
  max-width: 92vw;
  background: linear-gradient(160deg, #120f1a 0%, #1a1525 100%);
  border: 1px solid rgba(255,180,60,0.25);
  border-radius: 14px;
  overflow: hidden;
  animation: unfurl 0.5s ease;
}

@keyframes unfurl {
  from { transform: scaleY(0.8); opacity: 0; }
  to { transform: scaleY(1); opacity: 1; }
}

.scrl-top {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 16px;
}

.rod {
  flex: 1;
  height: 3px;
  background: linear-gradient(90deg, transparent, #c9a44a, transparent);
  border-radius: 2px;
}

.orn {
  width: 28px; height: 28px;
  border: 2px solid #c9a44a;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #ffd700;
  font-size: 12px;
  font-family: 'Noto Serif SC', serif;
}

.auth-body {
  padding: 24px 32px;
  text-align: center;
}

.auth-icon {
  font-size: 40px;
  margin-bottom: 8px;
}

.auth-title {
  font-size: 22px;
  color: #e0d8c8;
  font-family: 'Noto Serif SC', serif;
  margin: 0 0 24px;
}

.auth-form {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.field {
  text-align: left;
}

.field label {
  display: block;
  font-size: 13px;
  color: #8a8090;
  margin-bottom: 4px;
}

.field input {
  width: 100%;
  padding: 10px 14px;
  background: rgba(255,255,255,0.04);
  border: 1px solid rgba(255,255,255,0.1);
  border-radius: 8px;
  color: #e0d8c8;
  font-size: 14px;
  outline: none;
  transition: border-color 0.2s;
}

.field input:focus {
  border-color: #c9a44a;
}

.field input::placeholder {
  color: rgba(255,255,255,0.15);
}

.auth-error {
  font-size: 13px;
  color: #ff7878;
  padding: 8px 12px;
  background: rgba(255,80,80,0.08);
  border: 1px solid rgba(255,80,80,0.2);
  border-radius: 6px;
}

.auth-btn {
  padding: 12px;
  background: linear-gradient(135deg, #c9a44a, #e6b85a);
  border: none;
  border-radius: 8px;
  color: #120f1a;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  font-family: 'Noto Serif SC', serif;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.auth-btn:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 4px 16px rgba(201,164,74,0.3);
}

.auth-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.auth-spinner {
  width: 16px; height: 16px;
  border: 2px solid rgba(0,0,0,0.2);
  border-top-color: #120f1a;
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
}

@keyframes spin { to { transform: rotate(360deg); } }

.auth-toggle {
  margin-top: 16px;
  font-size: 13px;
  color: #6a6070;
}

.toggle-btn {
  background: none;
  border: none;
  color: #c9a44a;
  cursor: pointer;
  font-family: 'Noto Serif SC', serif;
  font-size: 13px;
  padding: 0;
  margin-left: 4px;
}

.toggle-btn:hover {
  color: #ffd700;
}

.skip-btn {
  margin-top: 12px;
  background: none;
  border: none;
  color: #4a4060;
  font-size: 12px;
  cursor: pointer;
  font-family: 'Noto Serif SC', serif;
  transition: color 0.2s;
}

.skip-btn:hover {
  color: #8a7090;
}
</style>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useI18n } from '../composables/useI18n'
import LoginModal from '../components/LoginModal.vue'

const emit = defineEmits<{
  start: []
  load: []
}>()

const { t, lang, toggleLang } = useI18n()
const showMenu = ref(true)
const showLogin = ref(false)
const loginRedirect = ref(false) // 登录后是否自动开始游戏
const currentUser = ref<{ token: string; user_id: number; username: string; nickname: string } | null>(null)

onMounted(() => {
  const saved = localStorage.getItem('mh_user')
  if (saved) {
    try { currentUser.value = JSON.parse(saved) } catch {}
  }
})

const handleLogin = (user: { token: string; user_id: number; username: string; nickname: string }) => {
  currentUser.value = user
  showLogin.value = false
  if (loginRedirect.value) {
    loginRedirect.value = false
    emit('start')
  }
}

const handleLogout = () => {
  localStorage.removeItem('mh_token')
  localStorage.removeItem('mh_user')
  currentUser.value = null
}

const handleStart = () => {
  if (!currentUser.value) {
    loginRedirect.value = true
    showLogin.value = true
    return
  }
  emit('start')
}

const handleLoad = () => {
  if (!currentUser.value) {
    loginRedirect.value = false
    showLogin.value = true
    return
  }
  emit('load')
}
</script>

<template>
  <div class="home" role="main" aria-label="游戏首页">
    <div class="particles">
      <div v-for="i in 20" :key="i" class="particle" :style="{
        left: Math.random() * 100 + '%',
        animationDelay: Math.random() * 5 + 's',
        animationDuration: (3 + Math.random() * 4) + 's',
      }" />
    </div>

    <div class="content">
      <div class="logo-area">
        <div class="logo-icon">
          <svg width="64" height="64" viewBox="0 0 64 64" fill="none">
            <circle cx="32" cy="28" r="20" stroke="rgba(100,180,255,0.4)" stroke-width="1.5" fill="none" />
            <circle cx="32" cy="28" r="12" stroke="rgba(100,150,255,0.3)" stroke-width="1" fill="none" />
            <circle cx="32" cy="28" r="4" fill="rgba(100,180,255,0.5)" />
            <path d="M26 48 Q32 56 38 48" stroke="rgba(100,180,255,0.4)" stroke-width="1.5" fill="none" stroke-linecap="round" />
            <circle cx="24" cy="22" r="2" fill="rgba(232,180,80,0.4)" />
            <circle cx="40" cy="22" r="2" fill="rgba(100,200,150,0.4)" />
            <circle cx="32" cy="18" r="1.5" fill="rgba(200,150,255,0.4)" />
          </svg>
        </div>
        <h1 class="title">拾 忆</h1>
        <p class="subtitle">Memory Healer</p>
        <div class="divider" />
        <p class="desc">进入记忆碎片，找回遗失的故事</p>
      </div>

      <div class="menu" v-if="showMenu">
        <button class="btn btn-primary" @click="handleStart" aria-label="开始新的记忆修复之旅">
          <svg class="btn-icon" width="18" height="18" viewBox="0 0 18 18" fill="none">
            <polygon points="4,2 16,9 4,16" fill="currentColor" />
          </svg>
          开始新的记忆修复
        </button>
        <button class="btn btn-secondary" @click="handleLoad" aria-label="读取之前的存档">
          <svg class="btn-icon" width="18" height="18" viewBox="0 0 18 18" fill="none">
            <rect x="2" y="4" width="14" height="10" rx="2" stroke="currentColor" stroke-width="1.5" fill="none" />
            <path d="M2 7h14" stroke="currentColor" stroke-width="1" opacity="0.5" />
            <rect x="4" y="9" width="4" height="2" rx="0.5" fill="currentColor" opacity="0.6" />
          </svg>
          读取存档
        </button>

        <div class="menu-divider" />

        <template v-if="currentUser">
          <div class="user-info">
            <svg class="user-icon" width="16" height="16" viewBox="0 0 16 16" fill="none">
              <circle cx="8" cy="6" r="3" stroke="currentColor" stroke-width="1.2" fill="none" />
              <path d="M2 14c0-3.3 2.7-5 6-5s6 1.7 6 5" stroke="currentColor" stroke-width="1.2" fill="none" stroke-linecap="round" />
            </svg>
            <span class="user-name">{{ currentUser.nickname || currentUser.username }}</span>
            <button class="btn-logout" @click="handleLogout" title="退出登录">退出</button>
          </div>
        </template>
        <template v-else>
          <button class="btn btn-login" @click="loginRedirect = false; showLogin = true">
            <svg class="btn-icon" width="18" height="18" viewBox="0 0 18 18" fill="none">
              <rect x="3" y="8" width="12" height="8" rx="2" stroke="currentColor" stroke-width="1.3" fill="none" />
              <circle cx="9" cy="5" r="3" stroke="currentColor" stroke-width="1.3" fill="none" />
              <circle cx="9" cy="5" r="1" fill="currentColor" opacity="0.5" />
            </svg>
            登录 / 注册
          </button>
        </template>
      </div>

      <div class="footer" role="contentinfo">
        <p>腾讯云黑客松 · AI叙事游戏</p>
        <p class="tech">Powered by DeepSeek · Vue 3 · FastAPI</p>
      </div>
    </div>

    <LoginModal v-if="showLogin" @login="handleLogin" @close="showLogin = false" />
  </div>
</template>
<style scoped>
.home {
  width: 100vw;
  height: 100vh;
  background: linear-gradient(135deg, #0a0a1a 0%, #1a1a3e 50%, #0d0d2b 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  overflow: hidden;
  font-family: 'Noto Serif SC', serif;
}

.particles {
  position: absolute;
  inset: 0;
  pointer-events: none;
}

.particle {
  position: absolute;
  width: 4px;
  height: 4px;
  background: rgba(100, 180, 255, 0.6);
  border-radius: 50%;
  bottom: -10px;
  animation: float linear infinite;
}

@keyframes float {
  0% { transform: translateY(0) scale(1); opacity: 0; }
  10% { opacity: 1; }
  90% { opacity: 1; }
  100% { transform: translateY(-100vh) scale(0); opacity: 0; }
}

.content {
  text-align: center;
  z-index: 1;
}

.logo-icon {
  margin-bottom: 16px;
  animation: pulse 3s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.08); }
}

.title {
  font-size: 56px;
  color: #e0e0ff;
  letter-spacing: 16px;
  margin: 0;
  text-shadow: 0 0 30px rgba(100, 150, 255, 0.5);
}

.subtitle {
  font-size: 14px;
  color: rgba(150, 180, 255, 0.6);
  letter-spacing: 8px;
  text-transform: uppercase;
  margin: 8px 0 24px;
}

.divider {
  width: 60px;
  height: 1px;
  background: linear-gradient(90deg, transparent, rgba(100, 150, 255, 0.5), transparent);
  margin: 0 auto 20px;
}

.desc {
  color: rgba(200, 210, 255, 0.7);
  font-size: 16px;
  margin-bottom: 48px;
}

/* ── 按钮组 ── */
.menu {
  display: flex;
  flex-direction: column;
  gap: 14px;
  align-items: center;
}

.btn {
  padding: 14px 40px;
  border: none;
  border-radius: 8px;
  font-size: 16px;
  font-family: 'Noto Serif SC', serif;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 10px;
  transition: all 0.3s ease;
  min-width: 260px;
  justify-content: center;
}

.btn-icon {
  flex-shrink: 0;
}

.btn-primary {
  background: linear-gradient(135deg, #3a5fcd, #5078e0);
  color: white;
  box-shadow: 0 4px 20px rgba(58, 95, 205, 0.4);
}
.btn-primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 30px rgba(58, 95, 205, 0.6);
}

.btn-secondary {
  background: rgba(255, 255, 255, 0.06);
  color: rgba(200, 210, 255, 0.75);
  border: 1px solid rgba(100, 150, 255, 0.15);
}
.btn-secondary:hover {
  background: rgba(255, 255, 255, 0.1);
  border-color: rgba(100, 150, 255, 0.35);
  transform: translateY(-1px);
}

.btn-login {
  background: rgba(255, 255, 255, 0.04);
  color: rgba(200, 210, 255, 0.5);
  border: 1px solid rgba(100, 150, 255, 0.1);
  padding: 12px 36px;
  font-size: 15px;
  min-width: 240px;
}
.btn-login:hover {
  background: rgba(255, 255, 255, 0.08);
  border-color: rgba(100, 150, 255, 0.3);
  color: rgba(200, 210, 255, 0.8);
  transform: translateY(-1px);
}

/* ── 菜单分隔线 ── */
.menu-divider {
  width: 40px;
  height: 1px;
  background: rgba(100, 150, 255, 0.12);
  margin: 4px 0;
}

/* ── 用户信息条 ── */
.user-info {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 8px 18px;
  border-radius: 20px;
  background: rgba(100, 150, 255, 0.06);
  border: 1px solid rgba(100, 150, 255, 0.1);
  color: rgba(200, 210, 255, 0.7);
  font-size: 14px;
}
.user-icon {
  flex-shrink: 0;
  color: rgba(100, 180, 255, 0.5);
}
.user-name {
  color: rgba(200, 210, 255, 0.85);
}
.btn-logout {
  background: none;
  border: none;
  color: rgba(150, 170, 220, 0.4);
  font-size: 12px;
  cursor: pointer;
  font-family: 'Noto Serif SC', serif;
  padding: 2px 10px;
  border-radius: 4px;
  transition: all 0.2s;
}
.btn-logout:hover {
  color: rgba(255, 120, 120, 0.8);
  background: rgba(255, 80, 80, 0.1);
}

/* ── 页脚 ── */
.footer {
  margin-top: 56px;
  color: rgba(150, 170, 220, 0.35);
  font-size: 13px;
}
.tech {
  font-size: 11px;
  margin-top: 4px;
  opacity: 0.7;
}
</style>

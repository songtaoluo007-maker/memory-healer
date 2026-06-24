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
const currentUser = ref<{ token: string; user_id: number; username: string; nickname: string } | null>(null)

onMounted(() => {
  // 检查本地存储的登录状态
  const saved = localStorage.getItem('mh_user')
  if (saved) {
    try {
      currentUser.value = JSON.parse(saved)
    } catch {}
  }
})

const handleLogin = (user: { token: string; user_id: number; username: string; nickname: string }) => {
  currentUser.value = user
  showLogin.value = false
}

const handleLogout = () => {
  localStorage.removeItem('mh_token')
  localStorage.removeItem('mh_user')
  currentUser.value = null
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
        <div class="logo-icon">🧠</div>
        <h1 class="title">拾 忆</h1>
        <p class="subtitle">Memory Healer</p>
        <div class="divider" />
        <p class="desc">进入记忆碎片，找回遗失的故事</p>
      </div>

      <div class="menu" v-if="showMenu">
        <button class="btn btn-primary" @click="emit('start')" aria-label="开始新的记忆修复之旅">
          <span class="btn-icon">▶</span>
          开始新的记忆修复
        </button>
        <button class="btn btn-secondary" @click="emit('load')" aria-label="读取之前的存档">
          <span class="btn-icon">📂</span>
          读取存档
        </button>
      </div>

      <!-- 用户状态 -->
      <div class="user-section">
        <template v-if="currentUser">
          <div class="user-info">
            <span class="user-avatar">?</span>
            <span class="user-name">{{ currentUser.nickname || currentUser.username }}</span>
            <button class="btn-logout" @click="handleLogout" title="退出登录">退出</button>
          </div>
        </template>
        <template v-else>
          <button class="btn btn-login" @click="showLogin = true">
            <span class="btn-icon">?</span>
            登录 / 注册
          </button>
        </template>
      </div>

      <div class="footer" role="contentinfo">
        <p>腾讯云黑客松 · AI叙事游戏</p>
        <p class="tech">Powered by DeepSeek · Vue 3 · FastAPI</p>
        <p class="version">v1.0.0 · P18</p>
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
  font-size: 64px;
  margin-bottom: 16px;
  animation: pulse 3s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.1); }
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

.menu {
  display: flex;
  flex-direction: column;
  gap: 16px;
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
  transition: all 0.3s;
  min-width: 260px;
  justify-content: center;
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
  background: rgba(255, 255, 255, 0.08);
  color: rgba(200, 210, 255, 0.8);
  border: 1px solid rgba(100, 150, 255, 0.2);
}

.btn-secondary:hover {
  background: rgba(255, 255, 255, 0.12);
  border-color: rgba(100, 150, 255, 0.4);
}

.btn-icon {
  font-size: 18px;
}

.footer {
  margin-top: 60px;
  color: rgba(150, 170, 220, 0.4);
  font-size: 13px;
}

.tech {
  font-size: 11px;
  margin-top: 4px;
}

.version {
  font-size: 10px;
  margin-top: 8px;
  opacity: 0.3;
}

.btn-login {
  background: rgba(255, 255, 255, 0.04);
  color: rgba(200, 210, 255, 0.5);
  border: 1px solid rgba(100, 150, 255, 0.12);
  padding: 10px 32px;
  font-size: 14px;
  min-width: 200px;
}
.btn-login:hover {
  background: rgba(255, 255, 255, 0.08);
  border-color: rgba(100, 150, 255, 0.3);
  color: rgba(200, 210, 255, 0.8);
  transform: translateY(-1px);
}

.user-section {
  margin-top: 20px;
}

.user-info {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  padding: 8px 20px;
  border-radius: 20px;
  background: rgba(100, 150, 255, 0.06);
  border: 1px solid rgba(100, 150, 255, 0.1);
  font-size: 14px;
}
.user-avatar {
  font-size: 18px;
}
.user-info .user-name {
  color: rgba(200, 210, 255, 0.8);
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
</style>

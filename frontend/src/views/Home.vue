<script setup lang="ts">
import { onMounted, ref } from 'vue'
import LoginModal from '../components/LoginModal.vue'
import homeBackdrop from '../assets/cinematic/scene-1972-xian-alley.png'
import type { AuthUser } from '../types/game'

const emit = defineEmits<{
  start: []
  load: []
}>()

const showLogin = ref(false)
const currentUser = ref<AuthUser | null>(null)

onMounted(async () => {
  const saved = localStorage.getItem('mh_user')
  if (!saved) return

  try {
    currentUser.value = JSON.parse(saved)
  } catch {
    localStorage.removeItem('mh_user')
    return
  }

  try {
    const response = await fetch('/api/auth/me', { credentials: 'include' })
    if (!response.ok) throw new Error('session unavailable')
    const user = (await response.json()) as AuthUser
    currentUser.value = user
    localStorage.setItem('mh_user', JSON.stringify(user))
  } catch {
    currentUser.value = null
    localStorage.removeItem('mh_user')
  }
})

const handleLogin = (user: AuthUser) => {
  currentUser.value = user
  showLogin.value = false
}

const handleLogout = async () => {
  try {
    await fetch('/api/auth/logout', {
      method: 'POST',
      credentials: 'include',
    })
  } finally {
    localStorage.removeItem('mh_user')
    currentUser.value = null
  }
}

const handleStart = () => {
  emit('start')
}

const handleLoad = () => {
  if (!currentUser.value) {
    showLogin.value = true
    return
  }
  emit('load')
}

const openLogin = () => {
  showLogin.value = true
}
</script>

<template>
  <div class="home cinematic-home" role="main" aria-label="游戏首页">
    <img class="home-backdrop" :src="homeBackdrop" alt="" aria-hidden="true" />
    <div class="home-grade" aria-hidden="true" />
    <div class="home-grain" aria-hidden="true" />

    <header class="home-header">
      <div class="home-brand">
        <span>拾</span>
        <div><strong>拾忆</strong><small>MEMORY HEALER</small></div>
      </div>
      <div class="release-index">
        <span>MEMORY ARCHIVE / 001</span>
        <i />
        <span>西安 · 1972</span>
      </div>
    </header>

    <section class="hero-copy" aria-labelledby="home-title">
      <span class="hero-kicker">一场关于记忆、传承与选择的叙事电影</span>
      <h1 id="home-title" class="title"><span>拾</span><span>忆</span></h1>
      <p class="subtitle">MEMORY HEALER</p>
      <p class="desc">进入一个人的一生，拾回被时间遗落的声音。</p>
    </section>

    <section class="menu" aria-label="开始菜单">
      <span class="menu-kicker">ENTER THE MEMORY</span>
      <button class="btn btn-primary" @click="handleStart" aria-label="开始新的记忆修复之旅">
        <span class="action-index">01</span>
        <span>开始新的记忆修复</span>
        <span aria-hidden="true">→</span>
      </button>
      <button class="btn btn-secondary" @click="handleLoad" aria-label="读取之前的存档">
        <span class="action-index">02</span>
        <span>读取记忆存档</span>
        <span aria-hidden="true">→</span>
      </button>

      <div class="account-row">
        <template v-if="currentUser">
          <div class="user-info">
            <span class="account-state">已连接</span>
            <strong>{{ currentUser.nickname || currentUser.username }}</strong>
          </div>
          <button class="text-action" @click="handleLogout">退出</button>
        </template>
        <template v-else>
          <span>跨设备保存进度</span>
          <button class="text-action" @click="openLogin">登录 / 注册</button>
        </template>
      </div>
    </section>

    <footer class="footer" role="contentinfo">
      <span>DEEPSEEK × EDGE TTS</span>
      <span class="footer-line" />
      <span>AN INTERACTIVE MEMORY FILM</span>
    </footer>

    <LoginModal v-if="showLogin" @login="handleLogin" @close="showLogin = false" />
  </div>
</template>

<style scoped>
.cinematic-home {
  position: relative;
  width: 100vw;
  height: 100vh;
  overflow: hidden;
  color: var(--paper-100);
  background: #050606;
}

.home-backdrop,
.home-grade,
.home-grain {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
}

.home-backdrop {
  object-fit: cover;
  object-position: 54% center;
  filter: saturate(0.78) contrast(1.06);
  animation: home-camera 24s ease-out both;
}

.home-grade {
  background:
    linear-gradient(
      90deg,
      rgba(3, 4, 3, 0.92) 0%,
      rgba(3, 4, 3, 0.46) 43%,
      rgba(3, 4, 3, 0.2) 68%,
      rgba(3, 4, 3, 0.62)
    ),
    linear-gradient(180deg, rgba(3, 4, 3, 0.54), transparent 28%, rgba(3, 4, 3, 0.82));
}

.home-grain {
  opacity: 0.04;
  background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 180 180' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='.85' numOctaves='3'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E");
  pointer-events: none;
}

.home-header {
  position: absolute;
  z-index: 2;
  top: 0;
  right: 0;
  left: 0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: max(1.5rem, env(safe-area-inset-top)) var(--safe-inline);
}

.home-brand {
  display: flex;
  gap: 0.65rem;
  align-items: center;
}

.home-brand > span {
  display: grid;
  width: 2.15rem;
  height: 2.15rem;
  place-items: center;
  border: 1px solid rgba(214, 173, 102, 0.68);
  color: var(--gold-300);
}

.home-brand div {
  display: flex;
  flex-direction: column;
}

.home-brand strong {
  font-size: 0.78rem;
  font-weight: 500;
  letter-spacing: 0.3em;
}

.home-brand small,
.release-index,
.hero-kicker,
.menu-kicker,
.footer {
  color: rgba(215, 196, 162, 0.52);
  font:
    500 0.5rem/1.2 ui-monospace,
    monospace;
  letter-spacing: 0.2em;
}

.release-index {
  display: flex;
  align-items: center;
  gap: 0.8rem;
}

.release-index i {
  width: 3rem;
  height: 1px;
  background: rgba(214, 173, 102, 0.35);
}

.hero-copy {
  position: absolute;
  z-index: 2;
  top: 50%;
  left: var(--safe-inline);
  width: min(35rem, 46vw);
  transform: translateY(-48%);
}

.hero-kicker {
  display: block;
  color: var(--gold-300);
}

.title {
  display: flex;
  gap: clamp(1rem, 2.6vw, 2.8rem);
  margin: 1.3rem 0 0;
  font-size: clamp(5rem, 10vw, 9rem);
  font-weight: 400;
  line-height: 0.95;
  letter-spacing: 0.02em;
  text-shadow: 0 1rem 3rem rgba(0, 0, 0, 0.55);
}

.title span:last-child {
  transform: translateY(1.25rem);
}

.subtitle {
  margin: 1.5rem 0 0;
  color: rgba(241, 229, 206, 0.62);
  font:
    500 clamp(0.58rem, 0.8vw, 0.75rem)/1 ui-monospace,
    monospace;
  letter-spacing: 0.65em;
}

.desc {
  width: fit-content;
  margin: 2.2rem 0 0;
  padding-top: 1rem;
  border-top: 1px solid rgba(214, 173, 102, 0.38);
  color: rgba(241, 229, 206, 0.72);
  font-size: clamp(0.8rem, 1vw, 0.95rem);
  letter-spacing: 0.12em;
}

.menu {
  position: absolute;
  z-index: 3;
  right: var(--safe-inline);
  bottom: clamp(5rem, 11vh, 8rem);
  display: flex;
  width: min(27rem, 34vw);
  flex-direction: column;
  gap: 0.45rem;
}

.menu-kicker {
  margin-bottom: 0.4rem;
  color: var(--gold-300);
  text-align: right;
}

.btn {
  display: grid;
  grid-template-columns: 2rem 1fr auto;
  gap: 0.9rem;
  align-items: center;
  min-height: 3.65rem;
  padding: 0 1.1rem;
  border: 1px solid rgba(215, 196, 162, 0.17);
  color: rgba(241, 229, 206, 0.78);
  text-align: left;
  background: rgba(5, 6, 6, 0.62);
  backdrop-filter: blur(14px);
  cursor: pointer;
  transition:
    transform 220ms var(--ease-cinema),
    border-color 180ms ease,
    background 180ms ease;
}

.btn:hover {
  border-color: rgba(214, 173, 102, 0.68);
  transform: translateX(-0.5rem);
}

.btn-primary {
  border-color: rgba(214, 173, 102, 0.5);
  color: var(--paper-100);
  background:
    linear-gradient(90deg, rgba(166, 109, 44, 0.26), transparent 45%), rgba(8, 8, 7, 0.74);
}

.action-index {
  color: var(--gold-300);
  font:
    500 0.62rem/1 ui-monospace,
    monospace;
}

.account-row {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  min-height: 2.9rem;
  gap: 1rem;
  padding: 0 0.3rem;
  color: rgba(215, 196, 162, 0.48);
  font-size: 0.68rem;
}

.text-action {
  padding: 0.3rem 0;
  border: 0;
  border-bottom: 1px solid rgba(214, 173, 102, 0.45);
  color: var(--gold-300);
  background: transparent;
  cursor: pointer;
}

.user-info {
  display: flex;
  gap: 0.6rem;
  align-items: center;
}

.account-state {
  color: rgba(151, 181, 133, 0.7);
}

.user-info strong {
  color: var(--paper-300);
  font-weight: 500;
}

.footer {
  position: absolute;
  z-index: 2;
  right: var(--safe-inline);
  bottom: max(1.45rem, env(safe-area-inset-bottom));
  left: var(--safe-inline);
  display: flex;
  align-items: center;
  gap: 0.8rem;
}

.footer-line {
  width: 2.5rem;
  height: 1px;
  background: rgba(215, 196, 162, 0.25);
}

@keyframes home-camera {
  from {
    transform: scale(1.04);
  }
  to {
    transform: scale(1.1) translateX(-0.7%);
  }
}

@media (max-width: 820px), (max-aspect-ratio: 4/5) {
  .home-backdrop {
    object-position: 38% center;
  }

  .home-grade {
    background:
      linear-gradient(180deg, rgba(3, 4, 3, 0.55), rgba(3, 4, 3, 0.2) 32%, rgba(3, 4, 3, 0.94) 72%),
      linear-gradient(90deg, rgba(3, 4, 3, 0.6), transparent);
  }

  .home-header {
    padding-right: 1rem;
    padding-left: 1rem;
  }

  .release-index {
    display: none;
  }

  .hero-copy {
    top: 14vh;
    left: 1.25rem;
    width: calc(100vw - 2.5rem);
    transform: none;
  }

  .hero-kicker {
    font-size: 0.46rem;
  }

  .title {
    font-size: clamp(4.5rem, 23vw, 7rem);
  }

  .desc {
    margin-top: 1.6rem;
  }

  .menu {
    right: 1rem;
    bottom: max(4.2rem, calc(env(safe-area-inset-bottom) + 3.5rem));
    left: 1rem;
    width: auto;
  }

  .footer {
    right: 1rem;
    bottom: max(1rem, env(safe-area-inset-bottom));
    left: 1rem;
    justify-content: center;
  }

  .footer span:last-child {
    display: none;
  }
}

@media (prefers-reduced-motion: reduce) {
  .home-backdrop {
    animation: none;
  }
}
</style>

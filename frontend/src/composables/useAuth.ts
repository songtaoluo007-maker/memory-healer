/**
 * 认证系统 — 登录/注册/JWT管理
 */
import { ref, computed } from 'vue'
import * as api from '../api'

interface User {
  id: number
  username: string
  nickname: string
  avatar_url?: string
  created_at: string
  last_login?: string
}

const currentUser = ref<User | null>(null)
const token = ref<string>(null)
const loading = ref(false)
const error = ref('')

// 从localStorage恢复
const saved = localStorage.getItem('mh_auth')
if (saved) {
  try {
    const data = JSON.parse(saved)
    token.value = data.token
    currentUser.value = data.user
  } catch {}
}

export function useAuth() {
  const isLoggedIn = computed(() => !!token.value && !!currentUser.value)

  function saveAuth(t: string, u: User) {
    token.value = t
    currentUser.value = u
    localStorage.setItem('mh_auth', JSON.stringify({ token: t, user: u }))
  }

  function clearAuth() {
    token.value = null
    currentUser.value = null
    localStorage.removeItem('mh_auth')
  }

  async function register(username: string, password: string, nickname?: string) {
    loading.value = true
    error.value = ''
    try {
      const res = await api.register(username, password, nickname)
      if (res.data.success) {
        saveAuth(res.data.token, res.data.user)
        return true
      }
      error.value = '注册失败'
      return false
    } catch (e: any) {
      error.value = e.response?.data?.detail || '注册失败'
      return false
    } finally {
      loading.value = false
    }
  }

  async function login(username: string, password: string) {
    loading.value = true
    error.value = ''
    try {
      const res = await api.login(username, password)
      if (res.data.success) {
        saveAuth(res.data.token, res.data.user)
        return true
      }
      error.value = '登录失败'
      return false
    } catch (e: any) {
      error.value = e.response?.data?.detail || '用户名或密码错误'
      return false
    } finally {
      loading.value = false
    }
  }

  function logout() {
    clearAuth()
  }

  async function fetchMe() {
    if (!token.value) return
    try {
      const res = await api.getMe()
      currentUser.value = res.data.user
      localStorage.setItem('mh_auth', JSON.stringify({ token: token.value, user: currentUser.value }))
    } catch {
      clearAuth()
    }
  }

  return {
    currentUser,
    token,
    isLoggedIn,
    loading,
    error,
    register,
    login,
    logout,
    fetchMe,
  }
}

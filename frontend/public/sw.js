/**
 * 拾忆 Service Worker - PWA离线支持
 * 缓存策略: Network First + Cache Fallback
 */

const CACHE_NAME = 'memory-healer-v1'
const STATIC_ASSETS = [
  '/',
  '/index.html',
  '/manifest.json',
  '/icons/icon-192.png',
  '/icons/icon-512.png',
]

// 安装事件 - 预缓存静态资源
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(STATIC_ASSETS)
    })
  )
  self.skipWaiting()
})

// 激活事件 - 清理旧缓存
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames
          .filter((name) => name !== CACHE_NAME)
          .map((name) => caches.delete(name))
      )
    })
  )
  self.clients.claim()
})

// 请求拦截 - Network First策略
self.addEventListener('fetch', (event) => {
  const { request } = event
  const url = new URL(request.url)

  // 跳过非GET请求
  if (request.method !== 'GET') return

  // 跳过API请求（需要实时数据）
  if (url.pathname.startsWith('/api/')) return

  // 跳过开发服务器的HMR请求
  if (url.pathname.includes('/__vite') || url.pathname.includes('/@vite')) return

  event.respondWith(
    fetch(request)
      .then((response) => {
        // 成功获取则更新缓存
        if (response && response.status === 200) {
          const responseClone = response.clone()
          caches.open(CACHE_NAME).then((cache) => {
            cache.put(request, responseClone)
          })
        }
        return response
      })
      .catch(() => {
        // 网络失败则从缓存读取
        return caches.match(request).then((cachedResponse) => {
          if (cachedResponse) {
            return cachedResponse
          }
          // 如果是导航请求，返回缓存的首页
          if (request.mode === 'navigate') {
            return caches.match('/index.html')
          }
          return new Response('离线状态，请检查网络连接', {
            status: 503,
            statusText: 'Service Unavailable',
          })
        })
      })
  )
})

// 推送通知（预留）
self.addEventListener('push', (event) => {
  if (event.data) {
    const data = event.data.json()
    event.waitUntil(
      self.registration.showNotification(data.title, {
        body: data.body,
        icon: '/icons/icon-192.png',
        badge: '/icons/icon-192.png',
      })
    )
  }
})

// 通知点击
self.addEventListener('notificationclick', (event) => {
  event.notification.close()
  event.waitUntil(
    self.clients.openWindow('/')
  )
})

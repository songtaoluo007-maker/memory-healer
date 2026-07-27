import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import { router } from './router'
import { syncServiceWorker } from './serviceWorker'
import './styles/cinematic.css'

createApp(App).use(createPinia()).use(router).mount('#app')

window.addEventListener('load', () => {
  void syncServiceWorker(import.meta.env.PROD).catch((error: unknown) => {
    console.warn('[拾忆] Service Worker 同步失败', error)
  })
})

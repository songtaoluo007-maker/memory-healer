import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'

export const routes: RouteRecordRaw[] = [
  {
    path: '/',
    name: 'home',
    component: () => import('../views/Home.vue'),
  },
  {
    path: '/prologue',
    name: 'prologue',
    component: () => import('../views/Intro.vue'),
  },
  {
    path: '/tutorial',
    name: 'tutorial',
    component: () => import('../components/GameTutorial.vue'),
  },
  {
    path: '/memory',
    name: 'memory',
    component: () => import('../views/Game.vue'),
  },
  {
    path: '/saves',
    name: 'saves',
    component: () => import('../views/Saves.vue'),
  },
  {
    path: '/ending/:type',
    name: 'ending',
    component: () => import('../views/Ending.vue'),
    props: true,
  },
]

export const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior: () => ({ top: 0 }),
})

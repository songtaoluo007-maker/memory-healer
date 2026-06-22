/**
 * Web Vitals 性能监控
 * 采集 LCP/FID/CLS/FCP/TTFB 指标
 */

import { onMounted } from 'vue'

interface VitalMetric {
  name: string
  value: number
  rating: 'good' | 'needs-improvement' | 'poor'
  timestamp: number
}

// 性能指标存储
const metrics: VitalMetric[] = []

// 指标阈值 (ms)
const THRESHOLDS = {
  LCP: { good: 2500, poor: 4000 },
  FID: { good: 100, poor: 300 },
  CLS: { good: 0.1, poor: 0.25 },
  FCP: { good: 1800, poor: 3000 },
  TTFB: { good: 800, poor: 1800 },
}

function getRating(name: string, value: number): 'good' | 'needs-improvement' | 'poor' {
  const threshold = THRESHOLDS[name as keyof typeof THRESHOLDS]
  if (!threshold) return 'good'
  if (value <= threshold.good) return 'good'
  if (value <= threshold.poor) return 'needs-improvement'
  return 'poor'
}

function sendToAnalytics(metric: VitalMetric) {
  metrics.push(metric)
  
  // 开发环境打印
  if (import.meta.env.DEV) {
    const emoji = metric.rating === 'good' ? '✅' : metric.rating === 'needs-improvement' ? '⚠️' : '❌'
    console.log(`[拾忆性能] ${emoji} ${metric.name}: ${metric.value.toFixed(2)} (${metric.rating})`)
  }
  
  // 生产环境可发送到后端
  // fetch('/api/analytics/vitals', {
  //   method: 'POST',
  //   headers: { 'Content-Type': 'application/json' },
  //   body: JSON.stringify(metric),
  // }).catch(() => {})
}

export function useWebVitals() {
  onMounted(async () => {
    try {
      const { onLCP, onFID, onCLS, onFCP, onTTFB } = await import('web-vitals')
      
      onLCP((metric) => {
        sendToAnalytics({
          name: 'LCP',
          value: metric.value,
          rating: getRating('LCP', metric.value),
          timestamp: Date.now(),
        })
      })
      
      onFID((metric) => {
        sendToAnalytics({
          name: 'FID',
          value: metric.value,
          rating: getRating('FID', metric.value),
          timestamp: Date.now(),
        })
      })
      
      onCLS((metric) => {
        sendToAnalytics({
          name: 'CLS',
          value: metric.value,
          rating: getRating('CLS', metric.value),
          timestamp: Date.now(),
        })
      })
      
      onFCP((metric) => {
        sendToAnalytics({
          name: 'FCP',
          value: metric.value,
          rating: getRating('FCP', metric.value),
          timestamp: Date.now(),
        })
      })
      
      onTTFB((metric) => {
        sendToAnalytics({
          name: 'TTFB',
          value: metric.value,
          rating: getRating('TTFB', metric.value),
          timestamp: Date.now(),
        })
      })
    } catch (err) {
      console.warn('[拾忆性能] Web Vitals 加载失败:', err)
    }
  })
  
  return {
    getMetrics: () => [...metrics],
    getMetricByName: (name: string) => metrics.filter((m) => m.name === name),
    clearMetrics: () => metrics.length = 0,
  }
}

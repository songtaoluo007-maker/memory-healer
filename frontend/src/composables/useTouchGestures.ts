/**
 * 触摸手势支持
 * 滑动切换场景、长按查看详情
 */

import { ref, onMounted, onUnmounted } from 'vue'

interface TouchOptions {
  onSwipeLeft?: () => void
  onSwipeRight?: () => void
  onSwipeUp?: () => void
  onSwipeDown?: () => void
  onLongPress?: () => void
  threshold?: number
  longPressTime?: number
}

export function useTouchGestures(options: TouchOptions = {}) {
  const {
    onSwipeLeft,
    onSwipeRight,
    onSwipeUp,
    onSwipeDown,
    onLongPress,
    threshold = 50,
    longPressTime = 500,
  } = options

  const isSwiping = ref(false)
  const startX = ref(0)
  const startY = ref(0)
  let longPressTimer: ReturnType<typeof setTimeout> | null = null

  const handleTouchStart = (e: TouchEvent) => {
    const touch = e.touches[0]
    startX.value = touch.clientX
    startY.value = touch.clientY
    isSwiping.value = true

    // 长按检测
    if (onLongPress) {
      longPressTimer = setTimeout(() => {
        onLongPress()
        isSwiping.value = false
      }, longPressTime)
    }
  }

  const handleTouchMove = (e: TouchEvent) => {
    if (!isSwiping.value) return

    // 移动超过阈值取消长按
    if (longPressTimer) {
      const touch = e.touches[0]
      const deltaX = Math.abs(touch.clientX - startX.value)
      const deltaY = Math.abs(touch.clientY - startY.value)
      if (deltaX > 10 || deltaY > 10) {
        clearTimeout(longPressTimer)
        longPressTimer = null
      }
    }
  }

  const handleTouchEnd = (e: TouchEvent) => {
    if (!isSwiping.value) return
    isSwiping.value = false

    // 清除长按计时器
    if (longPressTimer) {
      clearTimeout(longPressTimer)
      longPressTimer = null
    }

    const touch = e.changedTouches[0]
    const deltaX = touch.clientX - startX.value
    const deltaY = touch.clientY - startY.value
    const absDeltaX = Math.abs(deltaX)
    const absDeltaY = Math.abs(deltaY)

    // 判断滑动方向
    if (absDeltaX > threshold || absDeltaY > threshold) {
      if (absDeltaX > absDeltaY) {
        // 水平滑动
        if (deltaX > 0 && onSwipeRight) {
          onSwipeRight()
        } else if (deltaX < 0 && onSwipeLeft) {
          onSwipeLeft()
        }
      } else {
        // 垂直滑动
        if (deltaY > 0 && onSwipeDown) {
          onSwipeDown()
        } else if (deltaY < 0 && onSwipeUp) {
          onSwipeUp()
        }
      }
    }
  }

  onMounted(() => {
    document.addEventListener('touchstart', handleTouchStart, { passive: true })
    document.addEventListener('touchmove', handleTouchMove, { passive: true })
    document.addEventListener('touchend', handleTouchEnd, { passive: true })
  })

  onUnmounted(() => {
    document.removeEventListener('touchstart', handleTouchStart)
    document.removeEventListener('touchmove', handleTouchMove)
    document.removeEventListener('touchend', handleTouchEnd)
    if (longPressTimer) {
      clearTimeout(longPressTimer)
    }
  })

  return {
    isSwiping,
  }
}

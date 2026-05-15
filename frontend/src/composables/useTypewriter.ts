import { ref, onUnmounted } from 'vue'

export function useTypewriter(speed = 30) {
  const displayText = ref('')
  const isTyping = ref(false)
  let timer: ReturnType<typeof setTimeout> | null = null
  let currentIndex = 0
  let fullText = ''

  const start = (text: string, onComplete?: () => void) => {
    stop()
    fullText = text
    currentIndex = 0
    displayText.value = ''
    isTyping.value = true

    const tick = () => {
      if (currentIndex < fullText.length) {
        displayText.value += fullText[currentIndex]
        currentIndex++
        timer = setTimeout(tick, speed)
      } else {
        isTyping.value = false
        onComplete?.()
      }
    }
    tick()
  }

  const stop = () => {
    if (timer) {
      clearTimeout(timer)
      timer = null
    }
    isTyping.value = false
  }

  const skip = () => {
    stop()
    displayText.value = fullText
  }

  onUnmounted(stop)

  return { displayText, isTyping, start, stop, skip }
}

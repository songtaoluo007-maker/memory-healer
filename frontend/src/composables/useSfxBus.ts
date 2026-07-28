import { getCurrentInstance, onUnmounted, watch } from 'vue'
import { getAudioContext } from '../audio/context'
import { type AudioMixer, useAudioMixer } from '../audio/mixer'

interface ActiveTone {
  oscillator: OscillatorNode
  gain: GainNode
}

export function useSfxBus(mixer: AudioMixer = useAudioMixer()) {
  let context: AudioContext | null = null
  let outputGain: GainNode | null = null
  const delayedTimers = new Set<number>()
  const activeTones = new Set<ActiveTone>()

  const outputTarget = () => mixer.effectiveSfxVolume.value * 0.3

  const rampOutput = () => {
    if (!context || !outputGain) return
    outputGain.gain.cancelScheduledValues(context.currentTime)
    outputGain.gain.linearRampToValueAtTime(outputTarget(), context.currentTime + 0.03)
  }

  const ensureOutputGain = () => {
    context ??= getAudioContext()
    if (!outputGain) {
      outputGain = context.createGain()
      outputGain.gain.value = outputTarget()
      outputGain.connect(context.destination)
    }
    return { context, outputGain }
  }

  const schedule = (callback: () => void, delay: number) => {
    const timer = window.setTimeout(() => {
      delayedTimers.delete(timer)
      callback()
    }, delay)
    delayedTimers.add(timer)
  }

  const releaseTone = (tone: ActiveTone) => {
    activeTones.delete(tone)
    try {
      tone.oscillator.disconnect()
      tone.gain.disconnect()
    } catch {
      // Nodes may already have been disconnected during component cleanup.
    }
  }

  const playTone = (
    audioContext: AudioContext,
    destination: GainNode,
    frequency: number,
    duration: number,
    type: OscillatorType,
    volume: number,
  ) => {
    const oscillator = audioContext.createOscillator()
    const gain = audioContext.createGain()
    const tone = { oscillator, gain }
    oscillator.type = type
    oscillator.frequency.value = frequency
    gain.gain.value = volume
    gain.gain.linearRampToValueAtTime(0, audioContext.currentTime + duration)
    oscillator.connect(gain)
    gain.connect(destination)
    oscillator.start()
    oscillator.stop(audioContext.currentTime + duration)
    activeTones.add(tone)
    schedule(() => releaseTone(tone), duration * 1000 + 20)
  }

  const playSweep = (
    audioContext: AudioContext,
    destination: GainNode,
    startFrequency: number,
    endFrequency: number,
    duration: number,
  ) => {
    const oscillator = audioContext.createOscillator()
    const gain = audioContext.createGain()
    const tone = { oscillator, gain }
    oscillator.type = 'sine'
    oscillator.frequency.value = startFrequency
    oscillator.frequency.linearRampToValueAtTime(endFrequency, audioContext.currentTime + duration)
    gain.gain.value = 0.2
    gain.gain.linearRampToValueAtTime(0, audioContext.currentTime + duration)
    oscillator.connect(gain)
    gain.connect(destination)
    oscillator.start()
    oscillator.stop(audioContext.currentTime + duration)
    activeTones.add(tone)
    schedule(() => releaseTone(tone), duration * 1000 + 20)
  }

  const playChord = (
    audioContext: AudioContext,
    destination: GainNode,
    frequencies: number[],
    duration: number,
    type: OscillatorType,
  ) => frequencies.forEach((frequency) => playTone(audioContext, destination, frequency, duration, type, 0.15))

  const playSFX = (name: string) => {
    if (mixer.isMuted.value) return
    const { context: audioContext, outputGain: destination } = ensureOutputGain()

    switch (name) {
      case 'click':
        playTone(audioContext, destination, 800, 0.08, 'sine', 0.3)
        break
      case 'fragment_found':
        playTone(audioContext, destination, 1200, 0.15, 'sine', 0.4)
        schedule(() => playTone(audioContext, destination, 1600, 0.15, 'sine', 0.3), 100)
        schedule(() => playTone(audioContext, destination, 2000, 0.2, 'sine', 0.5), 200)
        schedule(() => playTone(audioContext, destination, 2400, 0.3, 'sine', 0.4), 350)
        break
      case 'trust_up':
        playTone(audioContext, destination, 523.25, 0.3, 'sine', 0.3)
        playTone(audioContext, destination, 659.25, 0.3, 'sine', 0.25)
        playTone(audioContext, destination, 783.99, 0.3, 'sine', 0.2)
        break
      case 'trust_down':
        playTone(audioContext, destination, 200, 0.4, 'sawtooth', 0.2)
        schedule(() => playTone(audioContext, destination, 150, 0.5, 'sawtooth', 0.15), 200)
        break
      case 'scene_transition':
        playSweep(audioContext, destination, 200, 2000, 1.5)
        break
      case 'typing':
        playTone(audioContext, destination, 600 + Math.random() * 200, 0.03, 'square', 0.1)
        break
      case 'ending_hope':
        playChord(audioContext, destination, [261.63, 329.63, 392, 523.25], 2, 'sine')
        break
      case 'ending_bittersweet':
        playChord(audioContext, destination, [261.63, 311.13, 392], 3, 'triangle')
        break
      case 'ending_tragic':
        playTone(audioContext, destination, 220, 3, 'sine', 0.3)
        break
      case 'dialogue_start':
        playTone(audioContext, destination, 500, 0.1, 'sine', 0.2)
        schedule(() => playTone(audioContext, destination, 700, 0.1, 'sine', 0.15), 80)
        break
      case 'explore':
        playSweep(audioContext, destination, 400, 800, 0.3)
        break
    }
  }

  const cleanup = () => {
    delayedTimers.forEach((timer) => window.clearTimeout(timer))
    delayedTimers.clear()
    activeTones.forEach((tone) => {
      try {
        tone.oscillator.stop()
      } catch {
        // The oscillator may already have ended naturally.
      }
      releaseTone(tone)
    })
    outputGain?.disconnect()
    outputGain = null
    context = null
  }

  watch(mixer.effectiveSfxVolume, rampOutput, { flush: 'sync' })
  if (getCurrentInstance()) onUnmounted(cleanup)

  return { playSFX }
}

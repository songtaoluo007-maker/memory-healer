import { getAudioContext } from '../audio/context'
import { useAudioMixer } from '../audio/mixer'

export function useSfxBus() {
  const mixer = useAudioMixer()

  const playTone = (
    context: AudioContext,
    destination: GainNode,
    frequency: number,
    duration: number,
    type: OscillatorType,
    volume: number,
  ) => {
    const oscillator = context.createOscillator()
    const gain = context.createGain()
    oscillator.type = type
    oscillator.frequency.value = frequency
    gain.gain.value = volume
    gain.gain.linearRampToValueAtTime(0, context.currentTime + duration)
    oscillator.connect(gain)
    gain.connect(destination)
    oscillator.start()
    oscillator.stop(context.currentTime + duration)
  }

  const playSweep = (
    context: AudioContext,
    destination: GainNode,
    startFrequency: number,
    endFrequency: number,
    duration: number,
  ) => {
    const oscillator = context.createOscillator()
    const gain = context.createGain()
    oscillator.type = 'sine'
    oscillator.frequency.value = startFrequency
    oscillator.frequency.linearRampToValueAtTime(endFrequency, context.currentTime + duration)
    gain.gain.value = 0.2
    gain.gain.linearRampToValueAtTime(0, context.currentTime + duration)
    oscillator.connect(gain)
    gain.connect(destination)
    oscillator.start()
    oscillator.stop(context.currentTime + duration)
  }

  const playChord = (
    context: AudioContext,
    destination: GainNode,
    frequencies: number[],
    duration: number,
    type: OscillatorType,
  ) => frequencies.forEach((frequency) => playTone(context, destination, frequency, duration, type, 0.15))

  const playSFX = (name: string) => {
    if (mixer.isMuted.value) return
    const context = getAudioContext()
    const masterGain = context.createGain()
    masterGain.gain.value = mixer.effectiveSfxVolume.value * 0.3
    masterGain.connect(context.destination)

    switch (name) {
      case 'click':
        playTone(context, masterGain, 800, 0.08, 'sine', 0.3)
        break
      case 'fragment_found':
        playTone(context, masterGain, 1200, 0.15, 'sine', 0.4)
        window.setTimeout(() => playTone(context, masterGain, 1600, 0.15, 'sine', 0.3), 100)
        window.setTimeout(() => playTone(context, masterGain, 2000, 0.2, 'sine', 0.5), 200)
        window.setTimeout(() => playTone(context, masterGain, 2400, 0.3, 'sine', 0.4), 350)
        break
      case 'trust_up':
        playTone(context, masterGain, 523.25, 0.3, 'sine', 0.3)
        playTone(context, masterGain, 659.25, 0.3, 'sine', 0.25)
        playTone(context, masterGain, 783.99, 0.3, 'sine', 0.2)
        break
      case 'trust_down':
        playTone(context, masterGain, 200, 0.4, 'sawtooth', 0.2)
        window.setTimeout(() => playTone(context, masterGain, 150, 0.5, 'sawtooth', 0.15), 200)
        break
      case 'scene_transition':
        playSweep(context, masterGain, 200, 2000, 1.5)
        break
      case 'typing':
        playTone(context, masterGain, 600 + Math.random() * 200, 0.03, 'square', 0.1)
        break
      case 'ending_hope':
        playChord(context, masterGain, [261.63, 329.63, 392, 523.25], 2, 'sine')
        break
      case 'ending_bittersweet':
        playChord(context, masterGain, [261.63, 311.13, 392], 3, 'triangle')
        break
      case 'ending_tragic':
        playTone(context, masterGain, 220, 3, 'sine', 0.3)
        break
      case 'dialogue_start':
        playTone(context, masterGain, 500, 0.1, 'sine', 0.2)
        window.setTimeout(() => playTone(context, masterGain, 700, 0.1, 'sine', 0.15), 80)
        break
      case 'explore':
        playSweep(context, masterGain, 400, 800, 0.3)
        break
    }
  }

  return { playSFX }
}

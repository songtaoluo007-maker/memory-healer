import { getCurrentInstance, onUnmounted, ref, watch } from 'vue'
import { getAudioContext } from '../audio/context'
import { useAudioMixer } from '../audio/mixer'

const sceneBgmConfig: Record<
  string,
  { frequencies: number[]; type: OscillatorType; volume: number }
> = {
  scene_1972: { frequencies: [261.63, 293.66, 329.63, 392, 440], type: 'sine', volume: 0.06 },
  scene_2024: { frequencies: [261.63, 311.13, 349.23, 415.3], type: 'triangle', volume: 0.05 },
  scene_2089: { frequencies: [220, 277.18, 329.63, 440, 554.37], type: 'sine', volume: 0.04 },
}

const ambientConfig: Record<string, { filterFreq: number; volume: number }> = {
  scene_1972: { filterFreq: 800, volume: 0.015 },
  scene_2024: { filterFreq: 400, volume: 0.02 },
  scene_2089: { filterFreq: 2000, volume: 0.008 },
}

interface ActiveMusic {
  gain: GainNode
  oscillators: OscillatorNode[]
}

interface ActiveAmbience {
  gain: GainNode
  source: AudioBufferSourceNode
}

const decibelsToGain = (decibels: number) => 10 ** (decibels / 20)

export function useMusicBus() {
  const mixer = useAudioMixer()
  const currentScene = ref('')
  let activeMusic: ActiveMusic | null = null
  let activeAmbience: ActiveAmbience | null = null

  const musicTarget = (sceneId: string) => {
    const config = sceneBgmConfig[sceneId] ?? sceneBgmConfig.scene_1972!
    return config.volume * mixer.effectiveMusicVolume.value * decibelsToGain(mixer.musicDuckDb.value)
  }

  const ambienceTarget = (sceneId: string) => {
    const config = ambientConfig[sceneId] ?? ambientConfig.scene_1972!
    return config.volume * mixer.effectiveMusicVolume.value * decibelsToGain(mixer.ambienceDuckDb.value)
  }

  const ramp = (gain: GainNode, target: number, duration = 0.15) => {
    const context = getAudioContext()
    gain.gain.cancelScheduledValues(context.currentTime)
    gain.gain.linearRampToValueAtTime(target, context.currentTime + duration)
  }

  const refreshGains = () => {
    if (activeMusic) ramp(activeMusic.gain, musicTarget(currentScene.value))
    if (activeAmbience) ramp(activeAmbience.gain, ambienceTarget(currentScene.value))
  }

  watch(
    [
      mixer.effectiveMusicVolume,
      mixer.musicDuckDb,
      mixer.ambienceDuckDb,
      () => currentScene.value,
    ],
    refreshGains,
  )

  const stopBGM = () => {
    const music = activeMusic
    const ambience = activeAmbience
    activeMusic = null
    activeAmbience = null
    currentScene.value = ''

    if (music) {
      ramp(music.gain, 0, 1)
      window.setTimeout(() => {
        music.oscillators.forEach((oscillator) => {
          try {
            oscillator.stop()
          } catch {
            // The oscillator may already have stopped during a scene change.
          }
        })
        music.gain.disconnect()
      }, 1200)
    }

    if (ambience) {
      ramp(ambience.gain, 0, 1)
      window.setTimeout(() => {
        try {
          ambience.source.stop()
        } catch {
          // The source may already have stopped during a scene change.
        }
        ambience.gain.disconnect()
      }, 1200)
    }
  }

  const playAmbient = (sceneId: string) => {
    const context = getAudioContext()
    const config = ambientConfig[sceneId] ?? ambientConfig.scene_1972!
    const buffer = context.createBuffer(1, context.sampleRate * 2, context.sampleRate)
    const data = buffer.getChannelData(0)
    for (let index = 0; index < data.length; index += 1) {
      data[index] = (Math.random() * 2 - 1) * 0.5
    }

    const source = context.createBufferSource()
    const filter = context.createBiquadFilter()
    const gain = context.createGain()
    source.buffer = buffer
    source.loop = true
    filter.type = 'lowpass'
    filter.frequency.value = config.filterFreq
    filter.Q.value = 1
    gain.gain.value = 0
    source.connect(filter)
    filter.connect(gain)
    gain.connect(context.destination)
    source.start()
    activeAmbience = { source, gain }
    ramp(gain, ambienceTarget(sceneId), 2)
  }

  const playBGM = (sceneId: string) => {
    if (mixer.isMuted.value) return
    if (currentScene.value === sceneId && activeMusic) return

    stopBGM()
    currentScene.value = sceneId
    const context = getAudioContext()
    const config = sceneBgmConfig[sceneId] ?? sceneBgmConfig.scene_1972!
    const gain = context.createGain()
    gain.gain.value = 0
    gain.connect(context.destination)
    const oscillators: OscillatorNode[] = []

    config.frequencies.forEach((frequency, index) => {
      const oscillator = context.createOscillator()
      const oscillatorGain = context.createGain()
      const lfo = context.createOscillator()
      const lfoGain = context.createGain()
      oscillator.type = config.type
      oscillator.frequency.value = frequency
      oscillatorGain.gain.value = 0.3 + index * 0.1
      lfo.frequency.value = 0.1 + index * 0.05
      lfoGain.gain.value = 0.15
      lfo.connect(lfoGain)
      lfoGain.connect(oscillatorGain.gain)
      oscillator.connect(oscillatorGain)
      oscillatorGain.connect(gain)
      lfo.start()
      oscillator.start()
      oscillators.push(oscillator, lfo)
    })

    activeMusic = { gain, oscillators }
    ramp(gain, musicTarget(sceneId), 2)
    playAmbient(sceneId)
  }

  if (getCurrentInstance()) onUnmounted(stopBGM)

  return { currentScene, playBGM, stopBGM }
}

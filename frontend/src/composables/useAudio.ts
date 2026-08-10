import { useAudioMixer } from '../audio/mixer'
import { useMusicBus } from './useMusicBus'
import { useSfxBus } from './useSfxBus'
import { useVoicePlayback } from './useVoicePlayback'

/**
 * Backwards-compatible facade for the focused music, effects, voice, and mixer APIs.
 */
export function useAudio() {
  return {
    ...useMusicBus(),
    ...useSfxBus(),
    ...useVoicePlayback(),
    ...useAudioMixer(),
  }
}

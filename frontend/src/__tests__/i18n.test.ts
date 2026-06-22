/**
 * useI18n 测试
 */

import { describe, it, expect, beforeEach } from 'vitest'
import { useI18n } from '../composables/useI18n'

describe('useI18n', () => {
  beforeEach(() => {
    localStorage.clear()
    // Reset language to zh
    const { setLang } = useI18n()
    setLang('zh')
  })

  it('returns default language as zh', () => {
    const { lang } = useI18n()
    expect(lang.value).toBe('zh')
  })

  it('t() returns Chinese text by default', () => {
    const { t } = useI18n()
    expect(t('app.title')).toBe('拾忆')
    expect(t('app.subtitle')).toBe('一部关于遗忘与记忆的互动叙事')
  })

  it('t() returns English text when lang is en', () => {
    const { setLang, t } = useI18n()
    setLang('en')
    expect(t('app.title')).toBe('Memory Healer')
    expect(t('app.subtitle')).toBe('An interactive narrative about forgetting and memory')
  })

  it('t() returns key when translation missing', () => {
    const { t } = useI18n()
    expect(t('nonexistent.key')).toBe('nonexistent.key')
  })

  it('toggleLang switches between zh and en', () => {
    const { lang, toggleLang } = useI18n()
    expect(lang.value).toBe('zh')
    toggleLang()
    expect(lang.value).toBe('en')
    toggleLang()
    expect(lang.value).toBe('zh')
  })

  it('setLang persists to localStorage', () => {
    const { setLang } = useI18n()
    setLang('en')
    expect(localStorage.getItem('mh_lang')).toBe('en')
  })

  it('setLang with invalid value changes language (no validation)', () => {
    const { setLang, lang } = useI18n()
    setLang('fr' as any)
    // setLang doesn't validate input, so it accepts any value
    expect(lang.value).toBe('fr')
  })
})

<script setup lang="ts">
import { ref, watch } from 'vue'
import type { FragmentPresentation } from '../stage/fragmentPresentation'

const props = defineProps<{ presentation: FragmentPresentation }>()
const failed = ref(false)

watch(
  () => props.presentation.image,
  () => {
    failed.value = false
  },
)
</script>

<template>
  <figure v-if="!failed" class="fragment-artwork">
    <img
      :src="presentation.image"
      :alt="presentation.alt"
      :style="{ objectPosition: presentation.focus }"
      @error="failed = true"
    />
  </figure>
</template>

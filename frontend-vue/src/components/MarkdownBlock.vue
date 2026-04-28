<script setup>
import { computed } from 'vue'
import { marked } from 'marked'
import DOMPurify from 'dompurify'

const props = defineProps({
  content: {
    type: String,
    default: '',
  },
})

const renderedHtml = computed(() => {
  if (!props.content) return ''
  const unsafeHtml = marked.parse(props.content, {
    gfm: true,
    breaks: true,
  })
  return DOMPurify.sanitize(unsafeHtml)
})
</script>

<template>
  <div class="markdown-content" v-html="renderedHtml" />
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'
import api, { formatApiError } from '@/api.js'
import { getMcpDemoImport } from '@/constants/mcpDemoImports.js'

const route = useRoute()
const router = useRouter()

const importKey = computed(() => String(route.params.importId))
const isDemo = computed(() => importKey.value.startsWith('demo-'))
const numericId = computed(() => {
  const n = Number(importKey.value)
  return Number.isFinite(n) ? n : null
})

const row = ref(null)
const error = ref('')
const promoteError = ref('')

async function load() {
  error.value = ''
  if (isDemo.value) {
    row.value = getMcpDemoImport(importKey.value)
    if (!row.value) {
      error.value = 'That import could not be found.'
      row.value = null
    }
    return
  }
  if (numericId.value == null) {
    error.value = 'That import could not be found.'
    row.value = null
    return
  }
  try {
    row.value = await api.getMcpImport(numericId.value)
  } catch (e) {
    error.value = formatApiError(e)
    row.value = null
  }
}

async function promote() {
  if (isDemo.value || numericId.value == null) return
  promoteError.value = ''
  const name = window.prompt('New subject name', row.value?.title || 'New subject')
  if (!name) return
  const desc =
    window.prompt('Subject description', `Created from imported conversation: ${row.value?.title || ''}.`) || ''
  try {
    await api.promoteToSubject({
      source_model: 'mcpconversationimport',
      source_id: numericId.value,
      subject_name: name.slice(0, 100),
      subject_description: desc,
    })
    await router.push({ name: 'subjects-mine' })
  } catch (e) {
    promoteError.value = formatApiError(e)
  }
}

onMounted(load)
watch(importKey, load)
</script>

<template>
  <div class="mx-auto max-w-3xl">
    <RouterLink :to="{ name: 'explore-mcp' }" class="text-sm font-medium text-indigo-600 hover:text-indigo-800">
      ← Conversation imports
    </RouterLink>

    <p v-if="error" class="mt-8 rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">{{ error }}</p>

    <template v-else-if="row">
      <h3 class="mt-4 text-xl font-semibold text-slate-900">{{ row.title }}</h3>
      <p class="mt-1 text-xs text-slate-500">{{ row.status }} · {{ new Date(row.created_at).toLocaleString() }}</p>

      <div v-if="!isDemo" class="mt-6 flex flex-wrap gap-2">
        <button
          type="button"
          class="rounded-lg bg-slate-900 px-4 py-2 text-sm font-semibold text-white hover:bg-slate-800"
          @click="promote"
        >
          Promote to subject
        </button>
      </div>
      <p v-if="promoteError" class="mt-2 text-sm text-red-600">{{ promoteError }}</p>

      <div class="mt-8 rounded-2xl border border-slate-200 bg-white p-5 font-mono text-sm leading-relaxed text-slate-700 shadow-sm">
        <p v-for="(line, i) in row.lines || []" :key="i" class="border-b border-slate-100 py-2 last:border-0">
          {{ line }}
        </p>
        <p v-if="!(row.lines && row.lines.length) && row.transcript" class="whitespace-pre-wrap">{{ row.transcript }}</p>
      </div>
    </template>
  </div>
</template>

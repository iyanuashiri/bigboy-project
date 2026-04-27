<script setup>
import { ref } from 'vue'
import { RouterLink, useRouter } from 'vue-router'
import api, { formatApiError } from '@/api.js'

const router = useRouter()
const query = ref('')
const error = ref('')
const loading = ref(false)

async function submit() {
  error.value = ''
  if (!query.value.trim()) {
    error.value = 'Describe what you want researched.'
    return
  }
  loading.value = true
  try {
    const row = await api.createResearchRun({ query: query.value.trim() })
    await router.push({ name: 'explore-research-detail', params: { researchId: String(row.id) } })
  } catch (e) {
    error.value = formatApiError(e)
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="mx-auto max-w-2xl">
    <RouterLink :to="{ name: 'explore-research' }" class="text-sm font-medium text-indigo-600 hover:text-indigo-800">
      ← Research list
    </RouterLink>
    <h3 class="mt-4 text-xl font-semibold text-slate-900">New research</h3>
    <p class="mt-2 text-sm text-slate-600">
      Sends your brief to the research agent and saves structured sections when it finishes. This can take up to a few
      minutes.
    </p>
    <form class="mt-8 space-y-4" @submit.prevent="submit">
      <textarea
        v-model="query"
        rows="5"
        class="w-full rounded-2xl border border-slate-300 px-4 py-3 text-sm shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
        placeholder="e.g. Summarize best practices for spaced repetition in edtech…"
      />
      <p v-if="error" class="text-sm text-red-600">{{ error }}</p>
      <button
        type="submit"
        :disabled="loading"
        class="rounded-xl bg-indigo-600 px-5 py-3 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500 disabled:opacity-50"
      >
        {{ loading ? 'Running research…' : 'Create run' }}
      </button>
    </form>
  </div>
</template>

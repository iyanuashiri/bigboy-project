<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { RouterLink, useRoute } from 'vue-router'
import api, { formatApiError } from '@/api.js'

const route = useRoute()
const subjectFilter = computed(() => {
  const s = route.query.subject
  if (s === undefined || s === null || s === '') return undefined
  const n = Number(s)
  return Number.isFinite(n) ? n : undefined
})

const quizzes = ref([])
const error = ref('')
const loading = ref(true)

async function load() {
  loading.value = true
  error.value = ''
  try {
    quizzes.value = await api.getQuizzes(subjectFilter.value)
  } catch (e) {
    error.value = formatApiError(e)
  } finally {
    loading.value = false
  }
}

onMounted(load)
watch(subjectFilter, load)
</script>

<template>
  <div class="mx-auto max-w-3xl">
    <div class="flex flex-wrap items-center justify-between gap-4">
      <h1 class="text-xl font-semibold text-slate-900">Quizzes</h1>
      <div class="flex gap-3 text-sm">
        <RouterLink :to="{ name: 'dashboard' }" class="font-medium text-slate-600 hover:text-slate-900">Dashboard</RouterLink>
        <RouterLink :to="{ name: 'subjects-mine' }" class="font-medium text-slate-600 hover:text-slate-900">
          My subjects
        </RouterLink>
      </div>
    </div>
    <p v-if="subjectFilter != null" class="mt-1 text-sm text-slate-600">Filtered to subject #{{ subjectFilter }}.</p>

    <p v-if="error" class="mt-4 rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">{{ error }}</p>
    <p v-if="loading" class="mt-8 text-sm text-slate-500">Loading…</p>

    <ul v-else-if="quizzes.length" class="mt-6 divide-y divide-slate-200 rounded-2xl border border-slate-200 bg-white shadow-sm">
      <li v-for="q in quizzes" :key="q.id" class="flex flex-wrap items-center justify-between gap-3 px-4 py-4">
        <div>
          <p class="font-medium text-slate-900">{{ q.topic?.name || `Quiz #${q.id}` }}</p>
          <p class="text-sm text-slate-600">{{ q.subject?.name }}</p>
        </div>
        <RouterLink
          :to="{ name: 'quiz', params: { id: q.id } }"
          class="rounded-lg bg-slate-900 px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-slate-800"
        >
          Open
        </RouterLink>
      </li>
    </ul>

    <div
      v-else-if="!loading && !error"
      class="mt-10 rounded-2xl border border-dashed border-slate-300 bg-slate-50/90 px-6 py-14 text-center"
    >
      <p class="text-sm font-medium text-slate-800">No quizzes here yet</p>
      <p class="mt-2 text-sm text-slate-600">
        Promote a document category or research run to a subject — quizzes are created per topic. Or pick another
        subject filter above.
      </p>
      <RouterLink
        :to="{ name: 'subjects-mine' }"
        class="mt-5 inline-flex text-sm font-semibold text-indigo-700 hover:text-indigo-900"
      >
        Go to subjects →
      </RouterLink>
    </div>
  </div>
</template>

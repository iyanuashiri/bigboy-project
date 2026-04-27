<script setup>
import { onMounted, ref } from 'vue'
import { RouterLink } from 'vue-router'
import api, { formatApiError } from '@/api.js'

const subjects = ref([])
const error = ref('')
const loading = ref(true)

async function load() {
  loading.value = true
  error.value = ''
  try {
    subjects.value = await api.getSubjects('enrolled')
  } catch (e) {
    error.value = formatApiError(e)
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>

<template>
  <div class="mx-auto max-w-3xl">
    <div class="flex items-center justify-between gap-4">
      <h1 class="text-xl font-semibold text-slate-900">My subjects</h1>
      <RouterLink :to="{ name: 'subjects-catalog' }" class="text-sm font-medium text-slate-600 hover:text-slate-900">
        Catalog
      </RouterLink>
    </div>

    <p v-if="error" class="mt-4 rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">{{ error }}</p>
    <p v-if="loading" class="mt-8 text-sm text-slate-500">Loading…</p>

    <ul v-else-if="subjects.length" class="mt-6 space-y-3">
      <li
        v-for="s in subjects"
        :key="s.id"
        class="rounded-lg border border-slate-200 bg-white p-4 shadow-sm"
      >
        <p class="font-medium text-slate-900">{{ s.name }}</p>
        <p class="mt-1 text-sm text-slate-600">{{ s.description }}</p>
        <div class="mt-3 flex flex-wrap gap-2">
          <RouterLink
            :to="{ name: 'subject', params: { id: s.id } }"
            class="rounded-md border border-slate-300 px-3 py-1.5 text-sm font-medium text-slate-800 hover:bg-slate-50"
          >
            Open
          </RouterLink>
          <RouterLink
            :to="{ name: 'lesson', params: { id: s.id } }"
            class="rounded-md bg-slate-900 px-3 py-1.5 text-sm font-medium text-white hover:bg-slate-800"
          >
            Lesson
          </RouterLink>
          <RouterLink
            :to="{ name: 'quizzes', query: { subject: s.id } }"
            class="rounded-md border border-slate-300 px-3 py-1.5 text-sm font-medium text-slate-800 hover:bg-slate-50"
          >
            Quizzes
          </RouterLink>
        </div>
      </li>
    </ul>

    <div
      v-else-if="!loading && !subjects.length && !error"
      class="mt-10 rounded-2xl border border-dashed border-slate-300 bg-gradient-to-b from-slate-50 to-white px-6 py-14 text-center shadow-sm"
    >
      <p class="text-base font-semibold text-slate-900">No subjects yet</p>
      <p class="mt-2 text-sm text-slate-600">
        Enroll from the catalog, or promote Explore sources into a subject when you are ready for structured bites and
        quizzes.
      </p>
      <div class="mt-6 flex flex-wrap justify-center gap-3">
        <RouterLink
          :to="{ name: 'subjects-catalog' }"
          class="rounded-lg bg-slate-900 px-4 py-2 text-sm font-semibold text-white hover:bg-slate-800"
        >
          Browse catalog
        </RouterLink>
        <RouterLink
          :to="{ name: 'explore-chats' }"
          class="rounded-lg border border-slate-300 bg-white px-4 py-2 text-sm font-semibold text-slate-800 hover:bg-slate-50"
        >
          Explore documents
        </RouterLink>
      </div>
    </div>
  </div>
</template>

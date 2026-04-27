<script setup>
import { onMounted, ref } from 'vue'
import { RouterLink, useRouter } from 'vue-router'
import api, { formatApiError } from '@/api.js'

const router = useRouter()
const subjects = ref([])
const message = ref('')
const error = ref('')
const loading = ref(true)
const enrollingId = ref(null)

async function load() {
  loading.value = true
  error.value = ''
  try {
    subjects.value = await api.getSubjects('catalog')
  } catch (e) {
    error.value = formatApiError(e)
  } finally {
    loading.value = false
  }
}

async function enroll(subjectId) {
  message.value = ''
  error.value = ''
  enrollingId.value = subjectId
  try {
    await api.enroll(subjectId)
    message.value = 'Enrolled successfully.'
    await router.push({ name: 'subjects-mine' })
  } catch (e) {
    error.value = formatApiError(e)
  } finally {
    enrollingId.value = null
  }
}

onMounted(load)
</script>

<template>
  <div class="mx-auto max-w-3xl">
    <div class="flex items-center justify-between gap-4">
      <h1 class="text-xl font-semibold text-slate-900">Catalog</h1>
      <RouterLink :to="{ name: 'subjects-mine' }" class="text-sm font-medium text-slate-600 hover:text-slate-900">
        My subjects
      </RouterLink>
    </div>
    <p class="mt-1 text-sm text-slate-600">All subjects. Enroll to unlock lessons and quizzes for that subject.</p>

    <p v-if="message" class="mt-4 rounded-md bg-emerald-50 px-3 py-2 text-sm text-emerald-800">{{ message }}</p>
    <p v-if="error" class="mt-4 rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">{{ error }}</p>

    <p v-if="loading" class="mt-8 text-sm text-slate-500">Loading…</p>

    <ul v-else class="mt-6 divide-y divide-slate-200 rounded-lg border border-slate-200 bg-white">
      <li v-for="s in subjects" :key="s.id" class="flex flex-wrap items-center justify-between gap-3 px-4 py-3">
        <div>
          <p class="font-medium text-slate-900">{{ s.name }}</p>
          <p class="text-sm text-slate-600">{{ s.description }}</p>
        </div>
        <button
          type="button"
          class="rounded-md bg-slate-900 px-3 py-1.5 text-sm font-medium text-white hover:bg-slate-800 disabled:opacity-50"
          :disabled="enrollingId === s.id"
          @click="enroll(s.id)"
        >
          {{ enrollingId === s.id ? '…' : 'Enroll' }}
        </button>
      </li>
    </ul>
  </div>
</template>

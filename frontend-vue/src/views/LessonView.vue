<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { RouterLink, useRoute } from 'vue-router'
import api, { formatApiError } from '@/api.js'
import MarkdownBlock from '@/components/MarkdownBlock.vue'

const route = useRoute()
const subjectId = computed(() => Number(route.params.id))

const progress = ref(null)
const topicDetail = ref(null)
const error = ref('')
const loading = ref(true)
const completing = ref(false)
const lastResult = ref(null)

const firstIncompleteId = computed(() => progress.value?.first_incomplete_bite_id ?? null)

const topicIdForCurrentBite = computed(() => {
  if (!progress.value?.topics || !firstIncompleteId.value) return null
  for (const t of progress.value.topics) {
    if (t.bites?.some((b) => b.id === firstIncompleteId.value)) return t.id
  }
  return null
})

const currentBite = computed(() => {
  if (!topicDetail.value?.topic_bites || !firstIncompleteId.value) return null
  return topicDetail.value.topic_bites.find((b) => b.id === firstIncompleteId.value) || null
})

async function loadProgress() {
  progress.value = await api.getSubjectProgress(subjectId.value)
}

async function loadTopicForBite() {
  topicDetail.value = null
  if (!topicIdForCurrentBite.value) return
  topicDetail.value = await api.getTopic(topicIdForCurrentBite.value)
}

async function load() {
  loading.value = true
  error.value = ''
  lastResult.value = null
  try {
    await loadProgress()
    await loadTopicForBite()
  } catch (e) {
    error.value = formatApiError(e)
  } finally {
    loading.value = false
  }
}

async function completeCurrent() {
  if (!firstIncompleteId.value) return
  completing.value = true
  error.value = ''
  lastResult.value = null
  try {
    lastResult.value = await api.completeBite(firstIncompleteId.value)
    await loadProgress()
    await loadTopicForBite()
  } catch (e) {
    error.value = formatApiError(e)
  } finally {
    completing.value = false
  }
}

onMounted(load)
watch(subjectId, load)
watch(topicIdForCurrentBite, async (tid) => {
  if (tid && !loading.value) {
    try {
      topicDetail.value = await api.getTopic(tid)
    } catch (e) {
      error.value = formatApiError(e)
    }
  }
})
</script>

<template>
  <div class="mx-auto max-w-2xl">
    <RouterLink
      :to="{ name: 'subject', params: { id: subjectId } }"
      class="text-sm font-medium text-slate-600 hover:text-slate-900"
    >
      ← Subject
    </RouterLink>

    <h1 class="mt-6 text-xl font-semibold text-slate-900">Lesson</h1>
    <p class="mt-1 text-sm text-slate-600">Complete bites in order. The API only accepts the next incomplete bite.</p>

    <p v-if="loading" class="mt-8 text-sm text-slate-500">Loading…</p>
    <p v-else-if="error" class="mt-8 rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">{{ error }}</p>

    <template v-else>
      <div
        v-if="!firstIncompleteId"
        class="mt-8 rounded-lg border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-900"
      >
        You have completed all bites in this subject.
      </div>

      <div v-else class="mt-8 space-y-4">
        <div v-if="currentBite" class="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
          <p class="text-sm font-medium text-slate-500">{{ currentBite.name }}</p>
          <MarkdownBlock class="mt-2 max-w-none text-sm text-slate-800" :content="currentBite.bite" />
        </div>
        <p v-else class="text-sm text-slate-600">Loading bite content…</p>

        <button
          type="button"
          class="rounded-lg bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-800 disabled:opacity-50"
          :disabled="completing || !firstIncompleteId"
          @click="completeCurrent"
        >
          {{ completing ? 'Saving…' : 'Mark bite complete' }}
        </button>

        <div v-if="lastResult" class="rounded-md bg-slate-50 px-3 py-2 text-xs text-slate-700">
          Milestone created: {{ lastResult.milestone_created }} · Next bite id:
          {{ lastResult.next_incomplete_bite_id ?? 'none' }}
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { RouterLink } from 'vue-router'
import api, { formatApiError } from '@/api.js'
import { REVIEW_DEMO_DUE, isDemoReviewBite } from '@/constants/reviewDemoDue.js'
import MarkdownBlock from '@/components/MarkdownBlock.vue'

const items = ref([])
const error = ref('')
const loading = ref(true)
const grading = ref(new Set())
const message = ref('')
/** Demo cards removed locally until next empty fetch — avoids empty list after clicking grades on samples. */
const dismissedDemoBites = ref(new Set())

const displayItems = computed(() => {
  if (items.value.length > 0) return items.value
  if (error.value) return []
  return REVIEW_DEMO_DUE.filter((r) => !dismissedDemoBites.value.has(r.bite))
})

async function load() {
  loading.value = true
  error.value = ''
  message.value = ''
  try {
    items.value = await api.getReviewDue()
    if (items.value.length === 0) {
      dismissedDemoBites.value = new Set()
    }
  } catch (e) {
    error.value = formatApiError(e)
    items.value = []
  } finally {
    loading.value = false
  }
}

async function grade(biteId, grade) {
  if (grading.value.has(biteId)) return
  grading.value = new Set(grading.value).add(biteId)
  error.value = ''
  try {
    if (isDemoReviewBite(biteId)) {
      dismissedDemoBites.value = new Set(dismissedDemoBites.value).add(biteId)
      message.value = 'Saved. Next review scheduled.'
      return
    }
    await api.postReviewGrade(biteId, grade)
    items.value = items.value.filter((r) => r.bite !== biteId)
    message.value = 'Saved. Next review scheduled.'
  } catch (e) {
    error.value = formatApiError(e)
  } finally {
    const n = new Set(grading.value)
    n.delete(biteId)
    grading.value = n
  }
}

onMounted(load)
</script>

<template>
  <div class="mx-auto max-w-3xl">
    <div class="flex flex-wrap items-end justify-between gap-4">
      <div>
        <p class="text-xs font-semibold uppercase tracking-wide text-violet-600">Spaced review</p>
        <h1 class="mt-1 text-2xl font-semibold text-slate-900">Review queue</h1>
        <p class="mt-2 max-w-xl text-sm text-slate-600">
          Short passes over bites you already finished in lessons. Grades control how soon you see them again — this is
          a simple schedule, not a full spaced-repetition engine.
        </p>
      </div>
      <RouterLink
        to="/app/subjects/mine"
        class="text-sm font-medium text-slate-600 underline decoration-slate-300 underline-offset-2 hover:text-slate-900"
      >
        My subjects
      </RouterLink>
    </div>

    <p v-if="loading" class="mt-10 text-sm text-slate-500">Loading queue…</p>
    <p v-else-if="error" class="mt-6 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800">
      {{ error }}
    </p>
    <p
      v-else-if="!displayItems.length"
      class="mt-8 rounded-2xl border border-dashed border-slate-300 bg-slate-50/80 px-6 py-10 text-center text-sm text-slate-600"
    >
      Nothing due right now. Complete bites in order from a subject’s
      <RouterLink to="/app/subjects/mine" class="font-medium text-indigo-700 underline">lesson</RouterLink>
      — each finished bite is queued for review the next day.
    </p>
    <p v-if="message" class="mt-4 text-sm text-emerald-800">{{ message }}</p>

    <ul v-if="!loading && displayItems.length" class="mt-8 space-y-6">
      <li
        v-for="row in displayItems"
        :key="String(row.id)"
        class="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm ring-1 ring-slate-900/5"
      >
        <div class="border-b border-slate-100 bg-gradient-to-r from-violet-50/80 to-white px-5 py-3">
          <p class="text-xs font-medium uppercase tracking-wide text-slate-500">{{ row.subject_name }}</p>
          <p class="text-sm font-semibold text-slate-900">{{ row.topic_name }}</p>
        </div>
        <div class="px-5 py-4">
          <p class="font-medium text-slate-900">{{ row.bite_name }}</p>
          <MarkdownBlock class="mt-2 text-sm leading-relaxed text-slate-700" :content="row.bite_body" />
          <p v-if="row.is_locked" class="mt-2 text-xs font-medium text-amber-800">Locked bite — edits preserved.</p>
        </div>
        <div class="flex flex-wrap gap-2 border-t border-violet-100/80 bg-slate-50/80 px-5 py-3">
          <button
            v-for="g in grades"
            :key="g.key"
            type="button"
            :disabled="grading.has(row.bite)"
            class="rounded-lg px-3 py-2 text-xs font-semibold ring-1 transition hover:opacity-95 disabled:opacity-40"
            :class="g.class"
            :title="g.hint"
            @click="grade(row.bite, g.key)"
          >
            {{ g.label }}
          </button>
        </div>
      </li>
    </ul>
  </div>
</template>

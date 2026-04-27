<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { RouterLink, useRoute } from 'vue-router'
import api, { formatApiError } from '@/api.js'

const route = useRoute()
const subject = ref(null)
const error = ref('')
const loading = ref(true)
const weekly = ref(null)
const goalTargetInput = ref(5)
const goalId = ref(null)
const goalSaving = ref(false)
const goalMsg = ref('')

const subjectId = computed(() => Number(route.params.id))

const topics = computed(() => subject.value?.subject_topics ?? [])

const totalBites = computed(() =>
  topics.value.reduce((n, t) => n + (Number(t.bite_count) || (t.topic_bites?.length ?? 0)), 0),
)

const totalQuizzes = computed(() => topics.value.filter((t) => t.quiz_id != null).length)

const goalProgressPct = computed(() => {
  const t = Number(weekly.value?.weekly_bite_target || goalTargetInput.value || 5)
  const d = weekly.value?.completed_this_week
  if (!t || t <= 0) return 0
  return Math.min(100, Math.round((100 * (d || 0)) / t))
})

function bitePreview(topic) {
  const bites = topic.topic_bites || []
  return bites.slice(0, 3)
}

async function loadWeekly() {
  weekly.value = { completed_this_week: 0, weekly_bite_target: null, goal_active: false }
  goalId.value = null
  try {
    weekly.value = await api.getWeeklyProgress(subjectId.value)
    const goals = await api.getSubjectGoals()
    const g = (goals || []).find((x) => x.subject === subjectId.value && x.active !== false)
    goalId.value = g?.id ?? null
    if (g) goalTargetInput.value = g.weekly_bite_target
    else goalTargetInput.value = weekly.value?.weekly_bite_target || 5
  } catch {
    weekly.value = { completed_this_week: 0, weekly_bite_target: null, goal_active: false }
  }
}

async function load() {
  loading.value = true
  error.value = ''
  goalMsg.value = ''
  subject.value = null
  try {
    const data = await api.getSubject(subjectId.value)
    await loadWeekly()
    subject.value = data
  } catch (e) {
    error.value = formatApiError(e)
  } finally {
    loading.value = false
  }
}

async function saveWeeklyGoal() {
  goalSaving.value = true
  goalMsg.value = ''
  error.value = ''
  try {
    const n = Math.max(1, Math.min(40, Number(goalTargetInput.value) || 5))
    const body = { subject: subjectId.value, weekly_bite_target: n, active: true }
    if (goalId.value) await api.patchSubjectGoal(goalId.value, body)
    else {
      const created = await api.createSubjectGoal(body)
      goalId.value = created.id
    }
    goalMsg.value = 'Weekly goal saved.'
    await loadWeekly()
  } catch (e) {
    error.value = formatApiError(e)
  } finally {
    goalSaving.value = false
  }
}

onMounted(load)
watch(subjectId, load)
</script>

<template>
  <div class="mx-auto max-w-3xl px-1">
    <div class="flex items-center justify-between gap-4">
      <RouterLink :to="{ name: 'subjects-mine' }" class="text-sm font-medium text-slate-600 hover:text-slate-900">
        ← My subjects
      </RouterLink>
    </div>

    <p v-if="loading" class="mt-8 text-sm text-slate-500">Loading…</p>
    <p v-else-if="error" class="mt-8 rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">{{ error }}</p>

    <template v-else-if="subject">
      <header class="mt-6 rounded-2xl border border-slate-200/80 bg-gradient-to-br from-slate-50 to-white px-5 py-6 shadow-sm">
        <h1 class="text-2xl font-semibold tracking-tight text-slate-900">{{ subject.name }}</h1>
        <p class="mt-2 text-sm leading-relaxed text-slate-600">{{ subject.description }}</p>
        <dl class="mt-4 flex flex-wrap gap-4 text-xs text-slate-500">
          <div>
            <dt class="font-medium text-slate-400">Topics</dt>
            <dd class="text-sm font-semibold text-slate-800">{{ topics.length }}</dd>
          </div>
          <div>
            <dt class="font-medium text-slate-400">Bites</dt>
            <dd class="text-sm font-semibold text-slate-800">{{ totalBites }}</dd>
          </div>
          <div>
            <dt class="font-medium text-slate-400">Quizzes</dt>
            <dd class="text-sm font-semibold text-slate-800">{{ totalQuizzes }}</dd>
          </div>
        </dl>
      </header>

      <section
        class="mt-6 overflow-hidden rounded-2xl border border-indigo-200/80 bg-gradient-to-br from-indigo-50/90 to-white p-5 shadow-sm"
      >
        <div class="flex flex-wrap items-end justify-between gap-4">
          <div>
            <h2 class="text-sm font-semibold uppercase tracking-wide text-indigo-700">Weekly bite goal</h2>
            <p class="mt-1 text-xs text-slate-600">Counts lesson bite checkpoints completed this calendar week.</p>
          </div>
          <RouterLink :to="{ name: 'review' }" class="text-xs font-semibold text-violet-700 hover:text-violet-900">
            Review queue →
          </RouterLink>
        </div>
        <div class="mt-4">
          <div class="flex justify-between text-xs font-medium text-slate-600">
            <span>{{ weekly.completed_this_week ?? 0 }} / {{ weekly.weekly_bite_target ?? goalTargetInput }} bites</span>
            <span v-if="weekly.goal_active">Goal on</span>
            <span v-else class="text-slate-400">No goal yet — set below</span>
          </div>
          <div class="mt-2 h-2.5 overflow-hidden rounded-full bg-white ring-1 ring-indigo-100">
            <div
              class="h-full rounded-full bg-gradient-to-r from-indigo-500 to-violet-500 transition-all"
              :style="{ width: goalProgressPct + '%' }"
            />
          </div>
        </div>
        <div class="mt-4 flex flex-wrap items-end gap-2">
          <div>
            <label class="text-xs font-medium text-slate-500" for="wt">Target / week</label>
            <input
              id="wt"
              v-model.number="goalTargetInput"
              type="number"
              min="1"
              max="40"
              class="mt-1 block w-24 rounded-lg border border-slate-300 px-2 py-1.5 text-sm"
            />
          </div>
          <button
            type="button"
            :disabled="goalSaving"
            class="rounded-lg bg-indigo-700 px-4 py-2 text-sm font-semibold text-white hover:bg-indigo-600 disabled:opacity-50"
            @click="saveWeeklyGoal"
          >
            {{ goalSaving ? 'Saving…' : 'Save goal' }}
          </button>
        </div>
        <p v-if="goalMsg" class="mt-2 text-xs font-medium text-emerald-800">{{ goalMsg }}</p>
      </section>

      <div class="mt-6 flex flex-wrap gap-2">
        <RouterLink
          :to="{ name: 'lesson', params: { id: subject.id } }"
          class="rounded-lg bg-slate-900 px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-slate-800"
        >
          Continue lesson
        </RouterLink>
        <RouterLink
          :to="{ name: 'quizzes', query: { subject: subject.id } }"
          class="rounded-lg border border-slate-300 bg-white px-4 py-2 text-sm font-medium text-slate-800 shadow-sm hover:bg-slate-50"
        >
          All quizzes
        </RouterLink>
        <RouterLink
          :to="{ name: 'review' }"
          class="rounded-lg border border-violet-300 bg-violet-50 px-4 py-2 text-sm font-medium text-violet-900 shadow-sm hover:bg-violet-100"
        >
          Review queue
        </RouterLink>
      </div>

      <h2 class="mt-10 text-sm font-semibold uppercase tracking-wide text-slate-500">Curriculum</h2>
      <p class="mt-1 text-sm text-slate-600">Each topic groups bites you learn in order; quizzes check that topic.</p>

      <ul v-if="topics.length" class="mt-5 space-y-4">
        <li
          v-for="t in topics"
          :key="t.id"
          class="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm ring-1 ring-slate-900/5"
        >
          <div class="border-b border-slate-100 bg-slate-50/80 px-4 py-3 sm:px-5">
            <div class="flex flex-wrap items-start justify-between gap-3">
              <div class="min-w-0 flex-1">
                <p class="font-semibold text-slate-900">{{ t.name }}</p>
                <p v-if="t.description" class="mt-1 text-sm text-slate-600">{{ t.description }}</p>
              </div>
              <div class="flex shrink-0 flex-wrap items-center gap-2">
                <span
                  class="inline-flex items-center rounded-full bg-emerald-50 px-2.5 py-0.5 text-xs font-medium text-emerald-800 ring-1 ring-emerald-600/20"
                >
                  {{ t.bite_count ?? t.topic_bites?.length ?? 0 }} bites
                </span>
                <RouterLink
                  v-if="t.quiz_id"
                  :to="{ name: 'quiz', params: { id: t.quiz_id } }"
                  class="inline-flex items-center rounded-full bg-violet-50 px-2.5 py-0.5 text-xs font-medium text-violet-800 ring-1 ring-violet-600/20 hover:bg-violet-100"
                >
                  Quiz
                </RouterLink>
              </div>
            </div>
          </div>

          <div v-if="bitePreview(t).length" class="px-4 py-3 sm:px-5">
            <p class="text-xs font-medium uppercase tracking-wide text-slate-400">Preview</p>
            <ul class="mt-2 space-y-2">
              <li v-for="b in bitePreview(t)" :key="b.id" class="text-sm text-slate-700">
                <span class="font-medium text-slate-900">{{ b.name }}</span>
                <span v-if="b.is_locked" class="ml-2 text-xs text-amber-700">(locked)</span>
                <span class="text-slate-500"> — </span>
                <span class="line-clamp-2 text-slate-600">{{ b.bite }}</span>
              </li>
            </ul>
          </div>

          <div class="flex flex-wrap gap-2 border-t border-slate-100 bg-slate-50/50 px-4 py-3 sm:px-5">
            <RouterLink
              :to="{ name: 'subject-topic', params: { subjectId: subject.id, topicId: t.id } }"
              class="text-sm font-medium text-slate-900 underline decoration-slate-300 underline-offset-2 hover:decoration-slate-600"
            >
              Open topic
            </RouterLink>
            <RouterLink
              v-if="t.quiz_id"
              :to="{ name: 'quiz', params: { id: t.quiz_id } }"
              class="text-sm font-medium text-violet-700 hover:text-violet-900"
            >
              Take quiz →
            </RouterLink>
          </div>
        </li>
      </ul>
      <p v-else class="mt-6 rounded-lg border border-dashed border-slate-200 bg-slate-50 px-4 py-6 text-center text-sm text-slate-600">
        No topics yet for this subject.
      </p>
    </template>
  </div>
</template>

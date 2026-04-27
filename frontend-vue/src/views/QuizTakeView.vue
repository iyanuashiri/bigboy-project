<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { RouterLink, useRoute } from 'vue-router'
import api, { formatApiError } from '@/api.js'

const route = useRoute()
const quizId = computed(() => Number(route.params.id))

const quiz = ref(null)
const error = ref('')
const loading = ref(true)
const answered = ref(new Set())
const submitting = ref(new Set())
const feedback = ref({})

async function load() {
  loading.value = true
  error.value = ''
  answered.value = new Set()
  submitting.value = new Set()
  feedback.value = {}
  try {
    quiz.value = await api.getQuiz(quizId.value)
  } catch (e) {
    error.value = formatApiError(e)
  } finally {
    loading.value = false
  }
}

async function chooseOption(questionId, optionId) {
  if (answered.value.has(questionId) || submitting.value.has(questionId)) return
  submitting.value = new Set(submitting.value).add(questionId)
  error.value = ''
  try {
    const res = await api.submitQuizAnswer({
      question: questionId,
      selected_option: optionId,
    })
    answered.value = new Set(answered.value).add(questionId)
    feedback.value = {
      ...feedback.value,
      [questionId]: res,
    }
  } catch (e) {
    error.value = formatApiError(e)
  } finally {
    const next = new Set(submitting.value)
    next.delete(questionId)
    submitting.value = next
  }
}

onMounted(load)
watch(quizId, load)
</script>

<template>
  <div class="mx-auto max-w-2xl">
    <RouterLink :to="{ name: 'quizzes' }" class="text-sm font-medium text-slate-600 hover:text-slate-900">
      ← Quizzes
    </RouterLink>

    <p v-if="loading" class="mt-8 text-sm text-slate-500">Loading…</p>
    <p v-else-if="error" class="mt-8 rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">{{ error }}</p>

    <template v-else-if="quiz">
      <h1 class="mt-6 text-xl font-semibold text-slate-900">{{ quiz.topic?.name || 'Quiz' }}</h1>
      <p class="text-sm text-slate-600">{{ quiz.subject?.name }}</p>

      <div
        v-if="Object.values(feedback).some((f) => f.quiz_completed)"
        class="mt-6 rounded-lg border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-900"
      >
        Quiz completed. Completion points were added to your total.
      </div>

      <section class="mt-8 space-y-8">
        <article
          v-for="(q, idx) in quiz.quiz_questions || []"
          :key="q.id"
          class="rounded-lg border border-slate-200 bg-white p-4 shadow-sm"
        >
          <p class="text-sm font-medium text-slate-500">Question {{ idx + 1 }}</p>
          <p class="mt-2 text-slate-900">{{ q.question }}</p>
          <div class="mt-3 flex flex-col gap-2">
            <button
              v-for="opt in q.question_options || []"
              :key="opt.id"
              type="button"
              :disabled="answered.has(q.id) || submitting.has(q.id)"
              class="rounded-xl border border-slate-200 bg-white px-4 py-3 text-left text-sm shadow-sm transition hover:border-slate-300 hover:bg-slate-50 disabled:opacity-50"
              @click="chooseOption(q.id, opt.id)"
            >
              {{ opt.option }}
            </button>
          </div>
          <div v-if="feedback[q.id]" class="mt-4 space-y-2">
            <p class="text-sm">
              <span :class="feedback[q.id].is_correct ? 'font-semibold text-emerald-700' : 'font-semibold text-red-700'">
                {{ feedback[q.id].is_correct ? 'Correct' : 'Incorrect' }}
              </span>
              <span class="text-slate-600">
                · +{{ feedback[q.id].points_earned }} pts · total {{ feedback[q.id].total_points }}
              </span>
            </p>
            <div
              v-if="!feedback[q.id].is_correct && feedback[q.id].why_wrong"
              class="rounded-xl border border-amber-200 bg-amber-50/90 px-4 py-3 text-sm leading-relaxed text-amber-950"
            >
              <p class="text-xs font-semibold uppercase tracking-wide text-amber-800/90">Why this tripped you up</p>
              <p class="mt-1">{{ feedback[q.id].why_wrong }}</p>
            </div>
          </div>
        </article>
      </section>
    </template>
  </div>
</template>

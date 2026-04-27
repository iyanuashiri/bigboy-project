<script setup>
import { useRoute, useRouter } from 'vue-router'

const route = useRoute()
const router = useRouter()

const steps = [
  {
    title: 'Explore',
    body: 'Upload documents, run research, or import conversations. Your sources stay organized in categories and runs.',
    to: '/app/explore/chats',
    cta: 'Open Explore',
  },
  {
    title: 'Promote to a subject',
    body: 'Turn a category or research run into a subject with topics, bites, and starter quizzes.',
    to: '/app/explore/chats',
    cta: 'Go to documents',
  },
  {
    title: 'Learn & review',
    body: 'Follow the lesson path bite by bite. Finished bites enter the Review queue for a light spaced schedule.',
    to: '/app/subjects/mine',
    cta: 'My subjects',
  },
  {
    title: 'Quizzes & goals',
    body: 'Check quizzes after topics. Set a weekly bite goal on a subject page to nudge steady progress.',
    to: '/app/quizzes',
    cta: 'Quizzes',
  },
]

function finish() {
  localStorage.setItem('onboardingDone', '1')
  const next = typeof route.query.next === 'string' && route.query.next.startsWith('/app') ? route.query.next : '/app/dashboard'
  router.replace(next)
}

function skipToDashboard() {
  localStorage.setItem('onboardingDone', '1')
  router.replace('/app/dashboard')
}
</script>

<template>
  <div class="mx-auto max-w-3xl">
    <p class="text-xs font-semibold uppercase tracking-wide text-indigo-600">Welcome</p>
    <h1 class="mt-2 text-3xl font-bold tracking-tight text-slate-900">How bigboy fits together</h1>
    <p class="mt-3 text-slate-600">
      A quick map of the main flows. You can reopen this tour anytime from the dashboard card (clear the
      <code class="rounded bg-slate-100 px-1 text-xs">onboardingDone</code> flag in devtools if you want to see it again).
    </p>

    <ol class="mt-10 space-y-5">
      <li
        v-for="(s, i) in steps"
        :key="s.title"
        class="flex gap-4 rounded-2xl border border-slate-200 bg-white p-5 shadow-sm"
      >
        <span
          class="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-indigo-600 text-sm font-bold text-white"
        >
          {{ i + 1 }}
        </span>
        <div class="min-w-0 flex-1">
          <h2 class="font-semibold text-slate-900">{{ s.title }}</h2>
          <p class="mt-1 text-sm leading-relaxed text-slate-600">{{ s.body }}</p>
          <RouterLink
            :to="s.to"
            class="mt-3 inline-flex text-sm font-semibold text-indigo-700 hover:text-indigo-900"
          >
            {{ s.cta }} →
          </RouterLink>
        </div>
      </li>
    </ol>

    <div class="mt-10 flex flex-wrap gap-3">
      <button
        type="button"
        class="rounded-xl bg-slate-900 px-5 py-2.5 text-sm font-semibold text-white shadow hover:bg-slate-800"
        @click="finish"
      >
        Got it — continue
      </button>
      <button
        type="button"
        class="rounded-xl border border-slate-300 px-5 py-2.5 text-sm font-medium text-slate-800 hover:bg-slate-50"
        @click="skipToDashboard"
      >
        Skip to dashboard
      </button>
    </div>
  </div>
</template>

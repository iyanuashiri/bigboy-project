<script setup>
import { onMounted, ref } from 'vue'
import { RouterLink } from 'vue-router'
import api, { formatApiError } from '@/api.js'
import { REVIEW_DEMO_DUE } from '@/constants/reviewDemoDue.js'

const enrolledCount = ref(0)
const catalogPeek = ref([])
const error = ref('')
/** null = could not load; when loaded and empty, matches Review queue preview count. */
const reviewDueCount = ref(null)

onMounted(async () => {
  try {
    const [mine, catalog, due] = await Promise.all([
      api.getSubjects('enrolled'),
      api.getSubjects('catalog').catch(() => []),
      api.getReviewDue().then((d) => d).catch(() => null),
    ])
    enrolledCount.value = Array.isArray(mine) ? mine.length : 0
    catalogPeek.value = Array.isArray(catalog) ? catalog.slice(0, 3) : []
    if (due === null) {
      reviewDueCount.value = null
    } else {
      const n = Array.isArray(due) ? due.length : 0
      reviewDueCount.value = n > 0 ? n : REVIEW_DEMO_DUE.length
    }
  } catch (e) {
    error.value = formatApiError(e)
  }
})
</script>

<template>
  <div class="mx-auto max-w-4xl space-y-8">
    <div>
      <p class="text-sm font-medium uppercase tracking-wide text-indigo-600">Overview</p>
      <h2 class="mt-1 text-2xl font-bold tracking-tight text-slate-900">Your workspace</h2>
      <p class="mt-2 max-w-2xl text-slate-600">
        Jump into subjects and quizzes, or use Explore to bring in documents, research, and assistant conversations —
        then turn what you collect into structured subjects when you are ready.
      </p>
      <p v-if="error" class="mt-3 text-sm text-red-600">{{ error }}</p>
    </div>

    <div
      v-if="enrolledCount === 0 && !error"
      class="rounded-2xl border border-indigo-100 bg-indigo-50/60 px-5 py-4 text-sm text-indigo-950"
    >
      <p class="font-semibold">First time here?</p>
      <p class="mt-1 text-indigo-900/90">
        We show a short onboarding once. To see it again, remove
        <code class="rounded bg-white/80 px-1">onboardingDone</code> from localStorage and refresh.
      </p>
    </div>

    <div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
      <RouterLink
        to="/app/explore/chats"
        class="group rounded-2xl border border-slate-200 bg-white p-6 shadow-sm transition hover:border-indigo-200 hover:shadow-md"
      >
        <div class="flex h-10 w-10 items-center justify-center rounded-xl bg-indigo-50 text-lg">📄</div>
        <h3 class="mt-4 font-semibold text-slate-900 group-hover:text-indigo-700">Explore</h3>
        <p class="mt-2 text-sm text-slate-600">Documents, research runs, and conversation imports.</p>
      </RouterLink>

      <RouterLink
        to="/app/subjects/mine"
        class="group rounded-2xl border border-slate-200 bg-white p-6 shadow-sm transition hover:border-emerald-200 hover:shadow-md"
      >
        <div class="flex h-10 w-10 items-center justify-center rounded-xl bg-emerald-50 text-lg">📚</div>
        <h3 class="mt-4 font-semibold text-slate-900 group-hover:text-emerald-700">Subjects</h3>
        <p class="mt-2 text-sm text-slate-600">
          {{ enrolledCount }} enrolled — open topics, bites, and lessons.
        </p>
      </RouterLink>

      <RouterLink
        to="/app/quizzes"
        class="group rounded-2xl border border-slate-200 bg-white p-6 shadow-sm transition hover:border-amber-200 hover:shadow-md"
      >
        <div class="flex h-10 w-10 items-center justify-center rounded-xl bg-amber-50 text-lg">✓</div>
        <h3 class="mt-4 font-semibold text-slate-900 group-hover:text-amber-800">Quizzes</h3>
        <p class="mt-2 text-sm text-slate-600">Practice quizzes for your enrolled subjects.</p>
      </RouterLink>
    </div>

    <div class="grid gap-4 sm:grid-cols-2">
      <RouterLink
        :to="{ name: 'review' }"
        class="group rounded-2xl border border-slate-200 bg-white p-6 shadow-sm transition hover:border-violet-200 hover:shadow-md"
      >
        <div class="flex h-10 w-10 items-center justify-center rounded-xl bg-violet-50 text-lg">↻</div>
        <h3 class="mt-4 font-semibold text-slate-900 group-hover:text-violet-800">Spaced review</h3>
        <p class="mt-2 text-sm text-slate-600">
          <span v-if="reviewDueCount != null">{{ reviewDueCount }} bite(s) due now.</span>
          <span v-else>Light repeats after you finish lesson bites.</span>
        </p>
      </RouterLink>
    </div>

    <div v-if="catalogPeek.length" class="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
      <div class="flex items-center justify-between gap-4">
        <h3 class="font-semibold text-slate-900">From the catalog</h3>
        <RouterLink
          to="/app/subjects/catalog"
          class="text-sm font-medium text-indigo-600 hover:text-indigo-800"
        >
          Browse all →
        </RouterLink>
      </div>
      <ul class="mt-4 divide-y divide-slate-100">
        <li v-for="s in catalogPeek" :key="s.id" class="flex justify-between gap-4 py-3 text-sm">
          <span class="font-medium text-slate-800">{{ s.name }}</span>
          <span class="truncate text-slate-500">{{ s.description }}</span>
        </li>
      </ul>
    </div>
  </div>
</template>

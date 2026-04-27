<script setup>
import { computed } from 'vue'
import { RouterLink, RouterView, useRoute, useRouter } from 'vue-router'
import api from '@/api.js'

const route = useRoute()
const router = useRouter()

const mainNav = [
  { name: 'dashboard', label: 'Dashboard', to: '/app/dashboard', icon: '◆' },
  { name: 'explore', label: 'Explore', to: '/app/explore/chats', match: 'explore' },
  { name: 'subjects-mine', label: 'Subjects', to: '/app/subjects/mine', match: 'subjects' },
  { name: 'review', label: 'Review', to: '/app/review', match: 'review', icon: '↻' },
  { name: 'quizzes', label: 'Quizzes', to: '/app/quizzes', match: 'quizzes', icon: '◇' },
]

function navActive(item) {
  if (item.match === 'explore') return route.path.startsWith('/app/explore')
  if (item.match === 'subjects') return route.path.startsWith('/app/subjects')
  if (item.match === 'review') return route.path.startsWith('/app/review')
  if (item.match === 'quizzes') return route.path.startsWith('/app/quizzes')
  return route.name === item.name || route.path === item.to
}

const showLearningStrip = computed(() => {
  const p = route.path
  return p.startsWith('/app/subjects') || p.startsWith('/app/review') || p.startsWith('/app/quizzes')
})

async function logout() {
  try {
    await api.logout()
  } catch {
    /* ignore */
  }
  localStorage.removeItem('authToken')
  await router.push({ name: 'login' })
}
</script>

<template>
  <div class="flex min-h-screen bg-slate-100 text-slate-900">
    <aside
      class="flex w-60 shrink-0 flex-col border-r border-slate-200/80 bg-[#0f172a] text-slate-200 shadow-xl"
    >
      <div class="border-b border-white/10 px-4 py-5">
        <RouterLink to="/app/dashboard" class="block font-semibold tracking-tight text-white">
          bigboy
        </RouterLink>
        <p class="mt-1 text-xs text-slate-400">Learn · Explore · Create</p>
      </div>

      <nav class="flex flex-1 flex-col gap-0.5 px-2 py-4">
        <RouterLink
          v-for="item in mainNav"
          :key="item.to"
          :to="item.to"
          class="flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors"
          :class="
            navActive(item)
              ? 'bg-white/10 text-white'
              : 'text-slate-400 hover:bg-white/5 hover:text-slate-100'
          "
        >
          <span class="w-5 text-center text-xs opacity-80">{{ item.icon || '·' }}</span>
          {{ item.label }}
        </RouterLink>
      </nav>

      <div class="border-t border-white/10 p-3">
        <button
          type="button"
          class="w-full rounded-lg border border-white/15 px-3 py-2 text-left text-sm text-slate-300 hover:bg-white/5 hover:text-white"
          @click="logout"
        >
          Log out
        </button>
      </div>
    </aside>

    <div class="flex min-w-0 flex-1 flex-col">
      <div
        v-if="showLearningStrip"
        class="border-b border-slate-200/90 bg-gradient-to-r from-violet-50/90 via-white to-emerald-50/80 px-6 py-2.5 sm:px-10"
      >
        <nav class="mx-auto flex max-w-5xl flex-wrap items-center gap-x-6 gap-y-1 text-xs font-medium text-slate-600">
          <span class="text-slate-400">Learning strip</span>
          <RouterLink to="/app/subjects/mine" class="hover:text-slate-900">Subjects</RouterLink>
          <RouterLink :to="{ name: 'review' }" class="hover:text-violet-800">Spaced review</RouterLink>
          <RouterLink to="/app/quizzes" class="hover:text-slate-900">Quizzes</RouterLink>
          <RouterLink to="/app/explore/chats" class="hover:text-slate-900">Explore sources</RouterLink>
        </nav>
      </div>
      <main class="flex-1 overflow-auto px-6 py-8 sm:px-10">
        <RouterView />
      </main>
    </div>
  </div>
</template>

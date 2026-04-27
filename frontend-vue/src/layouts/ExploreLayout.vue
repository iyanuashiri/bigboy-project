<script setup>
import { RouterLink, RouterView, useRoute } from 'vue-router'

const route = useRoute()

const tabs = [
  { name: 'explore-chats', label: 'Documents', to: '/app/explore/chats' },
  { name: 'explore-research', label: 'Research', to: '/app/explore/research' },
  { name: 'explore-mcp', label: 'Conversation imports', to: '/app/explore/mcp' },
]

function tabActive(to) {
  if (route.path === to) return true
  return route.path.startsWith(`${to}/`)
}
</script>

<template>
  <div class="mx-auto max-w-5xl">
    <div class="mb-6">
      <h2 class="text-base font-semibold text-slate-500">Explore</h2>
      <p class="mt-1 text-sm text-slate-600">
        Chat over your documents, run deeper research briefs, and pull in assistant threads as imports — each can feed
        subjects, topics, and quizzes when you promote them.
      </p>
      <nav class="mt-4 flex flex-wrap gap-2 border-b border-slate-200 pb-px">
        <RouterLink
          v-for="t in tabs"
          :key="t.to"
          :to="t.to"
          class="rounded-t-lg px-4 py-2 text-sm font-medium transition-colors"
          :class="
            tabActive(t.to)
              ? 'border border-b-0 border-slate-200 bg-white text-slate-900'
              : 'text-slate-600 hover:text-slate-900'
          "
        >
          {{ t.label }}
        </RouterLink>
      </nav>
    </div>
    <RouterView />
  </div>
</template>

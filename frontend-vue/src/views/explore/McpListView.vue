<script setup>
import { computed, onActivated, onMounted, ref } from 'vue'
import { RouterLink } from 'vue-router'
import api, { formatApiError } from '@/api.js'
import { MCP_DEMO_IMPORTS } from '@/constants/mcpDemoImports.js'

const items = ref([])
const error = ref('')

const displayItems = computed(() => {
  if (items.value.length > 0) return items.value
  if (error.value) return []
  return MCP_DEMO_IMPORTS
})

async function refresh() {
  error.value = ''
  try {
    items.value = await api.getMcpImports()
  } catch (e) {
    error.value = formatApiError(e)
  }
}

onMounted(refresh)
onActivated(refresh)
</script>

<template>
  <div>
    <div class="flex flex-wrap items-center justify-between gap-4">
      <div>
        <h3 class="text-lg font-semibold text-slate-900">Conversation imports</h3>
        <p class="mt-1 text-sm text-slate-600">
          Threads you have pulled in from assistants or tools. Open one to read the transcript, then promote it into a
          subject when you want topics, bites, and quizzes built around it.
        </p>
      </div>
      <RouterLink
        :to="{ name: 'explore-mcp-new' }"
        class="inline-flex rounded-xl bg-indigo-600 px-4 py-2.5 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500"
      >
        + New import
      </RouterLink>
    </div>

    <p v-if="error" class="mt-4 rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">{{ error }}</p>

    <ul
      v-if="displayItems.length"
      class="mt-8 divide-y divide-slate-200 overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm"
    >
      <li v-for="m in displayItems" :key="String(m.id)">
        <RouterLink
          :to="{ name: 'explore-mcp-detail', params: { importId: String(m.id) } }"
          class="block px-5 py-4 transition hover:bg-slate-50"
        >
          <p class="font-medium text-slate-900">{{ m.title }}</p>
          <p class="text-xs text-slate-500">{{ m.status }} · {{ new Date(m.created_at).toLocaleString() }}</p>
        </RouterLink>
      </li>
    </ul>

    <div
      v-else-if="!error"
      class="mt-10 rounded-2xl border border-dashed border-slate-300 bg-slate-50/80 px-6 py-14 text-center text-slate-600"
    >
      No conversation imports yet.
      <RouterLink :to="{ name: 'explore-mcp-new' }" class="mt-2 block font-semibold text-indigo-600 hover:text-indigo-800">
        Add your first import →
      </RouterLink>
    </div>
  </div>
</template>

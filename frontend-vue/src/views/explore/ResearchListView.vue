<script setup>
import { onActivated, onMounted, ref } from 'vue'
import { RouterLink } from 'vue-router'
import api, { formatApiError } from '@/api.js'

const items = ref([])
const error = ref('')

async function refresh() {
  error.value = ''
  try {
    items.value = await api.getResearchRuns()
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
        <h3 class="text-lg font-semibold text-slate-900">Research runs</h3>
        <p class="mt-1 text-sm text-slate-600">
          Each run is stored on the API. Open one to review blocks and promote to a subject.
        </p>
      </div>
      <RouterLink
        :to="{ name: 'explore-research-new' }"
        class="inline-flex rounded-xl bg-indigo-600 px-4 py-2.5 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500"
      >
        + New research
      </RouterLink>
    </div>

    <p v-if="error" class="mt-4 rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">{{ error }}</p>

    <ul
      v-if="items.length"
      class="mt-8 divide-y divide-slate-200 overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm"
    >
      <li v-for="r in items" :key="r.id">
        <RouterLink
          :to="{ name: 'explore-research-detail', params: { researchId: String(r.id) } }"
          class="block px-5 py-4 transition hover:bg-slate-50"
        >
          <p class="font-medium text-slate-900">{{ r.query }}</p>
          <p class="text-xs text-slate-500">{{ r.status }} · {{ new Date(r.created_at).toLocaleString() }}</p>
        </RouterLink>
      </li>
    </ul>

    <div
      v-else-if="!error"
      class="mt-10 rounded-2xl border border-dashed border-slate-300 bg-slate-50/80 px-6 py-14 text-center text-slate-600"
    >
      No research yet.
      <RouterLink :to="{ name: 'explore-research-new' }" class="mt-2 block font-semibold text-indigo-600 hover:text-indigo-800">
        Start a research run →
      </RouterLink>
    </div>
  </div>
</template>

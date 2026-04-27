<script setup>
import { onActivated, onMounted, ref } from 'vue'
import { RouterLink } from 'vue-router'
import api, { formatApiError } from '@/api.js'

const items = ref([])
const error = ref('')

async function refresh() {
  error.value = ''
  try {
    items.value = await api.getDocumentCategories()
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
        <h3 class="text-lg font-semibold text-slate-900">Document categories</h3>
        <p class="mt-1 text-sm text-slate-600">
          Each category groups uploaded documents. Open one to ask questions over your files, then promote to a subject
          when you want a lesson path built from what you found.
        </p>
      </div>
      <RouterLink
        :to="{ name: 'explore-chats-new' }"
        class="inline-flex items-center gap-2 rounded-xl bg-indigo-600 px-4 py-2.5 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500"
      >
        + Add category
      </RouterLink>
    </div>

    <p v-if="error" class="mt-4 rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">{{ error }}</p>

    <ul
      v-if="items.length"
      class="mt-8 divide-y divide-slate-200 overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm"
    >
      <li v-for="c in items" :key="c.id">
        <RouterLink
          :to="{ name: 'explore-chats-detail', params: { categoryId: String(c.id) } }"
          class="flex items-center justify-between gap-4 px-5 py-4 transition hover:bg-slate-50"
        >
          <div>
            <p class="font-medium text-slate-900">{{ c.name }}</p>
            <p class="text-xs text-slate-500">
              {{ c.document_count ?? 0 }} file(s) · {{ new Date(c.created_at).toLocaleString() }}
            </p>
          </div>
          <span class="text-slate-400">→</span>
        </RouterLink>
      </li>
    </ul>

    <div
      v-else-if="!error"
      class="mt-10 rounded-2xl border border-dashed border-slate-300 bg-slate-50/80 px-6 py-14 text-center"
    >
      <p class="text-slate-600">No categories yet.</p>
      <RouterLink
        :to="{ name: 'explore-chats-new' }"
        class="mt-4 inline-block text-sm font-semibold text-indigo-600 hover:text-indigo-800"
      >
        Create your first category →
      </RouterLink>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { RouterLink, useRouter } from 'vue-router'
import api, { formatApiError } from '@/api.js'

const router = useRouter()
const title = ref('')
const body = ref('')
const error = ref('')
const loading = ref(false)

async function submit() {
  error.value = ''
  loading.value = true
  try {
    const transcript = body.value.split('\n').filter(Boolean).join('\n')
    const row = await api.createMcpImport({
      title: title.value.trim() || 'Imported conversation',
      transcript,
    })
    await router.push({ name: 'explore-mcp-detail', params: { importId: String(row.id) } })
  } catch (e) {
    error.value = formatApiError(e)
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="mx-auto max-w-2xl">
    <RouterLink :to="{ name: 'explore-mcp' }" class="text-sm font-medium text-indigo-600 hover:text-indigo-800">
      ← Conversation imports
    </RouterLink>
    <h3 class="mt-4 text-xl font-semibold text-slate-900">New conversation import</h3>
    <p class="mt-2 text-sm text-slate-600">
      Paste a title and the transcript (one line per message is fine). You can open it afterward and promote it into a
      subject when you are ready to structure it.
    </p>
    <form class="mt-8 space-y-4" @submit.prevent="submit">
      <input
        v-model="title"
        type="text"
        class="w-full rounded-xl border border-slate-300 px-4 py-2.5 text-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
        placeholder="Conversation title"
      />
      <textarea
        v-model="body"
        rows="8"
        class="w-full rounded-2xl border border-slate-300 px-4 py-3 text-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
        placeholder="Paste the conversation here…"
      />
      <p v-if="error" class="text-sm text-red-600">{{ error }}</p>
      <button
        type="submit"
        :disabled="loading"
        class="rounded-xl bg-indigo-600 px-5 py-3 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500 disabled:opacity-50"
      >
        {{ loading ? 'Saving…' : 'Save import' }}
      </button>
    </form>
  </div>
</template>

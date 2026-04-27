<script setup>
import { ref } from 'vue'
import { RouterLink, useRouter } from 'vue-router'
import api, { formatApiError } from '@/api.js'

const router = useRouter()
const description = ref('')
const fileNames = ref([])
const error = ref('')
const loading = ref(false)

function onFiles(e) {
  const files = e.target.files
  fileNames.value = files ? Array.from(files).map((f) => f.name) : []
}

async function submit() {
  error.value = ''
  const files = document.getElementById('fl')?.files
  if (!files || !files.length) {
    error.value = 'Choose at least one document to upload.'
    return
  }
  loading.value = true
  try {
    const cat = await api.createDocumentCategory({
      description: description.value.trim(),
    })
    for (const f of Array.from(files)) {
      await api.uploadCategoryDocument(cat.id, f, f.name)
    }
    const fresh = await api.getDocumentCategory(cat.id)
    await router.push({ name: 'explore-chats-detail', params: { categoryId: String(fresh.id) } })
  } catch (e) {
    error.value = formatApiError(e)
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="mx-auto max-w-lg">
    <RouterLink :to="{ name: 'explore-chats' }" class="text-sm font-medium text-indigo-600 hover:text-indigo-800">
      ← Categories
    </RouterLink>
    <h3 class="mt-4 text-xl font-semibold text-slate-900">New document category</h3>
    <p class="mt-2 text-sm text-slate-600">
      Upload your files. The category title is generated automatically from the start of the extracted text (not the
      full files), so naming stays fast even with many uploads. Optional note below is passed to the model as a hint
      only.
    </p>

    <form class="mt-8 space-y-5" @submit.prevent="submit">
      <div>
        <label class="block text-sm font-medium text-slate-700" for="desc">Optional note for naming</label>
        <textarea
          id="desc"
          v-model="description"
          rows="2"
          class="mt-1 w-full rounded-xl border border-slate-300 px-4 py-2.5 text-sm shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
          placeholder="e.g. MBA strategy readings, Week 3 — helps the title match your intent"
        />
      </div>
      <div>
        <label class="block text-sm font-medium text-slate-700" for="fl">Documents</label>
        <input
          id="fl"
          type="file"
          multiple
          required
          class="mt-2 block w-full text-sm text-slate-600 file:mr-4 file:rounded-lg file:border-0 file:bg-indigo-50 file:px-4 file:py-2 file:text-sm file:font-semibold file:text-indigo-700 hover:file:bg-indigo-100"
          @change="onFiles"
        />
        <p v-if="fileNames.length" class="mt-2 text-xs text-slate-500">{{ fileNames.join(', ') }}</p>
      </div>
      <p v-if="error" class="text-sm text-red-600">{{ error }}</p>
      <button
        type="submit"
        :disabled="loading"
        class="w-full rounded-xl bg-indigo-600 py-3 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500 disabled:opacity-50"
      >
        {{ loading ? 'Uploading & naming…' : 'Upload & open chat' }}
      </button>
    </form>
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'
import api, { formatApiError } from '@/api.js'

const route = useRoute()
const router = useRouter()
const categoryId = computed(() => Number(route.params.categoryId))

const category = ref(null)
const sessionId = ref(null)
const messages = ref([])
const draft = ref('')
const error = ref('')
const promoteError = ref('')

async function loadCategory() {
  category.value = await api.getDocumentCategory(categoryId.value)
}

async function ensureSession() {
  const sessions = await api.getCategoryChatSessions(categoryId.value)
  if (!sessions.length) {
    const s = await api.createCategoryChatSession(categoryId.value, { title: '' })
    sessionId.value = s.id
  } else {
    sessionId.value = sessions[0].id
  }
}

async function loadMessages() {
  if (!sessionId.value) return
  messages.value = await api.getChatSessionMessages(sessionId.value)
}

async function load() {
  error.value = ''
  try {
    await loadCategory()
    await ensureSession()
    await loadMessages()
  } catch (e) {
    error.value = formatApiError(e)
    category.value = null
  }
}

async function send() {
  const t = draft.value.trim()
  if (!t || !sessionId.value) return
  promoteError.value = ''
  try {
    draft.value = ''
    await api.createChatSessionMessage(sessionId.value, { role: 'user', content: t })
    await loadMessages()
  } catch (e) {
    error.value = formatApiError(e)
  }
}

async function promote() {
  promoteError.value = ''
  const name = window.prompt('New subject name', category.value?.name || 'New subject')
  if (!name) return
  const desc =
    window.prompt('Subject description', `Created from document category “${category.value?.name}”.`) || ''
  try {
    await api.promoteToSubject({
      source_model: 'documentcategory',
      source_id: categoryId.value,
      subject_name: name.slice(0, 100),
      subject_description: desc,
    })
    await router.push({ name: 'subjects-mine' })
  } catch (e) {
    promoteError.value = formatApiError(e)
  }
}

function docStatusLine(doc) {
  const st = doc.status || ''
  const err = doc.processing_error ? ` — ${doc.processing_error}` : ''
  return `${doc.original_name} (${st})${err}`
}

onMounted(load)
watch(categoryId, load)
</script>

<template>
  <div class="mx-auto flex max-w-3xl flex-col gap-6">
    <div>
      <RouterLink :to="{ name: 'explore-chats' }" class="text-sm font-medium text-indigo-600 hover:text-indigo-800">
        ← Categories
      </RouterLink>
      <h3 class="mt-3 text-xl font-semibold text-slate-900">
        {{ category?.name || 'Category' }}
      </h3>
      <p v-if="category?.description" class="mt-1 text-sm text-slate-600">{{ category.description }}</p>
      <ul v-if="category?.documents?.length" class="mt-2 list-inside list-disc text-xs text-slate-500">
        <li v-for="d in category.documents" :key="d.id">{{ docStatusLine(d) }}</li>
      </ul>
      <p v-else class="mt-1 text-xs text-slate-500">No documents — add files when creating a category.</p>
    </div>

    <p v-if="error" class="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">{{ error }}</p>

    <template v-else-if="category">
      <div class="flex flex-wrap items-center gap-2">
        <button
          type="button"
          class="rounded-lg bg-slate-900 px-4 py-2 text-sm font-semibold text-white hover:bg-slate-800"
          @click="promote"
        >
          Promote to subject
        </button>
        <span class="text-xs text-slate-500">Creates a Subject, enrolls you, and records SourcePromotion.</span>
      </div>
      <p v-if="promoteError" class="text-sm text-red-600">{{ promoteError }}</p>

      <div class="flex max-h-[420px] flex-col overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
        <div class="flex-1 space-y-3 overflow-y-auto p-4">
          <div
            v-for="m in messages"
            :key="m.id"
            class="flex"
            :class="m.role === 'user' ? 'justify-end' : 'justify-start'"
          >
            <div
              class="max-w-[85%] rounded-2xl px-4 py-2 text-sm whitespace-pre-wrap"
              :class="
                m.role === 'user'
                  ? 'bg-indigo-600 text-white'
                  : 'border border-slate-200 bg-slate-50 text-slate-800'
              "
            >
              {{ m.content }}
            </div>
          </div>
          <p v-if="!messages.length" class="text-center text-sm text-slate-500">Send a message to start.</p>
        </div>
        <form class="flex gap-2 border-t border-slate-100 p-3" @submit.prevent="send">
          <input
            v-model="draft"
            type="text"
            class="min-w-0 flex-1 rounded-xl border border-slate-300 px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
            placeholder="Ask about your documents…"
          />
          <button
            type="submit"
            class="rounded-xl bg-indigo-600 px-4 py-2 text-sm font-semibold text-white hover:bg-indigo-500"
          >
            Send
          </button>
        </form>
      </div>
    </template>
  </div>
</template>

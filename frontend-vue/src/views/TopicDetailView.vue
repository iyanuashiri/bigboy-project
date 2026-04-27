<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { RouterLink, useRoute } from 'vue-router'
import api, { formatApiError } from '@/api.js'

const route = useRoute()
const topic = ref(null)
const error = ref('')
const loading = ref(true)
const draft = ref({})
const saving = ref(new Set())
const regenerating = ref(false)

const topicId = computed(() => Number(route.params.topicId ?? route.params.id))
const subjectIdParam = computed(() =>
  route.params.subjectId != null ? Number(route.params.subjectId) : null,
)

const subjectId = computed(() => subjectIdParam.value ?? topic.value?.subject?.id ?? null)

function syncDraft() {
  const d = {}
  for (const b of topic.value?.topic_bites || []) {
    d[b.id] = { name: b.name, bite: b.bite, is_locked: !!b.is_locked }
  }
  draft.value = d
}

async function load() {
  loading.value = true
  error.value = ''
  try {
    topic.value = await api.getTopic(topicId.value)
    syncDraft()
  } catch (e) {
    error.value = formatApiError(e)
  } finally {
    loading.value = false
  }
}

async function saveBite(biteId) {
  const row = draft.value[biteId]
  if (!row) return
  saving.value = new Set(saving.value).add(biteId)
  error.value = ''
  try {
    await api.patchBite(biteId, {
      name: row.name,
      bite: row.bite,
      is_locked: row.is_locked,
    })
    await load()
  } catch (e) {
    error.value = formatApiError(e)
  } finally {
    const n = new Set(saving.value)
    n.delete(biteId)
    saving.value = n
  }
}

async function regenerateBites() {
  if (!window.confirm('Regenerate AI bites for this topic? Locked bites stay; unlocked ones are replaced.')) return
  regenerating.value = true
  error.value = ''
  try {
    await api.regenerateTopicBites(topicId.value)
    await load()
  } catch (e) {
    error.value = formatApiError(e)
  } finally {
    regenerating.value = false
  }
}

onMounted(load)
watch(topicId, load)
</script>

<template>
  <div class="mx-auto max-w-3xl">
    <RouterLink
      v-if="subjectId"
      :to="{ name: 'subject', params: { id: subjectId } }"
      class="text-sm font-medium text-slate-600 hover:text-slate-900"
    >
      ← Subject
    </RouterLink>

    <p v-if="loading" class="mt-8 text-sm text-slate-500">Loading…</p>
    <p v-else-if="error" class="mt-8 rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">{{ error }}</p>

    <template v-else-if="topic">
      <div class="mt-6 flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 class="text-2xl font-semibold text-slate-900">{{ topic.name }}</h1>
          <p class="mt-2 text-slate-600">{{ topic.description }}</p>
        </div>
        <button
          type="button"
          :disabled="regenerating"
          class="rounded-lg border border-amber-300 bg-amber-50 px-3 py-2 text-sm font-semibold text-amber-950 shadow-sm hover:bg-amber-100 disabled:opacity-50"
          @click="regenerateBites"
        >
          {{ regenerating ? 'Regenerating…' : 'Regenerate bites' }}
        </button>
      </div>

      <div class="mt-4 rounded-xl border border-slate-200 bg-slate-50/80 px-4 py-3 text-xs text-slate-600">
        <strong class="text-slate-800">Human in the loop:</strong> edit text below, toggle <em>Lock</em> to keep a bite
        when you regenerate. Unlocked bites are removed and rebuilt from the topic content.
      </div>

      <div class="mt-6 whitespace-pre-wrap rounded-xl border border-slate-200 bg-white p-4 text-sm text-slate-800 shadow-sm">
        {{ topic.content }}
      </div>

      <aside
        v-if="subjectId"
        class="mt-8 rounded-2xl border border-violet-200 bg-gradient-to-br from-violet-50 to-white p-5 shadow-sm"
      >
        <p class="text-sm font-semibold text-violet-900">Topic quiz</p>
        <p class="mt-1 text-sm text-violet-900/80">Open quizzes filtered to this subject from the subject page.</p>
        <RouterLink
          :to="{ name: 'quizzes', query: { subject: subjectId } }"
          class="mt-3 inline-flex rounded-lg bg-violet-700 px-4 py-2 text-sm font-semibold text-white hover:bg-violet-600"
        >
          Quizzes for subject
        </RouterLink>
      </aside>

      <div class="mt-8 flex flex-wrap gap-2">
        <RouterLink
          v-if="subjectId"
          :to="{ name: 'lesson', params: { id: subjectId } }"
          class="rounded-md border border-slate-300 px-3 py-1.5 text-sm font-medium text-slate-800 hover:bg-slate-50"
        >
          Continue lesson path
        </RouterLink>
      </div>

      <h2 class="mt-12 text-lg font-semibold text-slate-900">Bites</h2>
      <p v-if="!(topic.topic_bites || []).length" class="mt-3 rounded-lg border border-dashed border-slate-200 bg-slate-50 px-4 py-8 text-center text-sm text-slate-600">
        No bites yet. Use “Regenerate bites” to generate from the topic content.
      </p>
      <ul v-else class="mt-4 space-y-6">
        <li
          v-for="b in topic.topic_bites"
          :key="b.id"
          class="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm ring-1 ring-slate-900/5"
        >
          <template v-if="draft[b.id]">
          <label class="block text-xs font-medium uppercase tracking-wide text-slate-500">Title</label>
          <input
            v-model="draft[b.id].name"
            type="text"
            class="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
          />
          <label class="mt-3 block text-xs font-medium uppercase tracking-wide text-slate-500">Body</label>
          <textarea
            v-model="draft[b.id].bite"
            rows="5"
            class="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
          />
          <label class="mt-3 flex items-center gap-2 text-sm text-slate-700">
            <input v-model="draft[b.id].is_locked" type="checkbox" class="rounded border-slate-400" />
            Lock this bite (kept on regenerate)
          </label>
          <button
            type="button"
            :disabled="saving.has(b.id)"
            class="mt-4 rounded-lg bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-800 disabled:opacity-50"
            @click="saveBite(b.id)"
          >
            {{ saving.has(b.id) ? 'Saving…' : 'Save changes' }}
          </button>
          </template>
        </li>
      </ul>
    </template>
  </div>
</template>

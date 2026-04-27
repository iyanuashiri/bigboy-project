<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'
import api, { formatApiError } from '@/api.js'

const route = useRoute()
const router = useRouter()
const researchId = computed(() => Number(route.params.researchId))

const row = ref(null)
const error = ref('')
const promoteError = ref('')

async function load() {
  error.value = ''
  try {
    row.value = await api.getResearchRun(researchId.value)
  } catch (e) {
    error.value = formatApiError(e)
    row.value = null
  }
}

async function promote() {
  promoteError.value = ''
  const name = window.prompt('New subject name', 'New subject from research')
  if (!name) return
  const desc =
    window.prompt('Subject description', `Created from research run #${researchId.value}.`) || ''
  try {
    await api.promoteToSubject({
      source_model: 'researchrun',
      source_id: researchId.value,
      subject_name: name.slice(0, 100),
      subject_description: desc,
    })
    await router.push({ name: 'subjects-mine' })
  } catch (e) {
    promoteError.value = formatApiError(e)
  }
}

onMounted(load)
watch(researchId, load)
</script>

<template>
  <div class="mx-auto max-w-3xl">
    <RouterLink :to="{ name: 'explore-research' }" class="text-sm font-medium text-indigo-600 hover:text-indigo-800">
      ← Research list
    </RouterLink>

    <p v-if="error" class="mt-8 rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">{{ error }}</p>

    <template v-else-if="row">
      <h3 class="mt-4 text-xl font-semibold text-slate-900">{{ row.query }}</h3>
      <p class="mt-1 text-xs text-slate-500">{{ row.status }} · {{ new Date(row.created_at).toLocaleString() }}</p>

      <div class="mt-6 flex flex-wrap gap-2">
        <button
          type="button"
          class="rounded-lg bg-slate-900 px-4 py-2 text-sm font-semibold text-white hover:bg-slate-800"
          @click="promote"
        >
          Promote to subject
        </button>
      </div>
      <p v-if="promoteError" class="mt-2 text-sm text-red-600">{{ promoteError }}</p>

      <p
        v-if="row.status === 'failed' && row.error_message"
        class="mt-4 rounded-md bg-amber-50 px-3 py-2 text-sm text-amber-900 whitespace-pre-wrap"
      >
        {{ row.error_message }}
      </p>

      <div class="mt-8 space-y-4">
        <article
          v-for="(b, i) in row.result_blocks || []"
          :key="i"
          class="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm"
        >
          <h4 class="font-semibold text-slate-900">{{ b.title }}</h4>
          <p class="mt-2 text-sm leading-relaxed text-slate-600 whitespace-pre-wrap">{{ b.body }}</p>
        </article>
      </div>
    </template>
  </div>
</template>

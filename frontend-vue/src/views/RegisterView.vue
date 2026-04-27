<script setup>
import { ref } from 'vue'
import { RouterLink, useRouter } from 'vue-router'
import api, { formatApiError } from '@/api.js'

const router = useRouter()

const first_name = ref('')
const last_name = ref('')
const phone_number = ref('')
const password = ref('')
const error = ref('')
const loading = ref(false)

async function onSubmit() {
  error.value = ''
  loading.value = true
  try {
    await api.register({
      first_name: first_name.value.trim(),
      last_name: last_name.value.trim(),
      phone_number: phone_number.value.trim(),
      password: password.value,
    })
    await router.push({ name: 'login', query: { registered: '1' } })
  } catch (e) {
    error.value = formatApiError(e)
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <main class="mx-auto max-w-md px-4 py-10">
    <h1 class="text-xl font-semibold text-slate-900">Create account</h1>
    <p class="mt-1 text-sm text-slate-600">After registering, sign in with the same phone number and password.</p>

    <form class="mt-6 space-y-4" @submit.prevent="onSubmit">
      <div class="grid grid-cols-2 gap-3">
        <div>
          <label class="block text-sm font-medium text-slate-700" for="fn">First name</label>
          <input
            id="fn"
            v-model="first_name"
            type="text"
            autocomplete="given-name"
            class="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm shadow-sm focus:border-slate-500 focus:outline-none focus:ring-1 focus:ring-slate-500"
            required
          />
        </div>
        <div>
          <label class="block text-sm font-medium text-slate-700" for="ln">Last name</label>
          <input
            id="ln"
            v-model="last_name"
            type="text"
            autocomplete="family-name"
            class="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm shadow-sm focus:border-slate-500 focus:outline-none focus:ring-1 focus:ring-slate-500"
            required
          />
        </div>
      </div>
      <div>
        <label class="block text-sm font-medium text-slate-700" for="phone">Phone number</label>
        <input
          id="phone"
          v-model="phone_number"
          type="text"
          autocomplete="tel"
          class="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm shadow-sm focus:border-slate-500 focus:outline-none focus:ring-1 focus:ring-slate-500"
          placeholder="+2348012345678"
          required
        />
      </div>
      <div>
        <label class="block text-sm font-medium text-slate-700" for="pw">Password</label>
        <input
          id="pw"
          v-model="password"
          type="password"
          autocomplete="new-password"
          class="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm shadow-sm focus:border-slate-500 focus:outline-none focus:ring-1 focus:ring-slate-500"
          required
        />
      </div>
      <p v-if="error" class="text-sm text-red-600">{{ error }}</p>
      <button
        type="submit"
        :disabled="loading"
        class="w-full rounded-lg bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-800 disabled:opacity-50"
      >
        {{ loading ? 'Creating…' : 'Create account' }}
      </button>
    </form>

    <p class="mt-6 text-center text-sm text-slate-600">
      Already have an account?
      <RouterLink to="/login" class="font-medium text-slate-900 underline">Log in</RouterLink>
    </p>
  </main>
</template>

<script setup>
import { computed, ref } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'
import api, { formatApiError } from '@/api.js'

const router = useRouter()
const route = useRoute()
const justRegistered = computed(() => route.query.registered === '1')

const phone_number = ref('')
const password = ref('')
const error = ref('')
const loading = ref(false)

async function onSubmit() {
  error.value = ''
  loading.value = true
  try {
    const data = await api.login({
      phone_number: phone_number.value.trim(),
      password: password.value,
    })
    localStorage.setItem('authToken', data.auth_token)
    const redirect = typeof route.query.redirect === 'string' ? route.query.redirect : ''
    await router.push(redirect || { name: 'dashboard' })
  } catch (e) {
    error.value = formatApiError(e)
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <main class="mx-auto max-w-md px-4 py-10">
    <h1 class="text-xl font-semibold text-slate-900">Log in</h1>
    <p class="mt-1 text-sm text-slate-600">Use the phone number and password you registered with.</p>
    <p
      v-if="justRegistered"
      class="mt-4 rounded-md bg-emerald-50 px-3 py-2 text-sm text-emerald-800"
    >
      Account created. Sign in below.
    </p>

    <form class="mt-6 space-y-4" @submit.prevent="onSubmit">
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
          autocomplete="current-password"
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
        {{ loading ? 'Signing in…' : 'Sign in' }}
      </button>
    </form>

    <p class="mt-6 text-center text-sm text-slate-600">
      No account?
      <RouterLink to="/register" class="font-medium text-slate-900 underline">Register</RouterLink>
    </p>
  </main>
</template>

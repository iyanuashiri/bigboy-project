<script setup>
import { RouterLink } from 'vue-router'
</script>

<template>
  <div class="min-h-screen bg-[#020617] text-slate-100">
    <div class="pointer-events-none absolute inset-0 overflow-hidden">
      <div
        class="absolute -left-40 top-0 h-[480px] w-[480px] rounded-full bg-indigo-600/25 blur-3xl"
      />
      <div
        class="absolute -right-20 bottom-0 h-[420px] w-[420px] rounded-full bg-violet-600/20 blur-3xl"
      />
      <div
        class="absolute left-1/2 top-1/3 h-64 w-64 -translate-x-1/2 rounded-full bg-cyan-500/10 blur-2xl"
      />
    </div>

    <header class="relative z-10 border-b border-white/5 bg-black/20 backdrop-blur-md">
      <div class="mx-auto flex max-w-6xl items-center justify-between px-6 py-5">
        <span class="text-lg font-semibold tracking-tight text-white">bigboy</span>
        <nav class="flex items-center gap-6 text-sm font-medium">
          <RouterLink to="/login" class="text-slate-300 hover:text-white">Log in</RouterLink>
          <RouterLink
            to="/register"
            class="rounded-full bg-white px-4 py-2 text-slate-900 shadow-sm hover:bg-slate-100"
          >
            Get started
          </RouterLink>
        </nav>
      </div>
    </header>

    <main class="relative z-10 mx-auto max-w-6xl px-6 pb-24 pt-16 sm:pt-24">
      <p
        class="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-3 py-1 text-xs font-medium uppercase tracking-wider text-indigo-200"
      >
        Capstone-ready layout
      </p>
      <h1
        class="mt-6 max-w-3xl text-4xl font-bold leading-tight tracking-tight text-white sm:text-5xl sm:leading-tight"
      >
        Learn from subjects, explore with AI, export into structure.
      </h1>
      <p class="mt-6 max-w-2xl text-lg leading-relaxed text-slate-400">
        A calm workspace for enrolled lessons and quizzes — plus Explore for document chat, research runs, and
        conversation imports so rabbit holes can land in structured subjects.
      </p>

      <div class="mt-10 flex flex-wrap gap-4">
        <RouterLink
          to="/register"
          class="inline-flex items-center justify-center rounded-full bg-indigo-500 px-8 py-3.5 text-sm font-semibold text-white shadow-lg shadow-indigo-500/30 transition hover:bg-indigo-400"
        >
          Create free account
        </RouterLink>
        <RouterLink
          to="/login"
          class="inline-flex items-center justify-center rounded-full border border-white/20 px-8 py-3.5 text-sm font-semibold text-white hover:bg-white/5"
        >
          I already have an account
        </RouterLink>
      </div>

      <div class="mt-24 grid gap-6 sm:grid-cols-3">
        <div class="rounded-2xl border border-white/10 bg-white/[0.04] p-6 backdrop-blur-sm">
          <div class="text-2xl">📚</div>
          <h2 class="mt-4 font-semibold text-white">Subjects & bites</h2>
          <p class="mt-2 text-sm leading-relaxed text-slate-400">
            Progress through topics and bites, with quizzes woven into the path.
          </p>
        </div>
        <div class="rounded-2xl border border-white/10 bg-white/[0.04] p-6 backdrop-blur-sm">
          <div class="text-2xl">🔭</div>
          <h2 class="mt-4 font-semibold text-white">Explore</h2>
          <p class="mt-2 text-sm leading-relaxed text-slate-400">
            Documents, research runs, and imported threads — each feeding your curriculum pipeline.
          </p>
        </div>
        <div class="rounded-2xl border border-white/10 bg-white/[0.04] p-6 backdrop-blur-sm">
          <div class="text-2xl">✓</div>
          <h2 class="mt-4 font-semibold text-white">Quizzes</h2>
          <p class="mt-2 text-sm leading-relaxed text-slate-400">
            Practice mode tied to the subjects you are enrolled in.
          </p>
        </div>
      </div>
    </main>

    <footer class="relative z-10 border-t border-white/5 py-8 text-center text-xs text-slate-500">
      bigboy · Vue + Django
    </footer>
  </div>
</template>

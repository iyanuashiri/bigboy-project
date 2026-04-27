import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    { path: '/', name: 'home', component: HomeView },
    {
      path: '/login',
      name: 'login',
      component: () => import('../views/LoginView.vue'),
      meta: { guestOnly: true },
    },
    {
      path: '/register',
      name: 'register',
      component: () => import('../views/RegisterView.vue'),
      meta: { guestOnly: true },
    },

    {
      path: '/app',
      component: () => import('../layouts/AppLayout.vue'),
      meta: { requiresAuth: true },
      children: [
        { path: '', redirect: { name: 'dashboard' } },
        {
          path: 'dashboard',
          name: 'dashboard',
          component: () => import('../views/DashboardView.vue'),
        },
        {
          path: 'onboarding',
          name: 'onboarding',
          component: () => import('../views/OnboardingView.vue'),
        },
        {
          path: 'review',
          name: 'review',
          component: () => import('../views/ReviewView.vue'),
        },
        {
          path: 'explore',
          component: () => import('../layouts/ExploreLayout.vue'),
          redirect: { name: 'explore-chats' },
          children: [
            {
              path: 'chats',
              name: 'explore-chats',
              component: () => import('../views/explore/ChatsCategoriesView.vue'),
            },
            {
              path: 'chats/new',
              name: 'explore-chats-new',
              component: () => import('../views/explore/CategoryFormView.vue'),
            },
            {
              path: 'chats/:categoryId',
              name: 'explore-chats-detail',
              component: () => import('../views/explore/CategoryChatView.vue'),
            },
            {
              path: 'research',
              name: 'explore-research',
              component: () => import('../views/explore/ResearchListView.vue'),
            },
            {
              path: 'research/new',
              name: 'explore-research-new',
              component: () => import('../views/explore/ResearchNewView.vue'),
            },
            {
              path: 'research/:researchId',
              name: 'explore-research-detail',
              component: () => import('../views/explore/ResearchDetailView.vue'),
            },
            {
              path: 'mcp',
              name: 'explore-mcp',
              component: () => import('../views/explore/McpListView.vue'),
            },
            {
              path: 'mcp/new',
              name: 'explore-mcp-new',
              component: () => import('../views/explore/McpNewView.vue'),
            },
            {
              path: 'mcp/:importId',
              name: 'explore-mcp-detail',
              component: () => import('../views/explore/McpDetailView.vue'),
            },
          ],
        },

        {
          path: 'subjects/mine',
          name: 'subjects-mine',
          component: () => import('../views/MySubjectsView.vue'),
        },
        {
          path: 'subjects/catalog',
          name: 'subjects-catalog',
          component: () => import('../views/CatalogView.vue'),
        },
        {
          path: 'subjects/:id/lesson',
          name: 'lesson',
          component: () => import('../views/LessonView.vue'),
        },
        {
          path: 'subjects/:subjectId/topics/:topicId',
          name: 'subject-topic',
          component: () => import('../views/TopicDetailView.vue'),
        },
        {
          path: 'subjects/:id',
          name: 'subject',
          component: () => import('../views/SubjectDetailView.vue'),
        },

        {
          path: 'quizzes',
          name: 'quizzes',
          component: () => import('../views/QuizListView.vue'),
        },
        {
          path: 'quizzes/:id',
          name: 'quiz',
          component: () => import('../views/QuizTakeView.vue'),
        },
      ],
    },

    { path: '/catalog', redirect: '/app/subjects/catalog' },
    { path: '/my-subjects', redirect: '/app/subjects/mine' },
    { path: '/subjects/:id/lesson', redirect: (to) => `/app/subjects/${to.params.id}/lesson` },
    { path: '/subjects/:id', redirect: (to) => `/app/subjects/${to.params.id}` },
    {
      path: '/topics/:id',
      name: 'topic-legacy',
      meta: { requiresAuth: true },
      component: () => import('../views/TopicDetailView.vue'),
    },
    { path: '/quizzes', redirect: '/app/quizzes' },
    { path: '/quizzes/:id', redirect: (to) => `/app/quizzes/${to.params.id}` },
  ],
})

router.beforeEach((to) => {
  const token = localStorage.getItem('authToken')
  if (to.name === 'home' && token) {
    return { name: 'dashboard' }
  }
  if (to.meta.requiresAuth && !token) {
    return { name: 'login', query: { redirect: to.fullPath } }
  }
  if (to.meta.guestOnly && token) {
    return { name: 'dashboard' }
  }
  if (to.meta.requiresAuth && token) {
    const onboarded = localStorage.getItem('onboardingDone')
    if (!onboarded && to.name !== 'onboarding' && to.path.startsWith('/app/')) {
      return { name: 'onboarding', query: { next: to.fullPath } }
    }
  }
  return true
})

export default router

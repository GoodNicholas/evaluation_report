import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'home',
      component: () => import('@/views/HomeView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/login',
      name: 'login',
      component: () => import('@/views/LoginView.vue'),
      meta: { guest: true },
    },
    {
      path: '/register',
      name: 'register',
      component: () => import('@/views/RegisterView.vue'),
      meta: { guest: true },
    },
    {
      path: '/courses',
      name: 'courses',
      component: () => import('@/views/CoursesView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/courses/:id',
      name: 'course',
      component: () => import('@/views/CourseView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/courses/:id/materials',
      name: 'materials',
      component: () => import('@/views/MaterialsView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/courses/:id/assignments',
      name: 'assignments',
      component: () => import('@/views/AssignmentsView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/courses/:id/gradebook',
      name: 'gradebook',
      component: () => import('@/views/GradebookView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/chat',
      name: 'chat',
      component: () => import('@/views/ChatView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/profile',
      name: 'profile',
      component: () => import('@/views/ProfileView.vue'),
      meta: { requiresAuth: true },
    },
  ],
})

router.beforeEach(async (to, from, next) => {
  const authStore = useAuthStore()
  const requiresAuth = to.matched.some((record) => record.meta.requiresAuth)
  const isGuest = to.matched.some((record) => record.meta.guest)

  if (!authStore.isAuthenticated) {
    await authStore.fetchUser()
  }

  if (requiresAuth && !authStore.isAuthenticated) {
    next('/login')
  } else if (isGuest && authStore.isAuthenticated) {
    next('/')
  } else {
    next()
  }
})

export default router 
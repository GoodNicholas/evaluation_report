<template>
  <div class="py-6">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <div class="flex justify-between items-center">
        <h1 class="text-2xl font-semibold text-gray-900">Courses</h1>
        <button
          v-if="authStore.isTeacher"
          @click="showCreateModal = true"
          class="btn btn-primary"
        >
          Create Course
        </button>
      </div>

      <div class="mt-6 grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
        <div
          v-for="course in coursesStore.courses"
          :key="course.id"
          class="card hover:shadow-lg transition-shadow"
        >
          <h3 class="text-lg font-medium text-gray-900">{{ course.title }}</h3>
          <p class="mt-2 text-gray-500">{{ course.description }}</p>
          <div class="mt-4 flex space-x-4">
            <router-link
              :to="`/courses/${course.id}`"
              class="text-blue-600 hover:text-blue-500"
            >
              View Details
            </router-link>
            <router-link
              :to="`/courses/${course.id}/materials`"
              class="text-blue-600 hover:text-blue-500"
            >
              Materials
            </router-link>
            <router-link
              :to="`/courses/${course.id}/assignments`"
              class="text-blue-600 hover:text-blue-500"
            >
              Assignments
            </router-link>
            <router-link
              :to="`/courses/${course.id}/gradebook`"
              class="text-blue-600 hover:text-blue-500"
            >
              Gradebook
            </router-link>
          </div>
        </div>
      </div>
    </div>

    <!-- Create Course Modal -->
    <div v-if="showCreateModal" class="fixed inset-0 bg-gray-500 bg-opacity-75 flex items-center justify-center">
      <div class="bg-white rounded-lg p-6 max-w-md w-full">
        <h2 class="text-lg font-medium text-gray-900 mb-4">Create Course</h2>
        <form @submit.prevent="handleCreateCourse">
          <div class="space-y-4">
            <div>
              <label for="title" class="block text-sm font-medium text-gray-700">Title</label>
              <input
                id="title"
                v-model="newCourse.title"
                type="text"
                required
                class="input mt-1"
              />
            </div>
            <div>
              <label for="description" class="block text-sm font-medium text-gray-700">Description</label>
              <textarea
                id="description"
                v-model="newCourse.description"
                rows="3"
                required
                class="input mt-1"
              ></textarea>
            </div>
          </div>
          <div class="mt-6 flex justify-end space-x-3">
            <button
              type="button"
              @click="showCreateModal = false"
              class="btn btn-secondary"
            >
              Cancel
            </button>
            <button
              type="submit"
              class="btn btn-primary"
              :disabled="loading"
            >
              {{ loading ? 'Creating...' : 'Create' }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useCoursesStore } from '@/stores/courses'

const authStore = useAuthStore()
const coursesStore = useCoursesStore()

const showCreateModal = ref(false)
const loading = ref(false)
const newCourse = ref({
  title: '',
  description: '',
})

onMounted(async () => {
  await coursesStore.fetchCourses()
})

async function handleCreateCourse() {
  loading.value = true
  try {
    await coursesStore.createCourse(newCourse.value)
    showCreateModal.value = false
    newCourse.value = { title: '', description: '' }
  } catch (error) {
    console.error('Failed to create course:', error)
  } finally {
    loading.value = false
  }
}
</script> 
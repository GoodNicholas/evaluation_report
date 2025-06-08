<template>
  <div class="py-6">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <div class="flex justify-between items-center">
        <h1 class="text-2xl font-semibold text-gray-900">Course Materials</h1>
        <div class="flex space-x-4">
          <input
            type="file"
            ref="fileInput"
            class="hidden"
            @change="handleFileSelect"
          />
          <button
            v-if="authStore.isTeacher"
            @click="$refs.fileInput.click()"
            class="btn btn-primary"
          >
            Upload Material
          </button>
          <router-link
            :to="`/courses/${courseId}`"
            class="btn btn-secondary"
          >
            Back to Course
          </router-link>
        </div>
      </div>

      <div class="mt-6 grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
        <div
          v-for="material in coursesStore.materials"
          :key="material.id"
          class="card hover:shadow-lg transition-shadow"
        >
          <div class="flex justify-between items-start">
            <div>
              <h3 class="text-lg font-medium text-gray-900">{{ material.title }}</h3>
              <p class="mt-1 text-sm text-gray-500">
                Uploaded {{ new Date(material.created_at).toLocaleDateString() }}
              </p>
            </div>
            <div class="flex space-x-2">
              <a
                :href="material.file_url"
                target="_blank"
                class="text-blue-600 hover:text-blue-500"
              >
                Download
              </a>
              <button
                v-if="authStore.isTeacher"
                @click="handleDeleteMaterial(material.id)"
                class="text-red-600 hover:text-red-500"
              >
                Delete
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useCoursesStore } from '@/stores/courses'

const route = useRoute()
const authStore = useAuthStore()
const coursesStore = useCoursesStore()

const courseId = route.params.id
const fileInput = ref(null)

onMounted(async () => {
  await coursesStore.fetchMaterials(courseId)
})

async function handleFileSelect(event) {
  const file = event.target.files[0]
  if (!file) return

  try {
    await coursesStore.uploadMaterial(courseId, file)
    event.target.value = null
  } catch (error) {
    console.error('Failed to upload material:', error)
  }
}

async function handleDeleteMaterial(materialId) {
  if (!confirm('Are you sure you want to delete this material?')) return

  try {
    await coursesStore.deleteMaterial(courseId, materialId)
  } catch (error) {
    console.error('Failed to delete material:', error)
  }
}
</script> 
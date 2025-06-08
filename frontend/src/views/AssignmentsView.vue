<template>
  <div class="py-6">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <div class="flex justify-between items-center">
        <h1 class="text-2xl font-semibold text-gray-900">Course Assignments</h1>
        <div class="flex space-x-4">
          <button
            v-if="authStore.isTeacher"
            @click="showCreateModal = true"
            class="btn btn-primary"
          >
            Create Assignment
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
          v-for="assignment in coursesStore.assignments"
          :key="assignment.id"
          class="card hover:shadow-lg transition-shadow"
        >
          <div class="flex justify-between items-start">
            <div>
              <h3 class="text-lg font-medium text-gray-900">{{ assignment.title }}</h3>
              <p class="mt-1 text-sm text-gray-500">{{ assignment.description }}</p>
              <p class="mt-2 text-sm text-gray-500">
                Due: {{ new Date(assignment.due_date).toLocaleDateString() }}
              </p>
            </div>
            <div class="flex space-x-2">
              <button
                v-if="!authStore.isTeacher"
                @click="handleSubmitAssignment(assignment)"
                class="text-blue-600 hover:text-blue-500"
              >
                Submit
              </button>
              <button
                v-if="authStore.isTeacher"
                @click="handleEditAssignment(assignment)"
                class="text-blue-600 hover:text-blue-500"
              >
                Edit
              </button>
              <button
                v-if="authStore.isTeacher"
                @click="handleDeleteAssignment(assignment.id)"
                class="text-red-600 hover:text-red-500"
              >
                Delete
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Create/Edit Assignment Modal -->
    <div v-if="showCreateModal" class="fixed inset-0 bg-gray-500 bg-opacity-75 flex items-center justify-center">
      <div class="bg-white rounded-lg p-6 max-w-md w-full">
        <h2 class="text-lg font-medium text-gray-900 mb-4">
          {{ editingAssignment ? 'Edit Assignment' : 'Create Assignment' }}
        </h2>
        <form @submit.prevent="handleSaveAssignment">
          <div class="space-y-4">
            <div>
              <label for="title" class="block text-sm font-medium text-gray-700">Title</label>
              <input
                id="title"
                v-model="assignmentForm.title"
                type="text"
                required
                class="input mt-1"
              />
            </div>
            <div>
              <label for="description" class="block text-sm font-medium text-gray-700">Description</label>
              <textarea
                id="description"
                v-model="assignmentForm.description"
                rows="3"
                required
                class="input mt-1"
              ></textarea>
            </div>
            <div>
              <label for="dueDate" class="block text-sm font-medium text-gray-700">Due Date</label>
              <input
                id="dueDate"
                v-model="assignmentForm.due_date"
                type="datetime-local"
                required
                class="input mt-1"
              />
            </div>
          </div>
          <div class="mt-6 flex justify-end space-x-3">
            <button
              type="button"
              @click="closeModal"
              class="btn btn-secondary"
            >
              Cancel
            </button>
            <button
              type="submit"
              class="btn btn-primary"
              :disabled="loading"
            >
              {{ loading ? 'Saving...' : 'Save' }}
            </button>
          </div>
        </form>
      </div>
    </div>

    <!-- Submit Assignment Modal -->
    <div v-if="showSubmitModal" class="fixed inset-0 bg-gray-500 bg-opacity-75 flex items-center justify-center">
      <div class="bg-white rounded-lg p-6 max-w-md w-full">
        <h2 class="text-lg font-medium text-gray-900 mb-4">Submit Assignment</h2>
        <form @submit.prevent="handleSubmit">
          <div class="space-y-4">
            <div>
              <label for="submissionFile" class="block text-sm font-medium text-gray-700">File</label>
              <input
                id="submissionFile"
                type="file"
                ref="submissionFileInput"
                @change="handleSubmissionFileSelect"
                required
                class="input mt-1"
              />
            </div>
          </div>
          <div class="mt-6 flex justify-end space-x-3">
            <button
              type="button"
              @click="showSubmitModal = false"
              class="btn btn-secondary"
            >
              Cancel
            </button>
            <button
              type="submit"
              class="btn btn-primary"
              :disabled="loading"
            >
              {{ loading ? 'Submitting...' : 'Submit' }}
            </button>
          </div>
        </form>
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
const showCreateModal = ref(false)
const showSubmitModal = ref(false)
const loading = ref(false)
const editingAssignment = ref(null)
const submissionFile = ref(null)
const submissionFileInput = ref(null)

const assignmentForm = ref({
  title: '',
  description: '',
  due_date: '',
})

onMounted(async () => {
  await coursesStore.fetchAssignments(courseId)
})

function handleEditAssignment(assignment) {
  editingAssignment.value = assignment
  assignmentForm.value = { ...assignment }
  showCreateModal.value = true
}

function handleSubmitAssignment(assignment) {
  editingAssignment.value = assignment
  showSubmitModal.value = true
}

function closeModal() {
  showCreateModal.value = false
  editingAssignment.value = null
  assignmentForm.value = {
    title: '',
    description: '',
    due_date: '',
  }
}

async function handleSaveAssignment() {
  loading.value = true
  try {
    if (editingAssignment.value) {
      await coursesStore.updateAssignment(courseId, editingAssignment.value.id, assignmentForm.value)
    } else {
      await coursesStore.createAssignment(courseId, assignmentForm.value)
    }
    closeModal()
  } catch (error) {
    console.error('Failed to save assignment:', error)
  } finally {
    loading.value = false
  }
}

async function handleDeleteAssignment(assignmentId) {
  if (!confirm('Are you sure you want to delete this assignment?')) return

  try {
    await coursesStore.deleteAssignment(courseId, assignmentId)
  } catch (error) {
    console.error('Failed to delete assignment:', error)
  }
}

function handleSubmissionFileSelect(event) {
  submissionFile.value = event.target.files[0]
}

async function handleSubmit() {
  if (!submissionFile.value) return

  loading.value = true
  try {
    // TODO: Implement submission logic
    showSubmitModal.value = false
    submissionFile.value = null
    if (submissionFileInput.value) {
      submissionFileInput.value.value = ''
    }
  } catch (error) {
    console.error('Failed to submit assignment:', error)
  } finally {
    loading.value = false
  }
}
</script> 
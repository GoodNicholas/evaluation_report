<template>
  <div class="py-6">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <div class="flex justify-between items-center">
        <h1 class="text-2xl font-semibold text-gray-900">Course Roles</h1>
        <div class="flex space-x-4">
          <button
            v-if="isOwner"
            @click="showCreateModal = true"
            class="btn btn-primary"
          >
            Add Role
          </button>
          <router-link
            :to="`/courses/${courseId}`"
            class="btn btn-secondary"
          >
            Back to Course
          </router-link>
        </div>
      </div>

      <div class="mt-6">
        <div class="bg-white shadow overflow-hidden sm:rounded-md">
          <ul class="divide-y divide-gray-200">
            <li v-for="role in roles" :key="role.id" class="px-6 py-4">
              <div class="flex items-center justify-between">
                <div class="flex items-center">
                  <div class="ml-4">
                    <div class="text-sm font-medium text-gray-900">
                      {{ role.user.email }}
                    </div>
                    <div class="text-sm text-gray-500">
                      Role: {{ role.role }}
                    </div>
                  </div>
                </div>
                <div v-if="isOwner && role.role !== 'owner'" class="flex space-x-2">
                  <button
                    @click="handleEditRole(role)"
                    class="text-blue-600 hover:text-blue-500"
                  >
                    Edit
                  </button>
                  <button
                    @click="handleDeleteRole(role)"
                    class="text-red-600 hover:text-red-500"
                  >
                    Delete
                  </button>
                </div>
              </div>
            </li>
          </ul>
        </div>
      </div>
    </div>

    <!-- Create/Edit Role Modal -->
    <div v-if="showCreateModal" class="fixed inset-0 bg-gray-500 bg-opacity-75 flex items-center justify-center">
      <div class="bg-white rounded-lg p-6 max-w-md w-full">
        <h2 class="text-lg font-medium text-gray-900 mb-4">
          {{ editingRole ? 'Edit Role' : 'Add Role' }}
        </h2>
        <form @submit.prevent="handleSaveRole">
          <div class="space-y-4">
            <div v-if="!editingRole">
              <label for="email" class="block text-sm font-medium text-gray-700">User Email</label>
              <input
                id="email"
                v-model="roleForm.email"
                type="email"
                required
                class="input mt-1"
              />
            </div>
            <div>
              <label for="role" class="block text-sm font-medium text-gray-700">Role</label>
              <select
                id="role"
                v-model="roleForm.role"
                required
                class="input mt-1"
              >
                <option value="teacher">Teacher</option>
                <option value="assistant">Assistant</option>
              </select>
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
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useCourseRolesStore } from '@/stores/courseRoles'

const route = useRoute()
const authStore = useAuthStore()
const courseRolesStore = useCourseRolesStore()

const courseId = route.params.id
const showCreateModal = ref(false)
const loading = ref(false)
const editingRole = ref(null)

const roleForm = ref({
  email: '',
  role: 'teacher'
})

const roles = computed(() => courseRolesStore.roles)
const isOwner = computed(() => {
  const userRole = courseRolesStore.getRoleByUserId(authStore.user.id)
  return userRole?.role === 'owner'
})

onMounted(async () => {
  await courseRolesStore.fetchRoles(courseId)
})

function handleEditRole(role) {
  editingRole.value = role
  roleForm.value = {
    role: role.role
  }
  showCreateModal.value = true
}

function closeModal() {
  showCreateModal.value = false
  editingRole.value = null
  roleForm.value = {
    email: '',
    role: 'teacher'
  }
}

async function handleSaveRole() {
  loading.value = true
  try {
    if (editingRole.value) {
      await courseRolesStore.updateRole(
        courseId,
        editingRole.value.user_id,
        { role: roleForm.value.role }
      )
    } else {
      // First, find the user by email
      const response = await fetch(`/api/v1/users/by-email/${roleForm.value.email}`)
      if (!response.ok) {
        throw new Error('User not found')
      }
      const user = await response.json()
      
      await courseRolesStore.createRole(courseId, {
        user_id: user.id,
        role: roleForm.value.role
      })
    }
    closeModal()
  } catch (error) {
    console.error('Failed to save role:', error)
  } finally {
    loading.value = false
  }
}

async function handleDeleteRole(role) {
  if (!confirm('Are you sure you want to remove this role?')) return

  try {
    await courseRolesStore.deleteRole(courseId, role.user_id)
  } catch (error) {
    console.error('Failed to delete role:', error)
  }
}
</script> 
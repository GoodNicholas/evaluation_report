import { defineStore } from 'pinia'
import { api } from '@/api'

export const useCourseRolesStore = defineStore('courseRoles', {
  state: () => ({
    roles: [],
    loading: false,
    error: null
  }),

  actions: {
    async fetchRoles(courseId) {
      this.loading = true
      this.error = null
      try {
        const response = await api.get(`/courses/${courseId}/roles`)
        this.roles = response.data
      } catch (error) {
        this.error = error.response?.data?.detail || 'Failed to fetch roles'
        throw error
      } finally {
        this.loading = false
      }
    },

    async createRole(courseId, roleData) {
      this.loading = true
      this.error = null
      try {
        const response = await api.post(`/courses/${courseId}/roles`, roleData)
        this.roles.push(response.data)
        return response.data
      } catch (error) {
        this.error = error.response?.data?.detail || 'Failed to create role'
        throw error
      } finally {
        this.loading = false
      }
    },

    async updateRole(courseId, userId, roleData) {
      this.loading = true
      this.error = null
      try {
        const response = await api.put(`/courses/${courseId}/roles/${userId}`, roleData)
        const index = this.roles.findIndex(role => role.user_id === userId)
        if (index !== -1) {
          this.roles[index] = response.data
        }
        return response.data
      } catch (error) {
        this.error = error.response?.data?.detail || 'Failed to update role'
        throw error
      } finally {
        this.loading = false
      }
    },

    async deleteRole(courseId, userId) {
      this.loading = true
      this.error = null
      try {
        const response = await api.delete(`/courses/${courseId}/roles/${userId}`)
        this.roles = this.roles.filter(role => role.user_id !== userId)
        return response.data
      } catch (error) {
        this.error = error.response?.data?.detail || 'Failed to delete role'
        throw error
      } finally {
        this.loading = false
      }
    }
  },

  getters: {
    getRoleByUserId: (state) => (userId) => {
      return state.roles.find(role => role.user_id === userId)
    },

    getRolesByType: (state) => (roleType) => {
      return state.roles.filter(role => role.role === roleType)
    }
  }
}) 
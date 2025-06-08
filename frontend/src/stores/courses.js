import { defineStore } from 'pinia'
import { ref } from 'vue'
import axios from 'axios'

export const useCoursesStore = defineStore('courses', () => {
  const courses = ref([])
  const currentCourse = ref(null)
  const materials = ref([])
  const assignments = ref([])

  async function fetchCourses() {
    const response = await axios.get('/api/v1/courses')
    courses.value = response.data
  }

  async function fetchCourse(id) {
    const response = await axios.get(`/api/v1/courses/${id}`)
    currentCourse.value = response.data
  }

  async function createCourse(data) {
    const response = await axios.post('/api/v1/courses', data)
    courses.value.push(response.data)
    return response.data
  }

  async function updateCourse(id, data) {
    const response = await axios.patch(`/api/v1/courses/${id}`, data)
    const index = courses.value.findIndex((course) => course.id === id)
    if (index !== -1) {
      courses.value[index] = response.data
    }
    if (currentCourse.value?.id === id) {
      currentCourse.value = response.data
    }
    return response.data
  }

  async function deleteCourse(id) {
    await axios.delete(`/api/v1/courses/${id}`)
    courses.value = courses.value.filter((course) => course.id !== id)
    if (currentCourse.value?.id === id) {
      currentCourse.value = null
    }
  }

  async function fetchMaterials(courseId) {
    const response = await axios.get(`/api/v1/courses/${courseId}/materials`)
    materials.value = response.data
  }

  async function uploadMaterial(courseId, file) {
    const formData = new FormData()
    formData.append('file', file)
    const response = await axios.post(`/api/v1/courses/${courseId}/materials`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
    materials.value.push(response.data)
    return response.data
  }

  async function deleteMaterial(courseId, materialId) {
    await axios.delete(`/api/v1/courses/${courseId}/materials/${materialId}`)
    materials.value = materials.value.filter((material) => material.id !== materialId)
  }

  async function fetchAssignments(courseId) {
    const response = await axios.get(`/api/v1/courses/${courseId}/assignments`)
    assignments.value = response.data
  }

  async function createAssignment(courseId, data) {
    const response = await axios.post(`/api/v1/courses/${courseId}/assignments`, data)
    assignments.value.push(response.data)
    return response.data
  }

  async function updateAssignment(courseId, assignmentId, data) {
    const response = await axios.patch(
      `/api/v1/courses/${courseId}/assignments/${assignmentId}`,
      data
    )
    const index = assignments.value.findIndex((assignment) => assignment.id === assignmentId)
    if (index !== -1) {
      assignments.value[index] = response.data
    }
    return response.data
  }

  async function deleteAssignment(courseId, assignmentId) {
    await axios.delete(`/api/v1/courses/${courseId}/assignments/${assignmentId}`)
    assignments.value = assignments.value.filter((assignment) => assignment.id !== assignmentId)
  }

  return {
    courses,
    currentCourse,
    materials,
    assignments,
    fetchCourses,
    fetchCourse,
    createCourse,
    updateCourse,
    deleteCourse,
    fetchMaterials,
    uploadMaterial,
    deleteMaterial,
    fetchAssignments,
    createAssignment,
    updateAssignment,
    deleteAssignment,
  }
}) 
import { defineStore } from 'pinia'
import { ref } from 'vue'
import axios from 'axios'

export const useGradebookStore = defineStore('gradebook', () => {
  const gradebook = ref([])
  const loading = ref(false)
  const error = ref(null)

  async function fetchGradebook(courseId) {
    loading.value = true
    error.value = null
    try {
      const response = await axios.get(`/api/v1/courses/${courseId}/gradebook`)
      gradebook.value = response.data
    } catch (err) {
      error.value = err.response?.data?.detail || 'Failed to fetch gradebook'
    } finally {
      loading.value = false
    }
  }

  async function updateGrade(courseId, studentId, assignmentId, score) {
    loading.value = true
    error.value = null
    try {
      const response = await axios.patch(`/api/v1/courses/${courseId}/gradebook`, {
        student_id: studentId,
        assignment_id: assignmentId,
        score,
      })
      const index = gradebook.value.findIndex(
        (entry) => entry.student_id === studentId && entry.assignment_id === assignmentId
      )
      if (index !== -1) {
        gradebook.value[index] = response.data
      }
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || 'Failed to update grade'
      throw err
    } finally {
      loading.value = false
    }
  }

  function getStudentGrades(studentId) {
    return gradebook.value.filter((entry) => entry.student_id === studentId)
  }

  function getAssignmentGrades(assignmentId) {
    return gradebook.value.filter((entry) => entry.assignment_id === assignmentId)
  }

  function getStudentAverage(studentId) {
    const grades = getStudentGrades(studentId)
    if (grades.length === 0) return null
    const sum = grades.reduce((acc, grade) => acc + grade.score, 0)
    return sum / grades.length
  }

  function getAssignmentAverage(assignmentId) {
    const grades = getAssignmentGrades(assignmentId)
    if (grades.length === 0) return null
    const sum = grades.reduce((acc, grade) => acc + grade.score, 0)
    return sum / grades.length
  }

  return {
    gradebook,
    loading,
    error,
    fetchGradebook,
    updateGrade,
    getStudentGrades,
    getAssignmentGrades,
    getStudentAverage,
    getAssignmentAverage,
  }
}) 
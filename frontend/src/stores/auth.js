import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import axios from 'axios'

export const useAuthStore = defineStore('auth', () => {
  const user = ref(null)
  const token = ref(localStorage.getItem('token'))
  const refreshToken = ref(localStorage.getItem('refreshToken'))

  const isAuthenticated = computed(() => !!token.value)
  const isAdmin = computed(() => user.value?.role === 'admin')
  const isTeacher = computed(() => user.value?.role === 'teacher')

  // Set up axios interceptor for token refresh
  axios.interceptors.response.use(
    (response) => response,
    async (error) => {
      const originalRequest = error.config

      if (error.response.status === 401 && !originalRequest._retry) {
        originalRequest._retry = true

        try {
          const response = await axios.post('/api/v1/auth/refresh', {
            refresh_token: refreshToken.value,
          })

          const { access_token, refresh_token } = response.data
          setTokens(access_token, refresh_token)

          originalRequest.headers.Authorization = `Bearer ${access_token}`
          return axios(originalRequest)
        } catch (error) {
          logout()
          return Promise.reject(error)
        }
      }

      return Promise.reject(error)
    }
  )

  function setTokens(accessToken, newRefreshToken) {
    token.value = accessToken
    refreshToken.value = newRefreshToken
    localStorage.setItem('token', accessToken)
    localStorage.setItem('refreshToken', newRefreshToken)
    axios.defaults.headers.common.Authorization = `Bearer ${accessToken}`
  }

  async function login(email, password) {
    const response = await axios.post('/api/v1/auth/login', {
      email,
      password,
    })

    const { access_token, refresh_token, user: userData } = response.data
    setTokens(access_token, refresh_token)
    user.value = userData
  }

  async function register(email, password, role) {
    const response = await axios.post('/api/v1/auth/register', {
      email,
      password,
      role,
    })

    const { access_token, refresh_token, user: userData } = response.data
    setTokens(access_token, refresh_token)
    user.value = userData
  }

  async function logout() {
    user.value = null
    token.value = null
    refreshToken.value = null
    localStorage.removeItem('token')
    localStorage.removeItem('refreshToken')
    delete axios.defaults.headers.common.Authorization
  }

  async function fetchUser() {
    if (!token.value) return

    try {
      const response = await axios.get('/api/v1/auth/me')
      user.value = response.data
    } catch (error) {
      logout()
    }
  }

  return {
    user,
    token,
    refreshToken,
    isAuthenticated,
    isAdmin,
    isTeacher,
    login,
    register,
    logout,
    fetchUser,
  }
}) 
import { defineStore } from 'pinia'
import { ref } from 'vue'
import axios from 'axios'

export const useChatStore = defineStore('chat', () => {
  const dialogs = ref([])
  const currentDialog = ref(null)
  const messages = ref([])
  const loading = ref(false)
  const error = ref(null)
  const ws = ref(null)

  function connectWebSocket() {
    const token = localStorage.getItem('token')
    ws.value = new WebSocket(`ws://localhost:8000/api/v1/ws/chat?token=${token}`)

    ws.value.onmessage = (event) => {
      const message = JSON.parse(event.data)
      if (message.dialog_id === currentDialog.value?.id) {
        messages.value.push(message)
      }
    }

    ws.value.onclose = () => {
      setTimeout(connectWebSocket, 1000)
    }
  }

  async function fetchDialogs() {
    loading.value = true
    error.value = null
    try {
      const response = await axios.get('/api/v1/messages/dialogs')
      dialogs.value = response.data
    } catch (err) {
      error.value = err.response?.data?.detail || 'Failed to fetch dialogs'
    } finally {
      loading.value = false
    }
  }

  async function fetchMessages(dialogId) {
    loading.value = true
    error.value = null
    try {
      const response = await axios.get(`/api/v1/messages/dialogs/${dialogId}/messages`)
      messages.value = response.data
      currentDialog.value = dialogs.value.find((dialog) => dialog.id === dialogId)
    } catch (err) {
      error.value = err.response?.data?.detail || 'Failed to fetch messages'
    } finally {
      loading.value = false
    }
  }

  async function sendMessage(dialogId, content) {
    if (!ws.value || ws.value.readyState !== WebSocket.OPEN) {
      throw new Error('WebSocket is not connected')
    }

    const message = {
      dialog_id: dialogId,
      content,
    }

    ws.value.send(JSON.stringify(message))
  }

  async function createDialog(userId) {
    loading.value = true
    error.value = null
    try {
      const response = await axios.post('/api/v1/messages/dialogs', { user_id: userId })
      dialogs.value.push(response.data)
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || 'Failed to create dialog'
      throw err
    } finally {
      loading.value = false
    }
  }

  function disconnect() {
    if (ws.value) {
      ws.value.close()
      ws.value = null
    }
  }

  return {
    dialogs,
    currentDialog,
    messages,
    loading,
    error,
    connectWebSocket,
    fetchDialogs,
    fetchMessages,
    sendMessage,
    createDialog,
    disconnect,
  }
}) 
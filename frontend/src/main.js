import { createApp } from 'vue'
import { createPinia } from 'pinia'
import axios from 'axios'

import App from './App.vue'
import router from './router'

import './assets/main.css'

// Configure axios
axios.defaults.baseURL = 'http://localhost:8000'
axios.defaults.headers.common['Content-Type'] = 'application/json'

const app = createApp(App)

app.use(createPinia())
app.use(router)

app.mount('#app')

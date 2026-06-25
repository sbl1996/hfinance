import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import { registerServiceWorker } from './registerServiceWorker'

// Vant �基础样式
import 'vant/lib/index.css'
import './styles/market-badge.css'

const app = createApp(App)
app.use(createPinia())
app.use(router)
app.mount('#app')

registerServiceWorker()

import { createApp } from 'vue'
import { createPinia } from 'pinia'
import Vant from 'vant'
import 'vant/lib/index.css'
import App from './App.vue'
import './styles/base.css'

createApp(App).use(createPinia()).use(Vant).mount('#app')

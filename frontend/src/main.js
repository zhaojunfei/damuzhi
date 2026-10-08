import { createApp } from 'vue'
import { createRouter, createWebHashHistory } from 'vue-router'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import * as Icons from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import axios from 'axios'
import App from './App.vue'
import Login from './views/Login.vue'
import Layout from './views/Layout.vue'
import Dashboard from './views/Dashboard.vue'
import Employees from './views/Employees.vue'
import Salaries from './views/Salaries.vue'
import Payments from './views/Payments.vue'
import GlobalParams from './views/GlobalParams.vue'
import AdminStores from './views/AdminStores.vue'
import AdminStats from './views/AdminStats.vue'
import AuditLog from './views/AuditLog.vue'

// 请求拦截：注入用户ID
axios.interceptors.request.use(cfg => {
  const u = JSON.parse(localStorage.getItem('salary_user') || 'null')
  if (u && u.id) cfg.params = { ...(cfg.params || {}), x_user_id: u.id }
  return cfg
})
axios.interceptors.response.use(r => r, e => {
  ElMessage.error(e.response?.data?.detail || e.message || '请求失败')
  return Promise.reject(e)
})
window.axios = axios

const routes = [
  { path: '/login', component: Login },
  {
    path: '/', component: Layout, children: [
      { path: '', redirect: '/dashboard' },
      { path: 'dashboard', component: Dashboard, meta: { title: '工作台' } },
      { path: 'employees', component: Employees, meta: { title: '员工档案' } },
      { path: 'salaries', component: Salaries, meta: { title: '工资明细' } },
      { path: 'payments', component: Payments, meta: { title: '工资发放' } },
      { path: 'params', component: GlobalParams, meta: { title: '全局参数', admin: true } },
      { path: 'stores', component: AdminStores, meta: { title: '商铺管理', admin: true } },
      { path: 'stats', component: AdminStats, meta: { title: '统计分析', admin: true } },
      { path: 'audit', component: AuditLog, meta: { title: '审计日志', admin: true } }
    ]
  }
]
const router = createRouter({ history: createWebHashHistory(), routes })
router.beforeEach((to, from, next) => {
  const u = JSON.parse(localStorage.getItem('salary_user') || 'null')
  if (to.path !== '/login' && !u) return next('/login')
  if (to.meta?.admin && u && u.role !== 'super_admin') return next('/dashboard')
  next()
})

const app = createApp(App)
for (const [name, comp] of Object.entries(Icons)) app.component(name, comp)
app.use(router).use(ElementPlus)
app.mount('#app')

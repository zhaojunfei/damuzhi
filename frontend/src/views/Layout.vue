<template>
  <el-container class="layout">
    <el-aside width="220px" class="aside">
      <div class="aside-logo">薪 · 工资管理</div>
      <el-menu :default-active="$route.path" router background-color="#1e293b"
               text-color="#cbd5e1" active-text-color="#3b82f6" class="menu">
        <el-menu-item index="/dashboard"><el-icon><Odometer /></el-icon><span>工作台</span></el-menu-item>
        <el-menu-item index="/employees"><el-icon><UserFilled /></el-icon><span>员工档案</span></el-menu-item>
        <el-menu-item index="/salaries"><el-icon><Money /></el-icon><span>工资明细</span></el-menu-item>
        <el-menu-item index="/payments"><el-icon><Tickets /></el-icon><span>工资发放</span></el-menu-item>
        <template v-if="user.role === 'super_admin'">
          <el-menu-item index="/params"><el-icon><Setting /></el-icon><span>全局参数</span></el-menu-item>
          <el-menu-item index="/stores"><el-icon><OfficeBuilding /></el-icon><span>商铺管理</span></el-menu-item>
          <el-menu-item index="/stats"><el-icon><DataAnalysis /></el-icon><span>统计分析</span></el-menu-item>
          <el-menu-item index="/audit"><el-icon><Document /></el-icon><span>审计日志</span></el-menu-item>
        </template>
      </el-menu>
    </el-aside>
    <el-container>
      <el-header class="header">
        <div class="header-title">{{ $route.meta.title || '' }}</div>
        <div class="header-right">
          <el-tag v-if="user.role === 'super_admin'" type="warning">超级管理员</el-tag>
          <el-tag v-else type="primary">{{ storeName }}</el-tag>
          <span class="username">{{ user.username }}</span>
          <el-button link @click="logout">退出</el-button>
        </div>
      </el-header>
      <el-main class="main">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>
<script setup>
import { onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessageBox } from 'element-plus'
const router = useRouter()
const route = useRoute()
const user = JSON.parse(localStorage.getItem('salary_user') || '{}')
const storeName = user.store_name || ''

// 需要商铺上下文的业务页
const NEED_STORE = ['/dashboard', '/employees', '/salaries', '/payments']
async function ensureStore() {
  if (user.role !== 'super_admin' || user.store_id) return
  if (!NEED_STORE.includes(route.path)) return
  try {
    const { data } = await window.axios.get('/api/stores')
    if (data.length) {
      localStorage.setItem('salary_user', JSON.stringify({ ...user, store_id: data[0].id, store_name: data[0].name, role: 'super_admin' }))
      location.reload()
    }
  } catch (e) {}
}
onMounted(ensureStore)
// 超管从商铺管理页直接进入业务页但未选商铺时，自动进入第一个商铺
watch(() => route.path, ensureStore)

function logout() {
  ElMessageBox.confirm('确定退出登录？', '提示', { type: 'warning' }).then(() => {
    localStorage.removeItem('salary_user')
    router.push('/login')
  }).catch(() => {})
}
</script>
<style scoped>
.layout { height: 100vh; }
.aside { background: #1e293b; display: flex; flex-direction: column; }
.aside-logo {
  color: #fff; font-size: 16px; font-weight: 700; padding: 20px 20px; letter-spacing: 1px;
}
.menu { border-right: none; flex: 1; }
.menu .el-menu-item { margin: 2px 8px; border-radius: 8px; }
.menu .el-menu-item.is-active { background: #334155; }
.header {
  background: #fff; display: flex; align-items: center; justify-content: space-between;
  box-shadow: 0 1px 4px rgba(0,0,0,.08); padding: 0 20px;
}
.header-title { font-size: 16px; font-weight: 600; color: #1e293b; }
.header-right { display: flex; align-items: center; gap: 12px; }
.username { color: #475569; font-weight: 500; }
.main { background: #f0f2f5; padding: 16px; overflow: auto; }
</style>

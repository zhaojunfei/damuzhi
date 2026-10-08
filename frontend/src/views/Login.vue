<template>
  <div class="login-wrap">
    <div class="login-card">
      <div class="brand">
        <div class="logo">薪</div>
        <h1>社保局店工资管理系统</h1>
        <p>多商铺 · 全局参数 · 智能计算</p>
      </div>
      <el-form @submit.prevent="doLogin" class="form">
        <el-form-item>
          <el-input v-model="username" placeholder="用户名" size="large" :prefix-icon="User" />
        </el-form-item>
        <el-form-item>
          <el-input v-model="password" type="password" placeholder="密码" size="large"
                    :prefix-icon="Lock" show-password @keyup.enter="doLogin" />
        </el-form-item>
        <el-button type="primary" size="large" style="width:100%" :loading="loading" @click="doLogin">
          登 录
        </el-button>
        <p class="tip">超级管理员：admin / admin2555</p>
      </el-form>
    </div>
  </div>
</template>
<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { User, Lock } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

const router = useRouter()
const username = ref('')
const password = ref('')
const loading = ref(false)

async function doLogin() {
  if (!username.value || !password.value) return ElMessage.warning('请输入用户名和密码')
  loading.value = true
  try {
    const { data } = await window.axios.post('/api/login', { username: username.value, password: password.value })
    localStorage.setItem('salary_user', JSON.stringify(data))
    ElMessage.success('登录成功')
    router.push(data.role === 'super_admin' ? '/stores' : '/dashboard')
  } catch (e) { /* 拦截器已提示 */ }
  loading.value = false
}
</script>
<style scoped>
.login-wrap {
  min-height: 100vh; display: flex; align-items: center; justify-content: center;
  background: linear-gradient(135deg, #1e3a8a 0%, #2563eb 50%, #3b82f6 100%);
}
.login-card {
  width: 420px; background: #fff; border-radius: 16px; padding: 40px 40px 30px;
  box-shadow: 0 20px 60px rgba(0,0,0,.3);
}
.brand { text-align: center; margin-bottom: 28px; }
.logo {
  width: 64px; height: 64px; margin: 0 auto 12px; border-radius: 16px;
  background: linear-gradient(135deg, #1e3a8a, #3b82f6); color: #fff;
  font-size: 32px; font-weight: 700; display: flex; align-items: center; justify-content: center;
  box-shadow: 0 8px 20px rgba(59,130,246,.4);
}
.brand h1 { font-size: 20px; color: #1e293b; }
.brand p { color: #64748b; font-size: 13px; margin-top: 6px; }
.tip { text-align: center; color: #94a3b8; font-size: 12px; margin-top: 16px; }
</style>

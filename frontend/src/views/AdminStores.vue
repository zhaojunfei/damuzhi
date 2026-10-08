<template>
  <div>
    <el-card shadow="never">
      <template #header>
        <div class="h">
          商铺管理
          <div style="flex:1"></div>
          <el-input v-model="newStore" placeholder="新商铺名称" style="width:180px" />
          <el-button type="primary" @click="addStore">新增商铺</el-button>
        </div>
      </template>
      <el-table :data="stores" stripe>
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column prop="name" label="商铺名称" width="160" />
        <el-table-column prop="employees" label="员工" width="80" />
        <el-table-column prop="active" label="在职" width="80" />
        <el-table-column prop="salary_records" label="工资记录" width="90" />
        <el-table-column label="操作" width="160">
          <template #default="{ row }">
            <el-button link type="primary" @click="enter(row)">进入商铺</el-button>
            <el-button link type="danger" @click="delStore(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
    <el-card shadow="never" style="margin-top:16px">
      <template #header>
        <div class="h">操作员管理</div>
      </template>
      <el-table :data="users" size="small">
        <el-table-column prop="username" label="用户名" />
        <el-table-column prop="role" label="角色" width="120" />
        <el-table-column prop="store_name" label="所属商铺" />
        <el-table-column label="操作" width="100">
          <template #default="{ row }">
            <el-button v-if="row.role !== 'super_admin'" link type="danger" @click="delUser(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
      <div class="add-user">
        <el-select v-model="opStore" placeholder="商铺" style="width:150px">
          <el-option v-for="s in stores" :key="s.id" :value="s.id" :label="s.name" />
        </el-select>
        <el-input v-model="opUser" placeholder="用户名" style="width:130px" />
        <el-input v-model="opPass" placeholder="密码" style="width:130px" />
        <el-button type="success" @click="addUser">添加操作员</el-button>
      </div>
    </el-card>
  </div>
</template>
<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
const router = useRouter()
const me = JSON.parse(localStorage.getItem('salary_user') || '{}')
const stores = ref([])
const users = ref([])
const newStore = ref('')
const opStore = ref(null)
const opUser = ref('')
const opPass = ref('')

async function load() {
  const [s, u] = await Promise.all([window.axios.get('/api/stores'), window.axios.get('/api/users')])
  stores.value = s.data; users.value = u.data
}
async function addStore() {
  if (!newStore.value.trim()) return ElMessage.warning('输入商铺名称')
  await window.axios.post('/api/stores', { name: newStore.value })
  ElMessage.success('已新增'); newStore.value = ''; load()
}
function enter(row) {
  const u = { ...me, store_id: row.id, store_name: row.name, role: me.role }
  localStorage.setItem('salary_user', JSON.stringify(u))
  router.push('/dashboard')
}
async function delStore(row) {
  if (!await auth()) return
  await ElMessageBox.confirm(`删除商铺「${row.name}」将级联删除全部数据！`, '危险操作', { type: 'error' })
  await window.axios.delete(`/api/stores/${row.id}`)
  ElMessage.success('已删除'); load()
}
async function addUser() {
  if (!opStore.value || !opUser.value || !opPass.value) return ElMessage.warning('请填写完整')
  await window.axios.post('/api/users', { store_id: opStore.value, username: opUser.value, password: opPass.value })
  ElMessage.success('已添加'); opUser.value = ''; opPass.value = ''; load()
}
async function delUser(row) {
  if (!await auth()) return
  await window.axios.delete(`/api/users/${row.id}`)
  ElMessage.success('已删除'); load()
}
async function auth() {
  try {
    const { value } = await ElMessageBox.prompt('请输入授权密码 2555', '授权', { inputType: 'password' })
    if (value !== '2555') { ElMessage.error('密码错误'); return false }
    return true
  } catch (e) { return false }
}
onMounted(load)
</script>
<style scoped>
.h { display: flex; align-items: center; gap: 10px; }
.add-user { display: flex; gap: 10px; margin-top: 12px; align-items: center; }
</style>

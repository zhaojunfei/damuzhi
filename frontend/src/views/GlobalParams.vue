<template>
  <el-row :gutter="16">
    <!-- 部门管理 -->
    <el-col :span="8">
      <el-card shadow="never">
        <template #header>全局部门（管理员统一维护）</template>
        <div class="add">
          <el-input v-model="newDept" placeholder="新部门名称" style="width:150px" />
          <el-button type="primary" @click="addDept">添加</el-button>
        </div>
        <el-table :data="depts" size="small">
          <el-table-column prop="name" label="部门名称" />
          <el-table-column label="操作" width="80">
            <template #default="{ row }">
              <el-button link type="danger" @click="delDept(row)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-card>
    </el-col>
    <!-- 职务管理 -->
    <el-col :span="8">
      <el-card shadow="never">
        <template #header>全局职务 + 职务工资（职级补助）</template>
        <div class="add">
          <el-input v-model="newPos.name" placeholder="新职务" style="width:110px" />
          <el-input-number v-model="newPos.allowance" :min="0" :controls="false" placeholder="职级补助" style="width:110px" />
          <el-button type="primary" @click="addPos">添加</el-button>
        </div>
        <el-table :data="positions" size="small">
          <el-table-column prop="name" label="职务" />
          <el-table-column prop="allowance" label="职级补助(职务工资)" />
          <el-table-column label="操作" width="120">
            <template #default="{ row }">
              <el-button link type="primary" @click="editPos(row)">修改</el-button>
              <el-button link type="danger" @click="delPos(row)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-card>
    </el-col>
    <!-- 提成规则 -->
    <el-col :span="8">
      <el-card shadow="never">
        <template #header>提成规则（按职务）</template>
        <div class="add">
          <el-select v-model="newRule.position" placeholder="职务" style="width:110px">
            <el-option v-for="p in positions" :key="p.name" :value="p.name" :label="p.name" />
          </el-select>
          <el-input-number v-model="newRule.perf_rate" :controls="false" placeholder="绩效" style="width:80px" />
          <el-input-number v-model="newRule.sales_rate" :controls="false" placeholder="销售" style="width:80px" />
          <el-button type="primary" @click="addRule">添加</el-button>
        </div>
        <el-table :data="rules" size="small">
          <el-table-column prop="position" label="职务" />
          <el-table-column prop="perf_rate" label="绩效提成" />
          <el-table-column prop="sales_rate" label="销售提成" />
          <el-table-column label="操作" width="120">
            <template #default="{ row }">
              <el-button link type="primary" @click="editRule(row)">修改</el-button>
              <el-button link type="danger" @click="delRule(row)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-card>
    </el-col>
  </el-row>
</template>
<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
const depts = ref([])
const positions = ref([])
const rules = ref([])
const newDept = ref('')
const newPos = ref({ name: '', allowance: 0 })
const newRule = ref({ position: '', perf_rate: 0, sales_rate: 0 })

async function load() {
  const [d, p, r] = await Promise.all([
    window.axios.get('/api/global/departments'),
    window.axios.get('/api/global/positions'),
    window.axios.get('/api/rules')
  ])
  depts.value = d.data; positions.value = p.data; rules.value = r.data
}
async function addDept() {
  if (!newDept.value.trim()) return ElMessage.warning('输入部门名称')
  await window.axios.post('/api/global/departments', { name: newDept.value })
  ElMessage.success('已添加'); newDept.value = ''; load()
}
async function delDept(row) {
  if (!await auth()) return
  await window.axios.delete(`/api/global/departments/${row.id}`)
  ElMessage.success('已删除'); load()
}
async function addPos() {
  if (!newPos.value.name.trim()) return ElMessage.warning('输入职务名称')
  await window.axios.post('/api/global/positions', { name: newPos.value.name, allowance: newPos.value.allowance })
  ElMessage.success('已添加'); newPos.value = { name: '', allowance: 0 }; load()
}
function editPos(row) {
  ElMessageBox.prompt(`修改「${row.name}」的职级补助(职务工资)`, '修改职级补助', {
    inputValue: String(row.allowance), inputPattern: /^\d+$/, inputErrorMessage: '请输入数字'
  }).then(async ({ value }) => {
    await window.axios.put(`/api/global/positions/${row.id}`, { name: row.name, allowance: +value })
    ElMessage.success('已修改'); load()
  }).catch(() => {})
}
async function delPos(row) {
  if (!await auth()) return
  await window.axios.delete(`/api/global/positions/${row.id}`)
  ElMessage.success('已删除'); load()
}
async function addRule() {
  if (!newRule.value.position) return ElMessage.warning('选择职务')
  await window.axios.post('/api/rules', newRule.value)
  ElMessage.success('已添加'); newRule.value = { position: '', perf_rate: 0, sales_rate: 0 }; load()
}
function editRule(row) {
  ElMessageBox.prompt('绩效提成(空格分割绩效/销售，如: 800 200)', '修改提成规则', {
    inputValue: `${row.perf_rate} ${row.sales_rate}`
  }).then(async ({ value }) => {
    const [p, s] = value.split(/\s+/).map(Number)
    await window.axios.put(`/api/rules/${row.id}`, { position: row.position, perf_rate: p || 0, sales_rate: s || 0 })
    ElMessage.success('已修改'); load()
  }).catch(() => {})
}
async function delRule(row) {
  if (!await auth()) return
  await window.axios.delete(`/api/rules/${row.id}`)
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
.add { display: flex; gap: 8px; margin-bottom: 12px; align-items: center; }
</style>

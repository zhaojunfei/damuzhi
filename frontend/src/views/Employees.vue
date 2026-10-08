<template>
  <el-card shadow="never">
    <div class="toolbar">
      <el-input v-model="kw" placeholder="姓名/电话/部门/职务" clearable style="width:220px"
                @keyup.enter="load" />
      <el-select v-model="status" placeholder="状态" clearable style="width:130px">
        <el-option label="在职" value="在职" /><el-option label="离职" value="离职" />
      </el-select>
      <el-button type="primary" @click="load">查询</el-button>
      <div style="flex:1"></div>
      <el-button type="success" @click="openEdit()"><el-icon><Plus /></el-icon>新增员工</el-button>
    </div>
    <el-table :data="rows" stripe highlight-current-row @row-dblclick="row => openEdit(row)">
      <el-table-column prop="name" label="姓名" width="90" />
      <el-table-column prop="gender" label="性别" width="60" />
      <el-table-column prop="age" label="年龄" width="60" />
      <el-table-column prop="status" label="状态" width="80">
        <template #default="{ row }">
          <el-tag :type="row.status === '在职' ? 'success' : 'danger'">{{ row.status }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="department" label="部门" width="100" />
      <el-table-column prop="position" label="职务" width="100" />
      <el-table-column prop="phone" label="电话" width="120" />
      <el-table-column prop="is_bocom" label="是否交行" width="80" />
      <el-table-column prop="payment_method" label="发放形式" width="100" />
      <el-table-column prop="social_security" label="社保" width="80" />
      <el-table-column label="操作" width="120" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" @click="openEdit(row)">编辑</el-button>
          <el-button link type="danger" @click="del(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="dlg" :title="form.id ? '编辑员工' : '新增员工'" width="720px" top="5vh">
      <el-form label-width="90px">
        <el-form-item label="身份证号">
          <el-input v-model="form.id_card" style="width:260px" placeholder="输入后自动识别性别/年龄/生日" />
          <el-button type="primary" size="small" style="margin-left:8px" @click="parseId">识别</el-button>
        </el-form-item>
        <el-row :gutter="12">
          <el-col :span="8"><el-form-item label="姓名"><el-input v-model="form.name" /></el-form-item></el-col>
          <el-col :span="8"><el-form-item label="性别"><el-input v-model="form.gender" /></el-form-item></el-col>
          <el-col :span="8"><el-form-item label="年龄"><el-input v-model.number="form.age" /></el-form-item></el-col>
        </el-row>
        <el-form-item label="出生日期"><el-input v-model="form.birth_date" /></el-form-item>
        <el-row :gutter="12">
          <el-col :span="8"><el-form-item label="状态">
            <el-select v-model="form.status"><el-option value="在职" /><el-option value="离职" /></el-select>
          </el-form-item></el-col>
          <el-col :span="8"><el-form-item label="部门">
            <el-select v-model="form.department" filterable allow-create style="width:100%">
              <el-option v-for="d in depts" :key="d" :label="d" :value="d" />
            </el-select>
          </el-form-item></el-col>
          <el-col :span="8"><el-form-item label="职务">
            <el-select v-model="form.position" filterable allow-create style="width:100%">
              <el-option v-for="p in positions" :key="p.name" :label="p.name" :value="p.name" />
            </el-select>
          </el-form-item></el-col>
        </el-row>
        <el-row :gutter="12">
          <el-col :span="12"><el-form-item label="电话"><el-input v-model="form.phone" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="地址"><el-input v-model="form.address" /></el-form-item></el-col>
        </el-row>
        <el-row :gutter="12">
          <el-col :span="12"><el-form-item label="银行卡号"><el-input v-model="form.bank_card" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="开户行"><el-input v-model="form.bank_name" /></el-form-item></el-col>
        </el-row>
        <el-row :gutter="12">
          <el-col :span="8"><el-form-item label="是否交行">
            <el-select v-model="form.is_bocom"><el-option value="否" /><el-option value="是" /></el-select>
          </el-form-item></el-col>
          <el-col :span="8"><el-form-item label="发放形式">
            <el-select v-model="form.payment_method">
              <el-option v-for="m in ['银行卡','现金','微信','交行代付']" :key="m" :value="m" />
            </el-select>
          </el-form-item></el-col>
          <el-col :span="8"><el-form-item label="社保状况">
            <el-select v-model="form.social_security">
              <el-option v-for="m in ['有社保','无社保','退休']" :key="m" :value="m" />
            </el-select>
          </el-form-item></el-col>
        </el-row>
        <el-row :gutter="12">
          <el-col :span="12"><el-form-item label="合同开始"><el-input v-model="form.contract_start" placeholder="yyyy-mm-dd" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="合同结束"><el-input v-model="form.contract_end" placeholder="yyyy-mm-dd" /></el-form-item></el-col>
        </el-row>
      </el-form>
      <template #footer>
        <el-button @click="dlg = false">取消</el-button>
        <el-button type="primary" @click="save">保存</el-button>
      </template>
    </el-dialog>
  </el-card>
</template>
<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'

const user = JSON.parse(localStorage.getItem('salary_user') || '{}')
const rows = ref([])
const kw = ref('')
const status = ref('')
const depts = ref([])
const positions = ref([])
const dlg = ref(false)
const form = ref(empty())

function empty() {
  return { id: 0, store_id: user.store_id, name: '', id_card: '', gender: '', age: 0,
    birth_date: '', status: '在职', department: '', position: '', phone: '', address: '',
    bank_card: '', bank_name: '', is_bocom: '否', payment_method: '银行卡', social_security: '有社保',
    contract_start: '', contract_end: '' }
}

async function load() {
  const { data } = await window.axios.get('/api/employees', { params: { store_id: user.store_id } })
  rows.value = data.filter(r =>
    (!kw.value || r.name.includes(kw.value) || r.phone.includes(kw.value) ||
     r.department.includes(kw.value) || r.position.includes(kw.value)) &&
    (!status.value || r.status === status.value))
}
function openEdit(row) {
  form.value = row ? { ...empty(), ...row } : empty()
  dlg.value = true
}
function parseId() {
  const id = form.value.id_card.trim()
  if (!/^\d{17}[\dXx]$/.test(id) && !/^\d{15}$/.test(id)) return ElMessage.warning('身份证格式不正确')
  const len = id.length
  const gender = (len === 18 ? +id[16] : +id[14]) % 2 ? '男' : '女'
  let b
  if (len === 18) b = `${id.slice(6,10)}-${id.slice(10,12)}-${id.slice(12,14)}`
  else b = `19${id.slice(6,8)}-${id.slice(8,10)}-${id.slice(10,12)}`
  const by = +b.split('-')[0], bm = +b.split('-')[1], bd = +b.split('-')[2]
  const now = new Date()
  let age = now.getFullYear() - by
  if (now.getMonth() + 1 < bm || (now.getMonth() + 1 === bm && now.getDate() < bd)) age--
  form.value.gender = gender; form.value.birth_date = b; form.value.age = age
  ElMessage.success(`识别成功：${gender} ${b} ${age}岁`)
}
async function save() {
  if (!form.value.name) return ElMessage.warning('姓名不能为空')
  await window.axios.post('/api/employees', form.value)
  ElMessage.success('已保存')
  dlg.value = false; load()
}
async function del(row) {
  await ElMessageBox.confirm(`确定删除员工「${row.name}」？删除需授权密码。`, '删除确认', { type: 'warning' })
  try {
    const { value } = await ElMessageBox.prompt('请输入授权密码 2555', '授权', { inputType: 'password' })
    if (value !== '2555') return ElMessage.error('密码错误')
  } catch (e) { return }
  await window.axios.delete(`/api/employees/${row.id}`)
  ElMessage.success('已删除'); load()
}
onMounted(async () => {
  const [d, p] = await Promise.all([
    window.axios.get('/api/global/departments'),
    window.axios.get('/api/global/positions')
  ])
  depts.value = d.data.map(x => x.name)
  positions.value = p.data
  load()
})
</script>
<style scoped>
.toolbar { display: flex; gap: 10px; align-items: center; margin-bottom: 12px; }
</style>

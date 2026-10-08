<template>
  <el-card shadow="never">
    <div class="toolbar">
      <el-select v-model="month" style="width:130px" @change="load">
        <el-option v-for="m in months" :key="m" :value="m" :label="m" />
      </el-select>
      <el-button type="primary" @click="load">查询</el-button>
      <div style="flex:1"></div>
      <el-button @click="exportCsv">导出CSV</el-button>
    </div>
    <el-table :data="rows" stripe height="calc(100vh - 320px)">
      <el-table-column prop="name" label="姓名" width="120" fixed />
      <el-table-column prop="department" label="部门" width="100" />
      <el-table-column prop="should_pay" label="应发" width="100" />
      <el-table-column prop="actual_pay" label="实发" width="100">
        <template #default="{ row }"><b style="color:#dc2626">{{ row.actual_pay }}</b></template>
      </el-table-column>
      <el-table-column prop="bocom_pay" label="交行代付" width="100" />
      <el-table-column prop="payment_method" label="发放形式" width="110" />
    </el-table>
    <el-divider>部门汇总</el-divider>
    <el-table :data="deptRows" size="small" border>
      <el-table-column prop="department" label="部门" />
      <el-table-column prop="cnt" label="人数" />
      <el-table-column prop="should" label="应发总计" />
      <el-table-column prop="actual" label="实发总计" />
    </el-table>
    <el-divider>发放形式统计</el-divider>
    <el-table :data="methodRows" size="small" border>
      <el-table-column prop="method" label="发放形式" />
      <el-table-column prop="cnt" label="人数" />
      <el-table-column prop="should" label="应发小计" />
      <el-table-column prop="actual" label="实发小计" />
      <el-table-column prop="bocom" label="交行代付" />
    </el-table>
  </el-card>
</template>
<script setup>
import { ref, onMounted } from 'vue'
const user = JSON.parse(localStorage.getItem('salary_user') || '{}')
const rows = ref([])
const months = ref([])
const month = ref('')
const deptRows = ref([])
const methodRows = ref([])

async function load() {
  const { data } = await window.axios.get('/api/payments', { params: { store_id: user.store_id, month: month.value } })
  rows.value = data
  // 部门汇总
  const dept = {}
  for (const r of data) {
    dept[r.department] = dept[r.department] || { department: r.department, cnt: 0, should: 0, actual: 0 }
    dept[r.department].cnt++; dept[r.department].should += r.should_pay; dept[r.department].actual += r.actual_pay
  }
  deptRows.value = Object.values(dept)
  deptRows.value.push({ department: '合计', cnt: data.length, should: sum('should_pay'), actual: sum('actual_pay') })
  // 发放形式统计
  const meth = {}
  for (const r of data) {
    meth[r.payment_method] = meth[r.payment_method] || { method: r.payment_method, cnt: 0, should: 0, actual: 0, bocom: 0 }
    meth[r.payment_method].cnt++; meth[r.payment_method].should += r.should_pay
    meth[r.payment_method].actual += r.actual_pay; meth[r.payment_method].bocom += r.bocom_pay
  }
  methodRows.value = Object.values(meth)
}
function sum(k) { return rows.value.reduce((s, r) => s + (r[k] || 0), 0) }
async function loadMonths() {
  const { data } = await window.axios.get('/api/salaries/months', { params: { store_id: user.store_id } })
  months.value = data.length ? data : [new Date().toISOString().slice(0,7)]
  if (!month.value || !data.includes(month.value)) month.value = months.value[0]
}
function exportCsv() {
  const lines = ['姓名,部门,应发,实发,交行代付,发放形式']
  for (const r of rows.value) lines.push([r.name, r.department, r.should_pay, r.actual_pay, r.bocom_pay, r.payment_method].join(','))
  lines.push('')
  lines.push('部门汇总'); lines.push('部门,人数,应发,实发')
  for (const d of deptRows.value) lines.push([d.department, d.cnt, d.should, d.actual].join(','))
  lines.push('')
  lines.push('发放形式统计'); lines.push('发放形式,人数,应发,实发,交行代付')
  for (const m of methodRows.value) lines.push([m.method, m.cnt, m.should, m.actual, m.bocom].join(','))
  const blob = new Blob(['\ufeff' + lines.join('\n')], { type: 'text/csv;charset=utf-8' })
  const a = document.createElement('a'); a.href = URL.createObjectURL(blob); a.download = `工资发放_${month.value}.csv`; a.click()
}
onMounted(async () => { await loadMonths(); load() })
</script>
<style scoped>
.toolbar { display: flex; gap: 10px; align-items: center; margin-bottom: 12px; }
</style>

<template>
  <el-card shadow="never">
    <div class="toolbar">
      <el-select v-model="month" style="width:130px" @change="load">
        <el-option v-for="m in months" :key="m" :value="m" :label="m" />
      </el-select>
      <el-button type="primary" @click="load">查询</el-button>
      <div style="flex:1"></div>
      <el-button @click="openEdit()"><el-icon><Plus /></el-icon>新增</el-button>
      <el-button @click="copyAll">复制整月</el-button>
      <el-button @click="exportCsv">导出工资条</el-button>
    </div>
    <el-table :data="rows" stripe height="calc(100vh - 260px)" @row-dblclick="row => openEdit(row)">
      <el-table-column prop="name" label="姓名" width="90" fixed />
      <el-table-column prop="month" label="月份" width="80" />
      <el-table-column prop="department" label="部门" width="90" />
      <el-table-column prop="position" label="职务" width="90" />
      <el-table-column prop="attendance_days" label="出勤" width="70" />
      <el-table-column prop="base_salary" label="基本" width="70" />
      <el-table-column prop="subtotal1" label="补助小计" width="80" />
      <el-table-column prop="bonus_salary" label="绩效" width="70" />
      <el-table-column prop="sales_commission" label="销售提成" width="80" />
      <el-table-column prop="overtime_pay" label="加班" width="70" />
      <el-table-column prop="total_salary" label="总计" width="80" />
      <el-table-column prop="total_deduction" label="扣款" width="70" />
      <el-table-column prop="tax" label="个税" width="70" />
      <el-table-column prop="actual_salary" label="实发" width="90">
        <template #default="{ row }"><b style="color:#dc2626">{{ row.actual_salary }}</b></template>
      </el-table-column>
      <el-table-column label="操作" width="120" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" @click="openEdit(row)">编辑</el-button>
          <el-button link type="danger" @click="del(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>
    <div class="footer-total">
      共 {{ rows.length }} 条 &nbsp; 总计应发 ¥{{ sum('total_salary') }} &nbsp; 总计实发 ¥{{ sum('actual_salary') }}
    </div>

    <el-dialog v-model="dlg" :title="form.id ? '编辑工资明细' : '添加工资明细'" width="760px" top="3vh">
      <div class="d-head">
        <el-select v-model="form.employee_id" placeholder="选择员工" style="width:260px" filterable @change="onEmp">
          <el-option v-for="e in empList" :key="e.id" :value="e.id"
                     :label="`${e.name}(${e.department}-${e.position})`" />
        </el-select>
        <el-select v-model="form.month" style="width:120px;margin-left:12px">
          <el-option v-for="m in months" :key="m" :value="m" :label="m" />
        </el-select>
      </div>
      <el-row :gutter="10">
        <el-col :span="6" v-for="f in income" :key="f.k">
          <el-form-item :label="f.l">
            <el-input-number v-model="form[f.k]" :disabled="f.auto" controls-position="right" style="width:100%" />
          </el-form-item>
        </el-col>
        <el-col :span="6" v-for="f in deduction" :key="f.k">
          <el-form-item :label="f.l">
            <el-input-number v-model="form[f.k]" :disabled="f.auto" controls-position="right" style="width:100%" />
          </el-form-item>
        </el-col>
      </el-row>
      <el-form-item label="备注">
        <el-input v-model="form.notes" type="textarea" :rows="3" />
      </el-form-item>
      <el-divider>计算结果</el-divider>
      <el-row :gutter="16">
        <el-col :span="6"><div class="res"><span>基本小计</span><b>{{ calc.subtotal1 }}</b></div></el-col>
        <el-col :span="6"><div class="res"><span>收入小计</span><b>{{ calc.subtotal2 }}</b></div></el-col>
        <el-col :span="6"><div class="res"><span>总计工资</span><b>{{ calc.total_salary }}</b></div></el-col>
        <el-col :span="6"><div class="res"><span>实发工资</span><b style="color:#dc2626">{{ calc.actual_salary }}</b></div></el-col>
      </el-row>
      <template #footer>
        <el-button @click="dlg = false">取消</el-button>
        <el-button type="primary" @click="save">保存</el-button>
      </template>
    </el-dialog>
  </el-card>
</template>
<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'

const user = JSON.parse(localStorage.getItem('salary_user') || '{}')
const rows = ref([])
const months = ref([])
const month = ref('')
const empList = ref([])
const dlg = ref(false)
const income = [
  { k: 'attendance_days', l: '出勤天数' }, { k: 'base_salary', l: '基本工资' },
  { k: 'ss_return', l: '社保返还' }, { k: 'performance_salary', l: '业绩工资' },
  { k: 'position_allowance', l: '职级补助' }, { k: 'holiday_salary', l: '节假日工资' },
  { k: 'bonus_salary', l: '绩效工资' }, { k: 'sales_commission', l: '销售提成' },
  { k: 'overtime_hours', l: '加班工时' }, { k: 'overtime_pay', l: '加班补助', auto: true },
  { k: 'other_allowance', l: '其他补助' }, { k: 'full_attendance', l: '全勤补助' }, { k: 'award', l: '奖金' }
]
const deduction = [
  { k: 'leave_days', l: '请假天数' }, { k: 'leave_deduction', l: '请假扣款', auto: true },
  { k: 'absent_days', l: '旷工天数' }, { k: 'absent_deduction', l: '旷工扣款', auto: true },
  { k: 'outing_hours', l: '外出工时' }, { k: 'outing_deduction', l: '外出扣款', auto: true },
  { k: 'discipline_deduction', l: '纪律扣款' }, { k: 'quality_deduction', l: '质控扣款' },
  { k: 'ss_paid', l: '社保代缴' }, { k: 'tax', l: '个税扣款' }
]

function empty() {
  const o = {}
  for (const f of [...income, ...deduction]) o[f.k] = 0
  return { id: 0, store_id: user.store_id, employee_id: null, month: '', notes: '', ...o }
}
const form = ref(empty())
const calc = computed(() => {
  const d = form.value
  const base = (d.base_salary||0) + (d.performance_salary||0) + (d.position_allowance||0) +
               (d.holiday_salary||0) + (d.bonus_salary||0) + (d.sales_commission||0)
  const m = (d.month || '').replace('-', '')
  let days = 30
  if (m) { const mo = +m.slice(4,6); if (mo===2) days = (+m.slice(0,4)%4===0&&+m.slice(0,4)%100!==0)||+m.slice(0,4)%400===0?29:28; else if([4,6,9,11].includes(mo)) days=30; else days=31 }
  const dw = days ? base/days : 0, hw = dw/10
  const ot = Math.round((d.overtime_hours||0)*hw*2)
  const leave = Math.round((d.leave_days||0)*dw)
  const out = Math.round((d.outing_hours||0)*hw)
  const ab = Math.round((d.absent_days||0)*dw*1.5)
  const sub1 = Math.round((d.base_salary||0)+(d.ss_return||0)+(d.performance_salary||0)+(d.position_allowance||0)+(d.holiday_salary||0))
  const sub2 = Math.round((d.bonus_salary||0)+(d.sales_commission||0)+ot+(d.other_allowance||0)+(d.full_attendance||0)+(d.award||0))
  const total = sub1 + sub2
  const ded = leave + ab + out + (d.discipline_deduction||0) + (d.quality_deduction||0) + (d.ss_paid||0)
  const actual = total - ded - (d.tax||0)
  return { subtotal1: sub1, subtotal2: sub2, total_salary: total, actual_salary: actual }
})

async function load() {
  const { data } = await window.axios.get('/api/salaries', { params: { store_id: user.store_id, month: month.value } })
  rows.value = data
}
async function loadMonths() {
  const { data } = await window.axios.get('/api/salaries/months', { params: { store_id: user.store_id } })
  months.value = data.length ? data : [new Date().toISOString().slice(0,7)]
  if (!month.value || !data.includes(month.value)) month.value = months.value[0]
}
function openEdit(row) {
  form.value = row ? { ...empty(), ...row } : empty()
  if (!form.value.month) form.value.month = month.value
  dlg.value = true
}
async function onEmp(id) {
  const emp = empList.value.find(e => e.id === id)
  if (!emp) return
  try {
    const { data } = await window.axios.get('/api/global/positions')
    const p = data.find(x => x.name === emp.position)
    if (p) form.value.position_allowance = p.allowance
  } catch (e) {}
  try {
    const { data } = await window.axios.get('/api/rules')
    const r = data.find(x => x.position === emp.position)
    if (r) { form.value.bonus_salary = r.perf_rate; form.value.sales_commission = r.sales_rate }
  } catch (e) {}
}
async function save() {
  if (!form.value.employee_id) return ElMessage.warning('请选择员工')
  form.value.month = form.value.month || month.value
  await window.axios.post('/api/salaries', form.value)
  ElMessage.success('已保存'); dlg.value = false; load(); loadMonths()
}
async function del(row) {
  await ElMessageBox.confirm(`删除「${row.name}」${row.month} 的工资记录？`, '删除确认', { type: 'warning' })
  try {
    const { value } = await ElMessageBox.prompt('请输入授权密码 2555', '授权', { inputType: 'password' })
    if (value !== '2555') return ElMessage.error('密码错误')
  } catch (e) { return }
  await window.axios.delete(`/api/salaries/${row.id}`)
  ElMessage.success('已删除'); load()
}
function copyAll() {
  ElMessageBox.prompt('复制当前页面全部数据到指定月份(yyyy-mm)', '复制整月', {
    inputValue: '2026-09', inputPattern: /^\d{4}-\d{2}$/, inputErrorMessage: '格式 yyyy-mm'
  }).then(async ({ value }) => {
    let n = 0
    for (const r of rows.value) {
      try {
        await window.axios.post('/api/salaries', { ...r, id: 0, month: value })
        n++
      } catch (e) { /* 跳过已存在 */ }
    }
    ElMessage.success(`已复制 ${n} 条到 ${value}`)
  }).catch(() => {})
}
function sum(k) { return rows.value.reduce((s, r) => s + (r[k] || 0), 0) }
function exportCsv() {
  const heads = ['编号','姓名','月份','部门','职务','出勤天数','基本工资','社保返还','业绩工资','职级补助','节假日工资','小计1','绩效工资','销售提成','加班工时','加班补助','其他补助','全勤补助','奖金','小计2','总计工资','请假天数','请假扣款','旷工天数','旷工扣款','外出工时','外出扣款','纪律扣款','质控扣款','社保代缴','应扣工资','扣个税','实发工资','备注']
  const lines = [heads.join(',')]
  for (const r of rows.value) lines.push([r.id, r.name, r.month, r.department, r.position, r.attendance_days,
    r.base_salary, r.ss_return, r.performance_salary, r.position_allowance, r.holiday_salary, r.subtotal1,
    r.bonus_salary, r.sales_commission, r.overtime_hours, r.overtime_pay, r.other_allowance, r.full_attendance,
    r.award, r.subtotal2, r.total_salary, r.leave_days, r.leave_deduction, r.absent_days, r.absent_deduction,
    r.outing_hours, r.outing_deduction, r.discipline_deduction, r.quality_deduction, r.ss_paid,
    r.total_deduction, r.tax, r.actual_salary, (r.notes||'').replace(/,/g,'，')].join(','))
  download(lines.join('\n'), `工资条_${month.value}.csv`)
}
function download(text, name) {
  const blob = new Blob(['\ufeff' + text], { type: 'text/csv;charset=utf-8' })
  const a = document.createElement('a'); a.href = URL.createObjectURL(blob); a.download = name
  a.click(); URL.revokeObjectURL(a.href)
}
onMounted(async () => {
  const { data } = await window.axios.get('/api/employees', { params: { store_id: user.store_id } })
  empList.value = data
  await loadMonths(); load()
})
</script>
<style scoped>
.toolbar { display: flex; gap: 10px; align-items: center; margin-bottom: 12px; }
.footer-total { margin-top: 10px; color: #475569; font-weight: 600; }
.d-head { margin-bottom: 10px; }
.res { background: #f1f5f9; border-radius: 8px; padding: 12px; text-align: center; }
.res span { display: block; color: #64748b; font-size: 12px; }
.res b { font-size: 20px; color: #2563eb; }
</style>

<template>
  <div>
    <!-- 店铺收入与人员概览卡片 -->
    <el-row :gutter="16" v-if="stats">
      <el-col :span="6" v-for="s in stats.store_stats" :key="s.store_id">
        <el-card shadow="hover" class="stat-card">
          <div class="s-name">{{ s.name }}</div>
          <div class="s-meta">员工 {{ s.total_emp }} 人（在职 {{ s.active_emp }}）· 工资 {{ s.salary_records }} 条</div>
          <el-row class="s-nums">
            <el-col :span="12"><div class="num-label">累计应发</div><div class="num" style="color:#d97706">¥{{ s.total_should.toLocaleString() }}</div></el-col>
            <el-col :span="12"><div class="num-label">累计实发</div><div class="num" style="color:#dc2626">¥{{ s.total_actual.toLocaleString() }}</div></el-col>
          </el-row>
          <div class="s-latest">最新月：{{ s.latest_month || '-' }}</div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="16" style="margin-top:16px">
      <el-col :span="12">
        <el-card shadow="hover">
          <template #header>各店铺累计收入（应发/实发）</template>
          <div ref="incomeChart" style="height:320px"></div>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card shadow="hover">
          <template #header>员工年龄分布</template>
          <div ref="ageChart" style="height:320px"></div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="16" style="margin-top:16px">
      <el-col :span="12">
        <el-card shadow="hover">
          <template #header>人员状态分布</template>
          <div ref="statusChart" style="height:300px"></div>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card shadow="hover">
          <template #header>部门人员分布</template>
          <div ref="deptChart" style="height:300px"></div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 店铺明细表 -->
    <el-card shadow="hover" style="margin-top:16px">
      <template #header>各店铺收入明细</template>
      <el-table :data="stats ? stats.store_stats : []" stripe>
        <el-table-column prop="name" label="商铺" width="120" />
        <el-table-column prop="total_emp" label="员工" width="70" />
        <el-table-column prop="active_emp" label="在职" width="70" />
        <el-table-column prop="salary_records" label="工资记录" width="90" />
        <el-table-column prop="total_should" label="累计应发" width="120">
          <template #default="{ row }">¥{{ row.total_should.toLocaleString() }}</template>
        </el-table-column>
        <el-table-column prop="total_actual" label="累计实发" width="120">
          <template #default="{ row }">¥{{ row.total_actual.toLocaleString() }}</template>
        </el-table-column>
        <el-table-column prop="latest_month" label="最新月" />
      </el-table>
    </el-card>
  </div>
</template>
<script setup>
import { ref, onMounted, nextTick } from 'vue'
import * as echarts from 'echarts'

const stats = ref(null)
const incomeChart = ref(null)
const ageChart = ref(null)
const statusChart = ref(null)
const deptChart = ref(null)

onMounted(async () => {
  const { data } = await window.axios.get('/api/admin/stats')
  stats.value = data
  await nextTick()
  render()
})

function render() {
  const s = stats.value
  // 各店铺累计收入（应发/实发分组柱状图）
  const names = s.store_stats.map(x => x.name)
  echarts.init(incomeChart.value).setOption({
    tooltip: { trigger: 'axis' },
    legend: { data: ['应发', '实发'] },
    grid: { left: 60, right: 30, top: 40, bottom: 30 },
    xAxis: { type: 'category', data: names },
    yAxis: { type: 'value' },
    series: [
      { name: '应发', type: 'bar', data: s.store_stats.map(x => x.total_should), itemStyle: { color: '#f59e0b' } },
      { name: '实发', type: 'bar', data: s.store_stats.map(x => x.total_actual), itemStyle: { color: '#ef4444' } }
    ]
  })
  // 年龄分布饼图
  echarts.init(ageChart.value).setOption({
    tooltip: { trigger: 'item' },
    legend: { orient: 'vertical', left: 'right' },
    series: [{
      type: 'pie', radius: '62%', center: ['45%', '52%'],
      label: { formatter: '{b}: {c}人' },
      data: s.age_dist.map(x => ({ name: x.name, value: x.value })),
      color: ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#14b8a6', '#64748b']
    }]
  })
  // 人员状态分布
  echarts.init(statusChart.value).setOption({
    tooltip: { trigger: 'item' },
    legend: { bottom: 0 },
    series: [{
      type: 'pie', radius: ['40%', '65%'], center: ['50%', '45%'],
      label: { formatter: '{b}: {c}人 ({d}%)' },
      data: [
        { name: '在职', value: s.status_dist['在职'] || 0 },
        { name: '离职', value: s.status_dist['离职'] || 0 }
      ],
      color: ['#10b981', '#94a3b8']
    }]
  })
  // 部门分布
  echarts.init(deptChart.value).setOption({
    tooltip: { trigger: 'axis' },
    grid: { left: 80, right: 30, top: 20, bottom: 30 },
    xAxis: { type: 'value' },
    yAxis: { type: 'category', data: s.dept_dist.map(x => x.name) },
    series: [{ type: 'bar', data: s.dept_dist.map(x => x.value), itemStyle: { color: '#2563eb' }, barWidth: 18 }]
  })
}
</script>
<style scoped>
.stat-card { margin-bottom: 8px; }
.s-name { font-size: 15px; font-weight: 700; color: #1e293b; }
.s-meta { color: #64748b; font-size: 12px; margin: 6px 0; }
.s-nums { margin-top: 8px; }
.num-label { color: #94a3b8; font-size: 12px; }
.num { font-size: 18px; font-weight: 700; margin-top: 2px; }
.s-latest { color: #64748b; font-size: 12px; margin-top: 8px; }
</style>

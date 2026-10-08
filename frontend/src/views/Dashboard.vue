<template>
  <div>
    <el-row :gutter="16">
      <el-col :span="6" v-for="c in cards" :key="c.label">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-label">{{ c.label }}</div>
          <div class="stat-value" :style="{ color: c.color }">{{ c.value }}</div>
        </el-card>
      </el-col>
    </el-row>
    <el-card shadow="hover" class="chart-card">
      <template #header>各月实发工资趋势</template>
      <div ref="chartEl" style="height:360px"></div>
    </el-card>
  </div>
</template>
<script setup>
import { ref, onMounted, nextTick } from 'vue'
import * as echarts from 'echarts'

const user = JSON.parse(localStorage.getItem('salary_user') || '{}')
const chartEl = ref(null)
const cards = ref([])

onMounted(async () => {
  const { data } = await window.axios.get('/api/dashboard', { params: { store_id: user.store_id } })
  cards.value = [
    { label: '员工总数', value: data.total_emp, color: '#2563eb' },
    { label: '在职人数', value: data.active_emp, color: '#16a34a' },
    { label: '最新月(' + (data.latest_month || '-') + ')应发', value: '¥' + (data.latest_should || 0), color: '#d97706' },
    { label: '最新月实发', value: '¥' + (data.latest_actual || 0), color: '#dc2626' }
  ]
  await nextTick()
  const chart = echarts.init(chartEl.value)
  chart.setOption({
    tooltip: { trigger: 'axis' },
    grid: { left: 60, right: 30, top: 30, bottom: 30 },
    xAxis: { type: 'category', data: data.monthly.map(m => m.month) },
    yAxis: { type: 'value' },
    series: [{
      type: 'line', smooth: true, data: data.monthly.map(m => m.actual),
      areaStyle: { opacity: .25 }, itemStyle: { color: '#2563eb' }, lineStyle: { width: 3 }
    }]
  })
})
</script>
<style scoped>
.stat-card { margin-bottom: 8px; }
.stat-label { color: #64748b; font-size: 14px; }
.stat-value { font-size: 26px; font-weight: 700; margin-top: 8px; }
.chart-card { margin-top: 8px; }
</style>

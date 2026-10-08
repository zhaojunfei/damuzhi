<template>
  <el-card shadow="never">
    <template #header>操作审计日志</template>
    <el-table :data="logs" stripe height="calc(100vh - 200px)">
      <el-table-column prop="created_at" label="时间" width="170" />
      <el-table-column prop="username" label="操作人" width="120" />
      <el-table-column prop="action" label="操作" width="150" />
      <el-table-column prop="detail" label="详情" />
    </el-table>
  </el-card>
</template>
<script setup>
import { ref, onMounted } from 'vue'
const logs = ref([])
onMounted(async () => {
  const { data } = await window.axios.get('/api/audit')
  logs.value = data
})
</script>

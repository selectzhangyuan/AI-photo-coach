<script setup lang="ts">
import { onMounted } from "vue";
import { storeToRefs } from "pinia";

import { useAnalysisStore } from "../stores/analysis";

const store = useAnalysisStore();
const { history, error } = storeToRefs(store);

function formatDate(value: string): string {
  return new Date(value).toLocaleString("zh-CN", { hour12: false });
}

onMounted(async () => {
  await store.fetchHistory();
});
</script>

<template>
  <section class="view">
    <article class="panel">
      <p class="panel-title">历史记录</p>
      <p class="panel-subtitle">展示最近 20 条分析任务。</p>

      <div v-if="history.length === 0" class="empty-state">暂无记录，先去分析一张照片。</div>

      <div v-else class="history-list">
        <div v-for="item in history" :key="item.task_id" class="history-item">
          <div class="history-head">
            <span class="history-status">{{ item.status }}</span>
            <span class="history-time">{{ formatDate(item.created_at) }}</span>
          </div>
          <p class="history-summary">{{ item.summary ?? "任务尚未生成可展示结果" }}</p>
        </div>
      </div>
    </article>

    <p v-if="error" class="error-text">{{ error }}</p>
  </section>
</template>


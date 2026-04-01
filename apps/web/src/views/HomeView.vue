<script setup lang="ts">
import { computed, onUnmounted, ref } from "vue";
import { storeToRefs } from "pinia";

import { useAnalysisStore } from "../stores/analysis";

const store = useAnalysisStore();
const { imagePreviewUrl, taskStatus, taskDetail, loading, error, isPolling } = storeToRefs(store);

const fileInputRef = ref<HTMLInputElement | null>(null);

const statusText = computed(() => {
  if (!taskStatus.value) return "未创建任务";
  if (taskStatus.value === "PENDING") return "任务排队中";
  if (taskStatus.value === "RUNNING") return "AI 正在分析";
  if (taskStatus.value === "SUCCEEDED") return "分析完成";
  return "分析失败";
});

const statusClass = computed(() => {
  if (!taskStatus.value) return "is-idle";
  if (taskStatus.value === "SUCCEEDED") return "is-success";
  if (taskStatus.value === "FAILED") return "is-failed";
  return "is-pending";
});

function openFilePicker(): void {
  fileInputRef.value?.click();
}

async function onFileChange(event: Event): Promise<void> {
  const target = event.target as HTMLInputElement;
  const file = target.files?.[0];
  if (!file) return;
  await store.handleUpload(file);
}

async function onAnalyzeClick(): Promise<void> {
  await store.createAnalysisTask();
}

async function onRetryClick(): Promise<void> {
  await store.retryCurrentTask();
}

onUnmounted(() => {
  store.stopPolling();
});
</script>

<template>
  <section class="view">
    <article class="panel">
      <p class="panel-title">上传照片</p>
      <p class="panel-subtitle">建议竖图或横图 1 张，单张 10MB 以内。</p>

      <input
        ref="fileInputRef"
        class="hidden-input"
        type="file"
        accept="image/*"
        @change="onFileChange"
      />
      <button class="btn btn-primary" type="button" :disabled="loading" @click="openFilePicker">
        选择照片
      </button>

      <figure v-if="imagePreviewUrl" class="preview-wrap">
        <img :src="imagePreviewUrl" alt="预览图" class="preview-image" />
      </figure>
    </article>

    <article class="panel">
      <p class="panel-title">创建分析任务</p>
      <div :class="['status-chip', statusClass]">{{ statusText }}</div>
      <button
        class="btn btn-accent"
        type="button"
        :disabled="loading || !imagePreviewUrl || isPolling"
        @click="onAnalyzeClick"
      >
        {{ isPolling ? "分析中..." : "开始分析" }}
      </button>
      <button
        v-if="taskStatus === 'FAILED'"
        class="btn btn-ghost"
        type="button"
        :disabled="loading"
        @click="onRetryClick"
      >
        重试任务
      </button>
    </article>

    <article v-if="taskDetail?.result" class="panel">
      <p class="panel-title">AI 点评</p>
      <p class="summary-text">{{ taskDetail.result.summary }}</p>

      <div class="suggestion-list">
        <div v-for="item in taskDetail.result.suggestions" :key="item.id" class="suggestion-item">
          <p class="suggestion-tag">{{ item.type }} · {{ item.priority }}</p>
          <p class="suggestion-text">{{ item.text }}</p>
        </div>
      </div>
    </article>

    <p v-if="error" class="error-text">{{ error }}</p>
  </section>
</template>


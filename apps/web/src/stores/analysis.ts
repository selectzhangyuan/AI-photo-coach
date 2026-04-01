import { defineStore } from "pinia";
import { ref } from "vue";

import {
  createTask,
  getHistory,
  getTaskDetail,
  retryTask,
  type HistoryItem,
  type TaskDetailResponse,
  type TaskStatus
} from "../api/analysis";
import { uploadImage } from "../api/images";

const POLL_INTERVAL = 1800;

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => {
    setTimeout(resolve, ms);
  });
}

export const useAnalysisStore = defineStore("analysis", () => {
  const imageId = ref<string | null>(null);
  const imagePreviewUrl = ref<string | null>(null);
  const taskId = ref<string | null>(null);
  const taskStatus = ref<TaskStatus | null>(null);
  const taskDetail = ref<TaskDetailResponse | null>(null);
  const history = ref<HistoryItem[]>([]);
  const loading = ref(false);
  const error = ref<string | null>(null);
  const isPolling = ref(false);

  async function handleUpload(file: File): Promise<void> {
    loading.value = true;
    error.value = null;
    try {
      const data = await uploadImage(file);
      imageId.value = data.image_id;
      if (imagePreviewUrl.value) {
        URL.revokeObjectURL(imagePreviewUrl.value);
      }
      imagePreviewUrl.value = URL.createObjectURL(file);
      taskId.value = null;
      taskStatus.value = null;
      taskDetail.value = null;
    } catch (err) {
      const message = err instanceof Error ? err.message : "上传失败";
      error.value = message;
    } finally {
      loading.value = false;
    }
  }

  async function createAnalysisTask(): Promise<void> {
    if (!imageId.value) {
      error.value = "请先上传图片";
      return;
    }

    loading.value = true;
    error.value = null;
    try {
      const data = await createTask(imageId.value);
      taskId.value = data.task_id;
      taskStatus.value = data.status;
      await pollTaskUntilDone(data.task_id);
    } catch (err) {
      const message = err instanceof Error ? err.message : "创建任务失败";
      error.value = message;
    } finally {
      loading.value = false;
    }
  }

  async function pollTaskUntilDone(targetTaskId: string): Promise<void> {
    isPolling.value = true;
    while (isPolling.value) {
      const detail = await getTaskDetail(targetTaskId);
      taskDetail.value = detail;
      taskStatus.value = detail.status;

      if (detail.status === "SUCCEEDED" || detail.status === "FAILED") {
        isPolling.value = false;
        await fetchHistory();
        return;
      }
      await sleep(POLL_INTERVAL);
    }
  }

  function stopPolling(): void {
    isPolling.value = false;
  }

  async function fetchHistory(): Promise<void> {
    try {
      const data = await getHistory(20);
      history.value = data.items;
    } catch (err) {
      const message = err instanceof Error ? err.message : "加载历史失败";
      error.value = message;
    }
  }

  async function retryCurrentTask(): Promise<void> {
    if (!taskId.value) {
      error.value = "当前没有可重试任务";
      return;
    }

    loading.value = true;
    error.value = null;
    try {
      await retryTask(taskId.value);
      await pollTaskUntilDone(taskId.value);
    } catch (err) {
      const message = err instanceof Error ? err.message : "重试失败";
      error.value = message;
    } finally {
      loading.value = false;
    }
  }

  return {
    imageId,
    imagePreviewUrl,
    taskId,
    taskStatus,
    taskDetail,
    history,
    loading,
    error,
    isPolling,
    handleUpload,
    createAnalysisTask,
    stopPolling,
    fetchHistory,
    retryCurrentTask
  };
});

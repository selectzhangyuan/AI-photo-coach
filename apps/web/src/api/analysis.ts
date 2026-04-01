import { http } from "./http";

export type TaskStatus = "PENDING" | "RUNNING" | "SUCCEEDED" | "FAILED";

export interface Suggestion {
  id: string;
  type: "composition" | "exposure" | "color" | "story" | "other";
  text: string;
  problem?: string;
  action?: string;
  priority: "high" | "medium" | "low";
}

export interface Annotation {
  id: string;
  source: "cv" | "llm" | "rule";
  category: string;
  geometry_type: "bbox" | "point" | "line" | "polygon";
  coords: Record<string, number | string>;
  label: string;
  message: string;
  confidence: number;
  related_suggestion_ids?: string[];
}

export interface EditAction {
  id: string;
  action_type: "crop" | "exposure" | "white_balance" | "contrast" | "saturation";
  source: "cv" | "llm" | "rule";
  params: Record<string, unknown>;
  reason: string;
  previewable: boolean;
  apply_mode: "destructive" | "non_destructive";
}

export interface AnalysisResult {
  version: string;
  summary: string;
  suggestions: Suggestion[];
  scores: Record<string, number> | null;
  features_ref?: { feature_id: string } | null;
  annotations: Annotation[];
  edit_actions: EditAction[];
}

export interface CreateTaskResponse {
  task_id: string;
  task_type: string;
  status: TaskStatus;
}

export interface TaskDetailResponse {
  task_id: string;
  image_id: string;
  task_type: string;
  status: TaskStatus;
  model_name: string;
  prompt_version: string;
  attempt_count: number;
  error_code: string | null;
  error_message: string | null;
  created_at: string;
  started_at: string | null;
  finished_at: string | null;
  result: AnalysisResult | null;
}

export interface HistoryItem {
  task_id: string;
  image_id: string;
  task_type: string;
  status: TaskStatus;
  created_at: string;
  finished_at: string | null;
  summary: string | null;
}

export interface HistoryResponse {
  items: HistoryItem[];
}

export async function createTask(imageId: string): Promise<CreateTaskResponse> {
  const { data } = await http.post<CreateTaskResponse>("/analysis/tasks", { image_id: imageId });
  return data;
}

export async function getTaskDetail(taskId: string): Promise<TaskDetailResponse> {
  const { data } = await http.get<TaskDetailResponse>(`/analysis/tasks/${taskId}`);
  return data;
}

export async function getHistory(limit = 20): Promise<HistoryResponse> {
  const { data } = await http.get<HistoryResponse>("/analysis/history", { params: { limit } });
  return data;
}

export async function retryTask(taskId: string): Promise<CreateTaskResponse> {
  const { data } = await http.post<CreateTaskResponse>(`/analysis/tasks/${taskId}/retry`);
  return data;
}

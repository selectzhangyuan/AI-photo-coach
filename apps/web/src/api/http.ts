import axios from "axios";

const baseURL = import.meta.env.VITE_API_BASE_URL ?? "/api/v1";
const userId = import.meta.env.VITE_USER_ID ?? "00000000-0000-0000-0000-000000000001";

export const http = axios.create({
  baseURL,
  timeout: 30000
});

http.interceptors.request.use((config) => {
  config.headers["X-User-Id"] = userId;
  return config;
});


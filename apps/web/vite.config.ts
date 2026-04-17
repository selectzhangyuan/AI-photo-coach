import { defineConfig, loadEnv } from "vite";
import vue from "@vitejs/plugin-vue";

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), "");
  const proxyTarget = env.VITE_DEV_API_PROXY_TARGET ?? "http://localhost:8000";

  return {
    plugins: [vue()],
    server: {
      host: "0.0.0.0",
      port: 5151,
      proxy: {
        "/api": {
          target: proxyTarget,
          changeOrigin: true
        },
        "/healthz": {
          target: proxyTarget,
          changeOrigin: true
        }
      }
    }
  };
});

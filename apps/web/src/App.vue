<script setup lang="ts">
import { computed } from "vue";
import { useRoute, useRouter } from "vue-router";
import { useAuthStore } from "./stores/auth";

const route = useRoute();
const router = useRouter();
const authStore = useAuthStore();

const tabs = [
  { key: "home", label: "分析", path: "/" },
  { key: "history", label: "历史", path: "/history" },
  { key: "profile", label: "个人", path: "/profile" },
];

const activePath = computed(() => route.path);

const displayName = computed(() => {
  if (!authStore.currentUser) return "";
  return authStore.currentUser.nickname ?? authStore.currentUser.email;
});

function go(path: string): void {
  if (route.path !== path) {
    void router.push(path);
  }
}

async function handleLogout(): Promise<void> {
  authStore.clearAuth();
  await router.push({ name: "login" });
}
</script>

<template>
  <div class="app-shell">
    <header class="app-header">
      <p class="app-kicker">AI Photo Coach</p>
      <div class="header-row">
        <h1 class="app-title">AI Photo Coach</h1>
        <template v-if="authStore.isAuthenticated">
          <span class="user-badge">{{ displayName }}</span>
          <button class="btn-logout" type="button" @click="handleLogout">登出</button>
        </template>
      </div>
    </header>

    <main class="app-main">
      <RouterView />
    </main>

    <nav v-if="authStore.isAuthenticated" class="tabbar">
      <button
        v-for="tab in tabs"
        :key="tab.key"
        type="button"
        :class="['tabbar-item', { 'is-active': activePath === tab.path }]"
        @click="go(tab.path)"
      >
        {{ tab.label }}
      </button>
    </nav>
  </div>
</template>

<style scoped>
.header-row {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-top: 4px;
}

.user-badge {
  font-size: 12px;
  color: var(--text-sub);
  background: rgba(18, 102, 79, 0.08);
  border-radius: 999px;
  padding: 3px 10px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 120px;
}

.btn-logout {
  border: 0;
  background: rgba(180, 35, 24, 0.1);
  color: var(--danger);
  font-size: 12px;
  font-weight: 600;
  border-radius: 999px;
  padding: 3px 10px;
  cursor: pointer;
}
</style>
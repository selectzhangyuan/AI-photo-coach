<script setup lang="ts">
import { computed } from "vue";
import { useRoute, useRouter } from "vue-router";

const route = useRoute();
const router = useRouter();

const tabs = [
  { key: "home", label: "分析", path: "/" },
  { key: "history", label: "历史", path: "/history" }
];

const activePath = computed(() => route.path);

function go(path: string): void {
  if (route.path !== path) {
    void router.push(path);
  }
}
</script>

<template>
  <div class="app-shell">
    <header class="app-header">
      <p class="app-kicker">AI Photo Coach</p>
      <h1 class="app-title">移动端摄影点评</h1>
    </header>

    <main class="app-main">
      <RouterView />
    </main>

    <nav class="tabbar">
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


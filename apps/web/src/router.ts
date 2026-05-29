import { createRouter, createWebHistory } from "vue-router";
import { useAuthStore } from "./stores/auth";

import HomeView from "./views/HomeView.vue";
import HistoryView from "./views/HistoryView.vue";
import LoginView from "./views/LoginView.vue";
import RegisterView from "./views/RegisterView.vue";
import ProfileView from "./views/ProfileView.vue";

export const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: "/login", name: "login", component: LoginView, meta: { guest: true } },
    { path: "/register", name: "register", component: RegisterView, meta: { guest: true } },
    { path: "/", name: "home", component: HomeView, meta: { requiresAuth: true } },
    { path: "/history", name: "history", component: HistoryView, meta: { requiresAuth: true } },
    { path: "/profile", name: "profile", component: ProfileView, meta: { requiresAuth: true } },
  ],
});

// 导航守卫
router.beforeEach((to) => {
  const authStore = useAuthStore();
  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    return { name: "login" };
  }
  if (to.meta.guest && authStore.isAuthenticated) {
    return { name: "home" };
  }
});
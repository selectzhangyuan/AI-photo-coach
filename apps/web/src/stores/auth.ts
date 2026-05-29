import { defineStore } from "pinia";
import { ref, computed } from "vue";
import type { UserProfile } from "../api/auth";

export const useAuthStore = defineStore("auth", () => {
  const accessToken = ref<string | null>(localStorage.getItem("access_token"));
  const refreshToken = ref<string | null>(localStorage.getItem("refresh_token"));
  const currentUser = ref<UserProfile | null>(null);

  const isAuthenticated = computed(() => !!accessToken.value);

  function setTokens(access: string, refresh: string) {
    accessToken.value = access;
    refreshToken.value = refresh;
    localStorage.setItem("access_token", access);
    localStorage.setItem("refresh_token", refresh);
  }

  function clearAuth() {
    accessToken.value = null;
    refreshToken.value = null;
    currentUser.value = null;
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
  }

  function setUser(user: UserProfile) {
    currentUser.value = user;
  }

  return {
    accessToken,
    refreshToken,
    currentUser,
    isAuthenticated,
    setTokens,
    clearAuth,
    setUser,
  };
});

<script setup lang="ts">
import { ref } from "vue";
import { useRouter } from "vue-router";
import { useAuthStore } from "../stores/auth";
import { login, getProfile } from "../api/auth";

const router = useRouter();
const authStore = useAuthStore();

const email = ref("");
const password = ref("");
const errorMsg = ref("");
const submitting = ref(false);

async function handleLogin(): Promise<void> {
  errorMsg.value = "";
  if (!email.value || !password.value) {
    errorMsg.value = "请填写邮箱和密码";
    return;
  }

  submitting.value = true;
  try {
    const { data } = await login({ email: email.value, password: password.value });
    authStore.setTokens(data.access_token, data.refresh_token);

    // 获取用户资料
    try {
      const profileRes = await getProfile();
      authStore.setUser(profileRes.data);
    } catch {
      // 获取资料失败不影响登录跳转
    }

    await router.push({ name: "home" });
  } catch (err: any) {
    const status = err.response?.status;
    if (status === 401 || status === 400) {
      errorMsg.value = "邮箱或密码错误";
    } else {
      errorMsg.value = "登录失败，请稍后重试";
    }
  } finally {
    submitting.value = false;
  }
}
</script>

<template>
  <section class="view">
    <article class="panel">
      <p class="panel-title">登录</p>
      <p class="panel-subtitle">登录后即可使用 photo功能。</p>

      <form class="auth-form" @submit.prevent="handleLogin">
        <label class="form-label">
          <span>邮箱</span>
          <input v-model="email" type="email" placeholder="your@email.com" required autocomplete="email" />
        </label>

        <label class="form-label">
          <span>密码</span>
          <input v-model="password" type="password" placeholder="输入密码" required autocomplete="current-password" />
        </label>

        <p v-if="errorMsg" class="error-text">{{ errorMsg }}</p>

        <button class="btn btn-primary" type="submit" :disabled="submitting">
          {{ submitting ? "登录中..." : "登录" }}
        </button>

        <!-- 社交登录预留位 -->
        <!-- <div class="social-login-divider">或使用以下方式登录</div>
        <button class="btn btn-ghost" type="button">Google 登录</button>
        <button class="btn btn-ghost" type="button">微信登录</button> -->
      </form>
    </article>

    <p class="auth-link">
      没有账号？<router-link :to="{ name: 'register' }">去注册</router-link>
    </p>
  </section>
</template>

<style scoped>
.auth-form {
  display: grid;
  gap: 14px;
}

.form-label {
  display: grid;
  gap: 6px;
}

.form-label span {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-sub);
}

.form-label input {
  width: 100%;
  border: 1px solid var(--surface-border);
  border-radius: var(--radius-lg);
  padding: 10px 12px;
  font-size: 15px;
  background: rgba(255, 255, 255, 0.6);
  outline: none;
  transition: border-color 160ms ease;
}

.form-label input:focus {
  border-color: var(--primary);
}

.auth-link {
  text-align: center;
  font-size: 14px;
  color: var(--text-sub);
}

.auth-link a {
  color: var(--primary);
  font-weight: 600;
}
</style>
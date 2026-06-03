<script setup lang="ts">
import { ref } from "vue";
import { useRouter } from "vue-router";
import { useAuthStore } from "../stores/auth";
import { register, getProfile, type RegisterParams } from "../api/auth";

const router = useRouter();
const authStore = useAuthStore();

const email = ref("");
const password = ref("");
const confirmPassword = ref("");
const nickname = ref("");
const errorMsg = ref("");
const submitting = ref(false);

function validate(): string | null {
  if (!email.value) return "请填写邮箱";
  if (!password.value) return "请填写密码";
  if (password.value.length < 8) return "密码至少需要 8 位";
  if (password.value !== confirmPassword.value) return "两次密码不一致";
  return null;
}

async function handleRegister(): Promise<void> {
  errorMsg.value = "";
  const validationError = validate();
  if (validationError) {
    errorMsg.value = validationError;
    return;
  }

  submitting.value = true;
  try {
    const params: RegisterParams = {
      email: email.value,
      password: password.value,
    };
    if (nickname.value.trim()) {
      params.nickname = nickname.value.trim();
    }

    const { data } = await register(params);
    // 注册成功后自动登录
    authStore.setTokens(data.access_token, data.refresh_token);

    try {
      const profileRes = await getProfile();
      authStore.setUser(profileRes.data);
    } catch {
      // 获取资料失败不影响跳转
    }

    await router.push({ name: "home" });
  } catch (err: any) {
    const status = err.response?.status;
    if (status === 409) {
      errorMsg.value = "该邮箱已被注册";
    } else if (status === 400) {
      errorMsg.value = "注册信息不合法，请检查输入";
    } else {
      errorMsg.value = "注册失败，请稍后重试";
    }
  } finally {
    submitting.value = false;
  }
}
</script>

<template>
  <section class="view">
    <article class="panel">
      <p class="panel-title">注册</p>
      <p class="panel-subtitle">创建账号，解锁 photo功能。</p>

      <form class="auth-form" @submit.prevent="handleRegister">
        <label class="form-label">
          <span>邮箱</span>
          <input v-model="email" type="email" placeholder="your@email.com" required autocomplete="email" />
        </label>

        <label class="form-label">
          <span>昵称（可选）</span>
          <input v-model="nickname" type="text" placeholder="给自己取个名字" autocomplete="nickname" />
        </label>

        <label class="form-label">
          <span>密码</span>
          <input
            v-model="password"
            type="password"
            placeholder="至少 8 位"
            required
            minlength="8"
            autocomplete="new-password"
          />
        </label>

        <label class="form-label">
          <span>确认密码</span>
          <input v-model="confirmPassword" type="password" placeholder="再次输入密码" required autocomplete="new-password" />
        </label>

        <p v-if="errorMsg" class="error-text">{{ errorMsg }}</p>

        <button class="btn btn-primary" type="submit" :disabled="submitting">
          {{ submitting ? "注册中..." : "注册" }}
        </button>
      </form>
    </article>

    <p class="auth-link">
      已有账号？<router-link :to="{ name: 'login' }">去登录</router-link>
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
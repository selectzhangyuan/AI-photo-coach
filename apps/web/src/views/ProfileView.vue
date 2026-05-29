<script setup lang="ts">
import { ref, onMounted } from "vue";
import { useAuthStore } from "../stores/auth";
import { getProfile, updateProfile, changePassword } from "../api/auth";

const authStore = useAuthStore();

// 用户资料区
const nickname = ref("");
const avatarUrl = ref("");
const profileLoaded = ref(false);
const profileMsg = ref("");
const profileError = ref("");
const profileSubmitting = ref(false);

// 修改密码区
const currentPassword = ref("");
const newPassword = ref("");
const confirmNewPassword = ref("");
const passwordMsg = ref("");
const passwordError = ref("");
const passwordSubmitting = ref(false);

onMounted(async () => {
  await loadProfile();
});

async function loadProfile(): Promise<void> {
  try {
    const { data } = await getProfile();
    authStore.setUser(data);
    nickname.value = data.nickname ?? "";
    avatarUrl.value = data.avatar_url ?? "";
    profileLoaded.value = true;
  } catch {
    profileError.value = "加载用户资料失败";
  }
}

async function handleUpdateProfile(): Promise<void> {
  profileMsg.value = "";
  profileError.value = "";
  profileSubmitting.value = true;
  try {
    const { data } = await updateProfile({
      nickname: nickname.value.trim() || undefined,
      avatar_url: avatarUrl.value.trim() || undefined,
    });
    authStore.setUser(data);
    profileMsg.value = "资料已更新";
  } catch {
    profileError.value = "更新失败，请稍后重试";
  } finally {
    profileSubmitting.value = false;
  }
}

async function handleChangePassword(): Promise<void> {
  passwordMsg.value = "";
  passwordError.value = "";
  if (!currentPassword.value || !newPassword.value || !confirmNewPassword.value) {
    passwordError.value = "请填写所有密码字段";
    return;
  }
  if (newPassword.value.length < 8) {
    passwordError.value = "新密码至少需要 8 位";
    return;
  }
  if (newPassword.value !== confirmNewPassword.value) {
    passwordError.value = "两次新密码不一致";
    return;
  }

  passwordSubmitting.value = true;
  try {
    await changePassword({
      current_password: currentPassword.value,
      new_password: newPassword.value,
    });
    passwordMsg.value = "密码已修改";
    currentPassword.value = "";
    newPassword.value = "";
    confirmNewPassword.value = "";
  } catch (err: any) {
    const status = err.response?.status;
    if (status === 400) {
      passwordError.value = "当前密码不正确";
    } else {
      passwordError.value = "修改失败，请稍后重试";
    }
  } finally {
    passwordSubmitting.value = false;
  }
}
</script>

<template>
  <section class="view">
    <!-- 用户资料展示 -->
    <article class="panel">
      <p class="panel-title">个人资料</p>

      <template v-if="profileLoaded && authStore.currentUser">
        <div class="profile-info">
          <div class="info-row">
            <span class="info-label">邮箱</span>
            <span class="info-value">{{ authStore.currentUser.email }}</span>
          </div>
          <div class="info-row">
            <span class="info-label">昵称</span>
            <span class="info-value">{{ authStore.currentUser.nickname ?? "未设置" }}</span>
          </div>
          <div class="info-row">
            <span class="info-label">头像</span>
            <span class="info-value">{{ authStore.currentUser.avatar_url ?? "未设置" }}</span>
          </div>
          <div class="info-row">
            <span class="info-label">验证状态</span>
            <span :class="['status-chip', authStore.currentUser.is_verified ? 'is-success' : 'is-pending']">
              {{ authStore.currentUser.is_verified ? "已验证" : "未验证" }}
            </span>
          </div>
        </div>
      </template>
      <p v-if="profileError" class="error-text">{{ profileError }}</p>
    </article>

    <!-- 编辑资料区 -->
    <article class="panel">
      <p class="panel-title">编辑资料</p>
      <p class="panel-subtitle">修改昵称和头像链接。</p>

      <form class="auth-form" @submit.prevent="handleUpdateProfile">
        <label class="form-label">
          <span>昵称</span>
          <input v-model="nickname" type="text" placeholder="给自己取个名字" />
        </label>

        <label class="form-label">
          <span>头像 URL</span>
          <input v-model="avatarUrl" type="url" placeholder="https://example.com/avatar.jpg" />
        </label>

        <p v-if="profileError" class="error-text">{{ profileError }}</p>
        <p v-if="profileMsg" class="success-text">{{ profileMsg }}</p>

        <button class="btn btn-primary" type="submit" :disabled="profileSubmitting">
          {{ profileSubmitting ? "保存中..." : "保存" }}
        </button>
      </form>
    </article>

    <!-- 修改密码区 -->
    <article class="panel">
      <p class="panel-title">修改密码</p>
      <p class="panel-subtitle">新密码至少 8 位。</p>

      <form class="auth-form" @submit.prevent="handleChangePassword">
        <label class="form-label">
          <span>当前密码</span>
          <input v-model="currentPassword" type="password" placeholder="输入当前密码" required autocomplete="current-password" />
        </label>

        <label class="form-label">
          <span>新密码</span>
          <input v-model="newPassword" type="password" placeholder="至少 8 位" required minlength="8" autocomplete="new-password" />
        </label>

        <label class="form-label">
          <span>确认新密码</span>
          <input v-model="confirmNewPassword" type="password" placeholder="再次输入新密码" required autocomplete="new-password" />
        </label>

        <p v-if="passwordError" class="error-text">{{ passwordError }}</p>
        <p v-if="passwordMsg" class="success-text">{{ passwordMsg }}</p>

        <button class="btn btn-accent" type="submit" :disabled="passwordSubmitting">
          {{ passwordSubmitting ? "修改中..." : "修改密码" }}
        </button>
      </form>
    </article>
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

.profile-info {
  display: grid;
  gap: 10px;
}

.info-row {
  display: flex;
  align-items: center;
  gap: 10px;
}

.info-label {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-sub);
  min-width: 70px;
}

.info-value {
  font-size: 15px;
}

.success-text {
  color: var(--success);
  font-size: 13px;
}
</style>
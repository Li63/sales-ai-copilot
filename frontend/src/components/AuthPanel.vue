<script setup lang="ts">
import { ref } from 'vue'
import { showToast } from 'vant'

const emit = defineEmits<{
  login: [username: string, password: string]
  register: [username: string, password: string, displayName: string, role: string, tenantName: string]
}>()

const mode = ref<'login' | 'register'>('login')
const username = ref('')
const password = ref('')
const displayName = ref('')
const role = ref<'sales' | 'tenant_admin'>('sales')
const tenantName = ref('')

function submit() {
  if (!username.value.trim() || !password.value.trim()) {
    showToast('请输入账号和密码')
    return
  }
  if (mode.value === 'login') {
    emit('login', username.value.trim(), password.value)
    return
  }
  emit('register', username.value.trim(), password.value, displayName.value.trim(), role.value, tenantName.value.trim())
}
</script>

<template>
  <section class="auth-panel">
    <div class="brand-block">
      <span>Sales AI Workspace</span>
      <h1>销冠副驾</h1>
      <p>每位销售都有独立账号、行业指南、客户记忆和专属话术分析。</p>
    </div>

    <div class="auth-card">
      <div class="switcher">
        <button :class="{ active: mode === 'login' }" type="button" @click="mode = 'login'">登录</button>
        <button :class="{ active: mode === 'register' }" type="button" @click="mode = 'register'">注册</button>
      </div>

      <label>
        <span>账号</span>
        <input v-model="username" autocomplete="username" placeholder="请输入账号" />
      </label>

      <label v-if="mode === 'register'">
        <span>姓名或昵称</span>
        <input v-model="displayName" placeholder="用于你的个人后台" />
      </label>

      <div v-if="mode === 'register'" class="role-switch">
        <button :class="{ active: role === 'sales' }" type="button" @click="role = 'sales'">销售账号</button>
        <button :class="{ active: role === 'tenant_admin' }" type="button" @click="role = 'tenant_admin'">企业账号</button>
      </div>

      <label v-if="mode === 'register'">
        <span>{{ role === 'tenant_admin' ? '企业名称' : '所属企业' }}</span>
        <input v-model="tenantName" :placeholder="role === 'tenant_admin' ? '请输入企业名称' : '不填则进入默认企业'" />
      </label>

      <label>
        <span>密码</span>
        <input v-model="password" autocomplete="current-password" placeholder="请输入密码" type="password" />
      </label>

      <button class="primary" type="button" @click="submit">
        {{ mode === 'login' ? '进入工作台' : '创建专属账号' }}
      </button>
    </div>

    <div class="trust-strip">
      <span>独立记忆</span>
      <span>手动发送</span>
      <span>客户隔离</span>
    </div>
  </section>
</template>

<style scoped>
.auth-panel {
  position: relative;
  overflow: hidden;
  display: grid;
  align-content: start;
  gap: 16px;
  min-height: 100vh;
  padding: 26px 14px;
  background:
    radial-gradient(circle at 88% 6%, oklch(0.84 0.1 82 / 0.68), transparent 220px),
    linear-gradient(180deg, oklch(0.24 0.056 226) 0, oklch(0.39 0.09 178) 190px, transparent 190px),
    var(--bg);
}

.brand-block {
  min-height: 148px;
  color: white;
}

.brand-block span {
  display: inline-block;
  margin-bottom: 10px;
  padding: 5px 9px;
  border: 1px solid oklch(1 0 0 / 0.28);
  border-radius: 999px;
  color: oklch(0.9 0.052 175);
  background: oklch(1 0 0 / 0.08);
  font-size: 11px;
  font-weight: 950;
}

h1 {
  margin: 0;
  font-size: 32px;
  letter-spacing: -0.06em;
  line-height: 1.15;
}

p {
  margin: 10px 0 0;
  max-width: 310px;
  color: oklch(0.93 0.02 185);
  font-size: 13px;
  line-height: 1.6;
}

.auth-card {
  display: grid;
  gap: 13px;
  padding: 16px;
  border: 1px solid oklch(1 0 0 / 0.62);
  border-radius: var(--radius-lg);
  background: oklch(1 0.004 95 / 0.9);
  box-shadow: var(--shadow);
  backdrop-filter: blur(16px);
}

.switcher {
  display: grid;
  grid-template-columns: 1fr 1fr;
  padding: 4px;
  border: 1px solid oklch(0.86 0.021 105);
  border-radius: 16px;
  background: oklch(0.965 0.018 104);
}

.role-switch {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
}

.role-switch button {
  height: 36px;
  border: 1px solid oklch(0.86 0.021 105);
  border-radius: 14px;
  color: var(--muted);
  background: oklch(1 0.004 95 / 0.76);
  font-weight: 800;
}

.role-switch .active {
  color: var(--brand-strong);
  border-color: oklch(0.78 0.055 175);
  background: var(--brand-soft);
}

.switcher button,
.primary {
  height: 40px;
  border: 0;
  border-radius: 14px;
  font-weight: 800;
}

.switcher button {
  color: var(--muted);
  background: transparent;
}

.switcher .active {
  color: var(--brand-strong);
  background: white;
  box-shadow: var(--shadow-tiny);
}

label {
  display: grid;
  gap: 6px;
}

label span {
  color: var(--muted);
  font-size: 12px;
  font-weight: 700;
}

input {
  width: 100%;
  height: 42px;
  border: 1px solid oklch(0.86 0.021 105);
  border-radius: 14px;
  padding: 0 12px;
  color: var(--ink);
  background: oklch(1 0.004 95 / 0.78);
}

.primary {
  margin-top: 2px;
  color: white;
  background:
    radial-gradient(circle at 88% 8%, var(--accent), transparent 48px),
    linear-gradient(135deg, var(--brand-strong), var(--brand));
  box-shadow: 0 14px 28px oklch(0.34 0.095 184 / 0.22);
}

.trust-strip {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px;
}

.trust-strip span {
  padding: 8px 6px;
  border: 1px solid oklch(0.88 0.018 105);
  border-radius: 14px;
  color: var(--muted);
  background: oklch(1 0 0 / 0.72);
  text-align: center;
  font-size: 12px;
  font-weight: 700;
}
</style>

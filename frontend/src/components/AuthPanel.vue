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
  display: grid;
  align-content: start;
  gap: 14px;
  min-height: 100vh;
  padding: 22px 14px;
  background:
    linear-gradient(180deg, oklch(0.26 0.05 230) 0, oklch(0.36 0.07 180) 178px, transparent 178px),
    var(--bg);
}

.brand-block {
  min-height: 138px;
  color: white;
}

.brand-block span {
  display: inline-block;
  margin-bottom: 10px;
  padding: 4px 8px;
  border: 1px solid oklch(1 0 0 / 0.18);
  border-radius: 999px;
  color: oklch(0.86 0.05 175);
  font-size: 11px;
  font-weight: 800;
}

h1 {
  margin: 0;
  font-size: 28px;
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
  gap: 12px;
  padding: 14px;
  border: 1px solid var(--line);
  border-radius: 8px;
  background: var(--surface);
  box-shadow: var(--shadow);
}

.switcher {
  display: grid;
  grid-template-columns: 1fr 1fr;
  padding: 3px;
  border: 1px solid var(--line);
  border-radius: 8px;
  background: var(--surface-soft);
}

.role-switch {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
}

.role-switch button {
  height: 36px;
  border: 1px solid var(--line);
  border-radius: 8px;
  color: var(--muted);
  background: white;
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
  border-radius: 6px;
  font-weight: 800;
}

.switcher button {
  color: var(--muted);
  background: transparent;
}

.switcher .active {
  color: var(--brand-strong);
  background: white;
  box-shadow: 0 2px 8px oklch(0.18 0.02 245 / 0.08);
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
  border: 1px solid var(--line);
  border-radius: 8px;
  padding: 0 12px;
  color: var(--ink);
  background: var(--surface-raised);
}

.primary {
  margin-top: 2px;
  color: white;
  background: var(--brand);
  box-shadow: 0 8px 18px oklch(0.38 0.11 175 / 0.22);
}

.trust-strip {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px;
}

.trust-strip span {
  padding: 8px 6px;
  border: 1px solid var(--line);
  border-radius: 8px;
  color: var(--muted);
  background: oklch(1 0 0 / 0.72);
  text-align: center;
  font-size: 12px;
  font-weight: 700;
}
</style>

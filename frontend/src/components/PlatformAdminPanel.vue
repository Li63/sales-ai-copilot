<script setup lang="ts">
import { ref } from 'vue'
import { showToast } from 'vant'
import type { Tenant } from '../stores/sidebar'

defineProps<{
  tenants: Tenant[]
}>()

const emit = defineEmits<{
  createTenant: [payload: { name: string; contact_name?: string; contact_phone?: string }]
  createTenantAdmin: [payload: { tenant_id: number; username: string; password: string; display_name?: string }]
  updateTenantStatus: [tenantId: number, status: string]
}>()

const tenantName = ref('')
const contactName = ref('')
const contactPhone = ref('')
const adminTenantId = ref<number | null>(null)
const adminUsername = ref('')
const adminPassword = ref('')
const adminName = ref('')

function submitTenant() {
  if (!tenantName.value.trim()) {
    showToast('请填写企业名称')
    return
  }
  emit('createTenant', {
    name: tenantName.value.trim(),
    contact_name: contactName.value.trim(),
    contact_phone: contactPhone.value.trim()
  })
  tenantName.value = ''
  contactName.value = ''
  contactPhone.value = ''
}

function submitAdmin() {
  if (!adminTenantId.value || !adminUsername.value.trim() || adminPassword.value.length < 6) {
    showToast('请选择企业，并填写管理员账号和至少 6 位密码')
    return
  }
  emit('createTenantAdmin', {
    tenant_id: adminTenantId.value,
    username: adminUsername.value.trim(),
    password: adminPassword.value,
    display_name: adminName.value.trim()
  })
  adminUsername.value = ''
  adminPassword.value = ''
  adminName.value = ''
}
</script>

<template>
  <section class="admin-page">
    <div class="hero">
      <span>总后台</span>
      <strong>多商户企业管理</strong>
      <p>当前审核能力已预留，默认不拦截销售端调试；后续打开审核开关即可生效。</p>
    </div>

    <div class="metric-grid">
      <article>
        <span>企业数量</span>
        <strong>{{ tenants.length }}</strong>
      </article>
      <article>
        <span>销售总数</span>
        <strong>{{ tenants.reduce((sum, item) => sum + (item.sales_count || 0), 0) }}</strong>
      </article>
    </div>

    <article class="panel">
      <div class="panel-head">
        <strong>开通企业</strong>
        <span>平台创建</span>
      </div>
      <input v-model="tenantName" placeholder="企业名称" />
      <input v-model="contactName" placeholder="联系人" />
      <input v-model="contactPhone" placeholder="联系方式" />
      <button class="primary" type="button" @click="submitTenant">创建企业</button>
    </article>

    <article class="panel">
      <div class="panel-head">
        <strong>添加企业管理员</strong>
        <span>上级添加</span>
      </div>
      <select v-model.number="adminTenantId">
        <option :value="null">选择企业</option>
        <option v-for="tenant in tenants" :key="tenant.id" :value="tenant.id">{{ tenant.name }}</option>
      </select>
      <input v-model="adminName" placeholder="管理员姓名" />
      <input v-model="adminUsername" placeholder="管理员账号" />
      <input v-model="adminPassword" placeholder="初始密码，至少 6 位" type="password" />
      <button class="primary" type="button" @click="submitAdmin">创建企业管理员</button>
    </article>

    <article class="panel">
      <div class="panel-head">
        <strong>企业列表</strong>
        <span>{{ tenants.length }} 家</span>
      </div>
      <div class="list">
        <div v-for="tenant in tenants" :key="tenant.id" class="row">
          <div>
            <strong>{{ tenant.name }}</strong>
            <p>{{ tenant.contact_name || '未填联系人' }} · 销售 {{ tenant.sales_count || 0 }} 人</p>
          </div>
          <select :value="tenant.status" @change="emit('updateTenantStatus', tenant.id, ($event.target as HTMLSelectElement).value)">
            <option value="approved">已开通</option>
            <option value="pending">待审核</option>
            <option value="rejected">已拒绝</option>
            <option value="disabled">已停用</option>
          </select>
        </div>
      </div>
    </article>
  </section>
</template>

<style scoped>
.admin-page {
  display: grid;
  gap: 12px;
  padding: 12px;
}

.hero,
.panel,
.metric-grid article,
.row {
  border: 1px solid var(--line);
  border-radius: 8px;
  background: var(--surface);
  box-shadow: var(--shadow-soft);
}

.hero {
  padding: 16px;
  color: white;
  background: linear-gradient(135deg, oklch(0.28 0.045 220), oklch(0.42 0.085 175));
}

.hero span,
.panel-head span,
.metric-grid span {
  color: var(--muted);
  font-size: 12px;
  font-weight: 800;
}

.hero span {
  color: oklch(0.84 0.055 178);
}

.hero strong {
  display: block;
  margin-top: 5px;
  font-size: 21px;
}

.hero p,
.row p {
  margin: 7px 0 0;
  color: var(--muted);
  font-size: 13px;
  line-height: 1.5;
}

.hero p {
  color: oklch(0.94 0.018 190);
}

.metric-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 8px;
}

.metric-grid article,
.panel,
.row {
  padding: 13px;
}

.metric-grid strong {
  display: block;
  margin-top: 5px;
  color: var(--ink);
  font-size: 22px;
}

.panel {
  display: grid;
  gap: 10px;
}

.panel-head,
.row {
  display: flex;
  justify-content: space-between;
  gap: 10px;
}

.panel-head strong,
.row strong {
  color: var(--ink);
  font-size: 15px;
}

input,
select {
  width: 100%;
  height: 40px;
  border: 1px solid var(--line);
  border-radius: 8px;
  padding: 0 10px;
  color: var(--ink);
  background: var(--surface-raised);
}

.primary {
  height: 39px;
  border: 0;
  border-radius: 8px;
  color: white;
  background: var(--brand);
  font-weight: 900;
}

.list {
  display: grid;
  gap: 8px;
}

.row {
  align-items: center;
  box-shadow: none;
}

.row select {
  width: 96px;
}
</style>

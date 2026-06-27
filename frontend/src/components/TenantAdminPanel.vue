<script setup lang="ts">
import { ref } from 'vue'
import { showToast } from 'vant'
import type { CompanyMaterial, TenantOverview, UserProfile } from '../stores/sidebar'
import CompanyMaterialPanel from './CompanyMaterialPanel.vue'

defineProps<{
  overview: TenantOverview | null
  sales: UserProfile[]
  materials: CompanyMaterial[]
}>()

const emit = defineEmits<{
  createSales: [payload: { username: string; password: string; display_name?: string }]
  updateSalesStatus: [userId: number, status: string]
  updateMaterialStatus: [materialId: number, status: string]
  addMaterial: [payload: { title: string; content: string; source_type: string; scope?: string }]
}>()

const salesName = ref('')
const salesUsername = ref('')
const salesPassword = ref('')

function submitSales() {
  if (!salesUsername.value.trim() || salesPassword.value.length < 6) {
    showToast('请填写销售账号和至少 6 位密码')
    return
  }
  emit('createSales', {
    username: salesUsername.value.trim(),
    password: salesPassword.value,
    display_name: salesName.value.trim()
  })
  salesName.value = ''
  salesUsername.value = ''
  salesPassword.value = ''
}

function addTenantMaterial(payload: { title: string; content: string; source_type: string; scope?: string }) {
  emit('addMaterial', { ...payload, scope: 'tenant' })
}
</script>

<template>
  <section class="tenant-page">
    <div class="hero">
      <span>企业端</span>
      <strong>{{ overview?.tenant.name || '企业管理后台' }}</strong>
      <p>企业资料库上传后，本企业销售会自动使用；销售提交资料先进入状态流，当前审核开关未开启。</p>
    </div>

    <div class="metric-grid">
      <article>
        <span>销售人数</span>
        <strong>{{ overview?.sales_count || 0 }}</strong>
      </article>
      <article>
        <span>资料数量</span>
        <strong>{{ overview?.material_count || 0 }}</strong>
      </article>
      <article>
        <span>待审销售</span>
        <strong>{{ overview?.pending_sales || 0 }}</strong>
      </article>
      <article>
        <span>待审资料</span>
        <strong>{{ overview?.pending_materials || 0 }}</strong>
      </article>
    </div>

    <CompanyMaterialPanel :materials="materials" @add="addTenantMaterial" />

    <article class="panel">
      <div class="panel-head">
        <strong>添加销售账号</strong>
        <span>企业上级添加</span>
      </div>
      <input v-model="salesName" placeholder="销售姓名" />
      <input v-model="salesUsername" placeholder="销售账号" />
      <input v-model="salesPassword" placeholder="初始密码，至少 6 位" type="password" />
      <button class="primary" type="button" @click="submitSales">创建销售账号</button>
    </article>

    <article class="panel">
      <div class="panel-head">
        <strong>销售使用情况</strong>
        <span>{{ sales.length }} 人</span>
      </div>
      <div class="list">
        <div v-for="user in sales" :key="user.id" class="row">
          <div>
            <strong>{{ user.display_name }}</strong>
            <p>{{ user.username }} · {{ user.approval_status }}</p>
          </div>
          <select :value="user.approval_status" @change="emit('updateSalesStatus', user.id, ($event.target as HTMLSelectElement).value)">
            <option value="approved">已通过</option>
            <option value="pending">待审核</option>
            <option value="rejected">已拒绝</option>
            <option value="disabled">已停用</option>
          </select>
        </div>
      </div>
    </article>

    <article class="panel">
      <div class="panel-head">
        <strong>资料审核</strong>
        <span>销售提交 / 企业资料</span>
      </div>
      <div class="list">
        <div v-for="item in materials" :key="item.id" class="row material-row">
          <div>
            <strong>{{ item.title }}</strong>
            <p>{{ item.scope === 'tenant' ? '企业资料' : '销售补充' }} · {{ item.approval_status }}</p>
          </div>
          <select :value="item.approval_status" @change="emit('updateMaterialStatus', item.id, ($event.target as HTMLSelectElement).value)">
            <option value="approved">生效</option>
            <option value="pending">待审核</option>
            <option value="rejected">拒绝</option>
            <option value="disabled">停用</option>
          </select>
        </div>
      </div>
    </article>
  </section>
</template>

<style scoped>
.tenant-page {
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
  background: linear-gradient(135deg, oklch(0.28 0.045 220), oklch(0.4 0.085 175));
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
  grid-template-columns: repeat(4, minmax(0, 1fr));
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

@media (max-width: 620px) {
  .metric-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { PullRefresh, showToast } from 'vant'
import AuthPanel from './components/AuthPanel.vue'
import CompanyMaterialPanel from './components/CompanyMaterialPanel.vue'
import CustomerHeader from './components/CustomerHeader.vue'
import CustomerLibrary from './components/CustomerLibrary.vue'
import FollowOverviewPanel from './components/FollowOverviewPanel.vue'
import FollowTab from './components/FollowTab.vue'
import GuidePanel from './components/GuidePanel.vue'
import GrowthPanel from './components/GrowthPanel.vue'
import PlatformAdminPanel from './components/PlatformAdminPanel.vue'
import ProfileTab from './components/ProfileTab.vue'
import RecommendationTab from './components/RecommendationTab.vue'
import SoftwareGuidePanel from './components/SoftwareGuidePanel.vue'
import SummaryDashboard from './components/SummaryDashboard.vue'
import TenantAdminPanel from './components/TenantAdminPanel.vue'
import { useSidebarStore } from './stores/sidebar'

const store = useSidebarStore()
const active = ref(0)
const refreshing = ref(false)
const navItems = ['作战', '客户', '画像', '跟进', '复盘', '内容', '我的']

const guideReady = computed(() => Boolean(store.user?.sales_guide))

async function runAction(action: () => Promise<void>, success?: string, busyMessage?: string) {
  if (busyMessage) store.busyMessage = busyMessage
  try {
    await action()
    if (success) showToast(success)
  } catch (error) {
    showToast(error instanceof Error ? error.message : '操作失败，请稍后重试')
  } finally {
    if (busyMessage && store.busyMessage === busyMessage) store.busyMessage = ''
  }
}

async function refresh() {
  refreshing.value = true
  await runAction(async () => {
    await store.loadAnalysis()
    await store.loadCustomers()
    await store.loadFollowOverview()
    await store.loadDailyIpAdvice()
    await store.loadSalesTechniqueGuide()
    await store.loadFeedback()
    await store.loadPersonaSources()
  }, undefined, 'AI 正在刷新客户分析、跟进建议和今日 IP 建议，请稍等...')
  refreshing.value = false
}

async function addFollow(content: string) {
  await runAction(() => store.addFollow(content), '已保存跟进', '正在保存跟进并刷新客户状态，请稍等...')
}

async function addFeedback(payload: {
  ai_reply: string
  customer_reply: string
  sales_review: string
  outcome: 'good' | 'bad' | 'neutral'
  original_customer_question?: string
}) {
  await runAction(() => store.addFeedback(payload), '复盘已保存', 'AI 正在复盘客户反馈，让销售助手更懂这类场景...')
}

async function addPersona(payload: { title: string; content: string; source_type: string; source_url?: string }) {
  await runAction(() => store.addPersonaSource(payload), '客户人设资料已保存', 'AI 正在更新客户长期判断，不会只凭单次资料下结论...')
}

async function addCompanyMaterial(payload: { title: string; content: string; source_type: string; scope?: string }) {
  await runAction(() => store.addCompanyMaterial({ ...payload, scope: 'tenant' }), '公司资料已保存', 'AI 正在更新企业知识库，稍后销售回复会参考最新资料...')
}

async function generateIp(theme: string, channel: 'moments' | 'douyin') {
  await runAction(
    () => store.generateIpContent(theme, channel),
    channel === 'douyin' ? '短视频文案已生成' : '朋友圈内容已生成',
    channel === 'douyin' ? 'AI 正在生成抖音短视频脚本，请稍等...' : 'AI 正在生成个人 IP 内容，请稍等...'
  )
}

async function importTranscript(transcript: string) {
  await runAction(() => store.importTranscript(transcript), '已导入并刷新分析', 'AI 正在分析聊天记录、生成客户判断和回复建议，请稍等...')
}

async function refreshAnalysis() {
  await runAction(() => store.refreshAnalysis(), '回复策略已刷新')
}

async function refreshDailyIp() {
  await runAction(() => store.refreshDailyIpAdvice(), '今日 IP 建议已刷新')
}

async function selectCustomer(externalUserId: string) {
  await runAction(async () => {
    await store.selectCustomer(externalUserId)
    active.value = 0
  }, undefined, 'AI 正在切换客户并读取最新客户全景，请稍等...')
}

async function createCustomer(nickname: string) {
  await runAction(async () => {
    await store.createCustomer(nickname)
    active.value = 0
  }, '客户已创建', '正在创建客户并初始化分析工作台...')
}

async function updateCustomerStatus(status: 'active' | 'closed') {
  await runAction(
    () => store.updateCustomerStatus(status),
    status === 'closed' ? '已标记成交' : '已恢复跟进',
    status === 'closed'
      ? '正在沉淀成交客户经验，后续话术会重点参考这类成功样本...'
      : '正在恢复客户跟进状态...'
  )
}

async function login(username: string, password: string) {
  await runAction(async () => {
    await store.login(username, password)
    await store.bootstrap()
  }, undefined, '正在进入工作台，请稍等...')
}

async function register(username: string, password: string, displayName: string, role: string, tenantName: string) {
  await runAction(async () => {
    await store.register(username, password, displayName, role, tenantName)
    await store.bootstrap()
  }, undefined, '正在创建账号并初始化工作台，请稍等...')
}

async function saveGuide(industry: string, customerGroup: string) {
  await runAction(async () => {
    await store.saveGuide(industry, customerGroup)
    await store.bootstrap()
  }, '销售指南已更新', 'AI 正在生成行业销售指南，这一步可能需要几十秒，请稍等...')
}

onMounted(() => {
  store.bootstrap()
})
</script>

<template>
  <main class="shell">
    <AuthPanel v-if="!store.user" @login="login" @register="register" />

    <template v-else>
      <header class="workspace-bar">
        <div>
          <span>Sales Copilot</span>
          <strong>销冠作战台</strong>
          <em>客户画像 · 话术策略 · 跟进复盘</em>
        </div>
        <button type="button" @click="store.logout()">退出</button>
      </header>

      <section v-if="store.user.role === 'sales' && !guideReady" class="onboarding">
        <div class="hello">
          <span>{{ store.user.display_name || store.user.username }}</span>
          <strong>先生成你的专属销售打法</strong>
          <p>填入行业和客户群体后，AI 会先建立行业销售指南，再开始分析聊天记录。</p>
        </div>
        <GuidePanel :sales-technique-guide="store.salesTechniqueGuide" :user="store.user" @save="saveGuide" />
      </section>

      <PlatformAdminPanel
        v-else-if="store.user.role === 'platform_admin'"
        :tenants="store.tenants"
        @create-tenant="(payload) => runAction(() => store.createTenant(payload), '企业已创建')"
        @create-tenant-admin="(payload) => runAction(() => store.createTenantAdmin(payload), '企业管理员已创建', '正在创建企业管理员账号...')"
        @update-tenant-status="(tenantId, status) => runAction(() => store.updateTenantStatus(tenantId, status), '企业状态已更新', '正在更新企业状态...')"
      />

      <TenantAdminPanel
        v-else-if="store.user.role === 'tenant_admin'"
        :materials="store.companyMaterials"
        :overview="store.tenantOverview"
        :sales="store.tenantSales"
        @add-material="addCompanyMaterial"
        @create-sales="(payload) => runAction(() => store.createTenantSales(payload), '销售账号已创建', '正在创建销售账号...')"
        @update-material-status="(materialId, status) => runAction(() => store.updateMaterialStatus(materialId, status), '资料状态已更新', '正在更新资料审核状态...')"
        @update-sales-status="(userId, status) => runAction(() => store.updateSalesStatus(userId, status), '销售状态已更新', '正在更新销售账号状态...')"
      />

      <template v-else>
        <CustomerHeader :customer="store.customer" :user="store.user" />

        <div v-if="store.error" class="error">{{ store.error }}</div>

        <PullRefresh v-model="refreshing" class="content" @refresh="refresh">
          <RecommendationTab
            v-if="active === 0"
            :analysis="store.analysis"
            :customer="store.customer"
            :customers="store.customers"
            @create-customer="createCustomer"
            @import="importTranscript"
            @refresh-analysis="refreshAnalysis"
            @select-customer="selectCustomer"
          />

          <CustomerLibrary v-else-if="active === 1" :groups="store.customersByCategory" @select="selectCustomer" />

          <ProfileTab
            v-else-if="active === 2"
            :analysis="store.analysis"
            :customer="store.customer"
            :feedback-records="store.feedbackRecords"
            :persona-sources="store.personaSources"
            @add-feedback="addFeedback"
            @add-persona="addPersona"
            @update-status="updateCustomerStatus"
          />

          <FollowTab v-else-if="active === 3" :records="store.followRecords" @add="addFollow" />

          <div v-else-if="active === 4" class="summary">
            <SummaryDashboard :customers="store.customers" :overview="store.followOverview" />
            <FollowOverviewPanel :overview="store.followOverview" />
          </div>

          <GrowthPanel
            v-else-if="active === 5"
            :daily-ip-advice="store.dailyIpAdvice"
            :ip-contents="store.ipContents"
            @generate-ip="generateIp"
            @refresh-daily-ip="refreshDailyIp"
          />

          <div v-else class="mine">
            <CompanyMaterialPanel :materials="store.companyMaterials" @add="addCompanyMaterial" />
            <GuidePanel :sales-technique-guide="store.salesTechniqueGuide" :user="store.user" @save="saveGuide" />
            <SoftwareGuidePanel :content="store.softwareGuide" />
          </div>
        </PullRefresh>

        <nav class="bottom-nav" aria-label="主导航">
          <button
            v-for="(item, index) in navItems"
            :key="item"
            :class="{ active: active === index }"
            type="button"
            @click="active = index"
          >
            {{ item }}
          </button>
        </nav>
      </template>
    </template>

    <div v-if="store.busyMessage" class="ai-busy" role="status" aria-live="polite">
      <div class="busy-card">
        <span class="spinner"></span>
        <strong>正在处理</strong>
        <p>{{ store.busyMessage }}</p>
      </div>
    </div>
  </main>
</template>

<style scoped>
.shell {
  position: relative;
  overflow: hidden;
  min-height: 100vh;
  width: min(100vw, 980px);
  margin: 0 auto;
  background:
    linear-gradient(180deg, oklch(1 0.004 95 / 0.82), oklch(0.97 0.014 112 / 0.92)),
    var(--bg);
  box-shadow:
    0 0 0 1px oklch(0.86 0.026 105 / 0.72),
    0 24px 80px oklch(0.2 0.045 224 / 0.12);
}

.shell::before {
  content: "";
  position: fixed;
  inset: 0 max(0px, calc((100vw - 980px) / 2)) auto;
  height: 230px;
  pointer-events: none;
  background:
    radial-gradient(circle at 18% 0%, oklch(0.82 0.08 174 / 0.32), transparent 210px),
    radial-gradient(circle at 86% 10%, oklch(0.9 0.085 82 / 0.4), transparent 190px);
  z-index: 0;
}

.shell > * {
  position: relative;
  z-index: 1;
}

.workspace-bar {
  position: sticky;
  top: 0;
  z-index: 15;
  display: flex;
  align-items: center;
  justify-content: space-between;
  min-height: 78px;
  padding: 14px 16px 12px;
  color: var(--ink);
  background:
    linear-gradient(135deg, oklch(1 0.004 95 / 0.9), oklch(0.94 0.047 171 / 0.82)),
    oklch(1 0 0 / 0.82);
  border-bottom: 1px solid oklch(0.87 0.026 105 / 0.75);
  box-shadow: 0 14px 34px oklch(0.18 0.04 224 / 0.07);
  backdrop-filter: blur(18px);
}

.workspace-bar div {
  display: grid;
  gap: 3px;
}

.workspace-bar span {
  width: fit-content;
  padding: 4px 8px;
  border: 1px solid oklch(0.79 0.056 175 / 0.65);
  border-radius: 999px;
  color: var(--brand-strong);
  background: oklch(1 0 0 / 0.52);
  font-size: 10px;
  font-weight: 950;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.workspace-bar strong {
  font-size: 20px;
  letter-spacing: -0.03em;
}

.workspace-bar em {
  color: var(--muted);
  font-size: 12px;
  font-style: normal;
  font-weight: 700;
}

.workspace-bar button {
  height: 34px;
  border: 1px solid oklch(0.78 0.052 175 / 0.62);
  border-radius: 999px;
  padding: 0 13px;
  color: var(--brand-strong);
  background: oklch(1 0 0 / 0.58);
  font-size: 12px;
  font-weight: 900;
  box-shadow: var(--shadow-tiny);
}

.onboarding {
  display: grid;
  gap: 14px;
  padding: 14px;
}

.hello {
  position: relative;
  overflow: hidden;
  padding: 20px;
  border: 1px solid oklch(1 0 0 / 0.34);
  border-radius: var(--radius-lg);
  color: white;
  background:
    radial-gradient(circle at 88% 12%, oklch(0.78 0.13 82 / 0.5), transparent 190px),
    linear-gradient(135deg, oklch(0.25 0.06 226), oklch(0.39 0.1 178));
  box-shadow: var(--shadow);
}

.hello::after {
  content: "";
  position: absolute;
  right: -34px;
  bottom: -52px;
  width: 160px;
  height: 160px;
  border: 1px solid oklch(1 0 0 / 0.22);
  border-radius: 50%;
}

.hello span {
  display: block;
  margin-bottom: 6px;
  color: oklch(0.83 0.055 178);
  font-size: 12px;
  font-weight: 800;
}

.hello strong {
  display: block;
  font-size: 20px;
  line-height: 1.25;
}

.hello p {
  margin: 8px 0 0;
  color: oklch(0.94 0.018 190);
  font-size: 13px;
  line-height: 1.55;
}

.content {
  min-height: calc(100vh - 128px);
  padding-bottom: 92px;
}

.mine,
.summary {
  display: grid;
  gap: 14px;
  padding: 14px;
}

.summary :deep(.summary-dashboard) {
  padding: 0;
}

.mine :deep(.guide-panel) {
  padding: 0;
}

.error {
  margin: 10px 12px;
  padding: 11px 13px;
  border: 1px solid oklch(0.86 0.09 25);
  border-radius: var(--radius-sm);
  color: oklch(0.4 0.14 25);
  background: oklch(0.97 0.035 25);
  font-size: 13px;
}

.bottom-nav {
  position: fixed;
  right: max(12px, calc((100vw - 956px) / 2));
  bottom: 12px;
  left: max(12px, calc((100vw - 956px) / 2));
  z-index: 20;
  display: grid;
  grid-template-columns: repeat(7, minmax(0, 1fr));
  gap: 5px;
  min-height: 62px;
  padding: 8px;
  padding-bottom: calc(8px + env(safe-area-inset-bottom));
  border: 1px solid oklch(0.88 0.021 105 / 0.82);
  border-radius: 24px;
  background: oklch(1 0.004 95 / 0.82);
  box-shadow: 0 18px 46px oklch(0.18 0.04 224 / 0.16);
  backdrop-filter: blur(18px);
}

.bottom-nav button {
  position: relative;
  min-width: 0;
  height: 44px;
  border: 0;
  border-radius: 17px;
  color: var(--muted);
  background: transparent;
  font-size: 12px;
  font-weight: 900;
  transition: color 0.18s ease, background 0.18s ease, transform 0.18s ease, box-shadow 0.18s ease;
}

.bottom-nav .active {
  color: white;
  background:
    radial-gradient(circle at 80% 0%, oklch(0.78 0.13 82 / 0.55), transparent 42px),
    linear-gradient(135deg, var(--brand-strong), var(--brand));
  box-shadow: 0 10px 20px oklch(0.34 0.095 184 / 0.22);
  transform: translateY(-1px);
}

.ai-busy {
  position: fixed;
  inset: 0;
  z-index: 40;
  display: grid;
  place-items: center;
  padding: 22px;
  background: oklch(0.18 0.04 224 / 0.34);
  backdrop-filter: blur(5px);
}

.busy-card {
  display: grid;
  justify-items: center;
  gap: 9px;
  width: min(320px, calc(100vw - 44px));
  padding: 20px 18px;
  border: 1px solid oklch(1 0 0 / 0.48);
  border-radius: var(--radius-lg);
  background:
    linear-gradient(180deg, oklch(1 0.004 95), oklch(0.966 0.018 105)),
    var(--surface);
  box-shadow: var(--shadow);
  text-align: center;
}

.spinner {
  width: 34px;
  height: 34px;
  border: 3px solid oklch(0.9 0.05 171);
  border-top-color: var(--brand);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

.busy-card strong {
  color: var(--ink);
  font-size: 15px;
}

.busy-card p {
  margin: 0;
  color: var(--muted);
  font-size: 13px;
  line-height: 1.55;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

@media (min-width: 760px) {
  .shell {
    min-height: 100vh;
  }

  .content {
    min-height: calc(100vh - 66px);
  }
}

@media (max-width: 420px) {
  .bottom-nav {
    gap: 2px;
    right: 8px;
    left: 8px;
    bottom: 8px;
    padding-inline: 6px;
    border-radius: 20px;
  }

  .bottom-nav button {
    height: 40px;
    font-size: 11px;
  }
}
</style>

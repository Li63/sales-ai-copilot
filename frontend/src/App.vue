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
const activeTitle = computed(() => {
  const titles = ['看板', '客户库', '客户画像', '跟进任务', '复盘中心', '内容增长', '系统设置']
  return titles[active.value] || '看板'
})
const activeCrumb = computed(() => `本地部署 / AI 自动化 / ${activeTitle.value}`)
const assistantConclusion = computed(() => {
  return store.analysis?.next_action || store.customer?.core_demand || '先补齐客户资料，再生成下一步建议。'
})
const assistantReasons = computed(() => {
  return [
    store.customer?.core_demand || store.analysis?.core_demand,
    store.customer?.objection || store.analysis?.objection,
    store.customer?.persona_profile ? '已结合客户画像和历史资料。' : '客户画像资料仍需继续补充。'
  ].filter(Boolean).slice(0, 3)
})
const assistantEvidence = computed(() => {
  const source = store.personaSources[0]
  if (source?.title) return `${source.title}${source.source_url ? ` / ${source.source_url}` : ''}`
  const tag = store.customer?.tags?.[0]
  if (tag) return `${tag.tag_name} / confidence ${tag.confidence}`
  return '等待抖音、企查查、官网或聊天截图补充证据。'
})
const assistantNextStep = computed(() => store.analysis?.reply_suggestions?.[0] || '创建跟进任务，并观察客户是否回复。')
const headerMetricCards = computed(() => [
  {
    label: '客户意向',
    value: `${store.customer?.intention_score ?? 0}`,
    desc: `${store.customer?.category || store.customer?.intention_level || 'C'} 类客户`,
    tone: 'green'
  },
  {
    label: '资料吸收',
    value: `${store.personaSources.length}`,
    desc: '抖音/企查查/截图',
    tone: 'blue'
  },
  {
    label: '跟进记录',
    value: `${store.followRecords.length}`,
    desc: '历史动作',
    tone: 'amber'
  },
  {
    label: '复盘样本',
    value: `${store.feedbackRecords.length}`,
    desc: '话术反馈',
    tone: 'slate'
  }
])

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

      <section v-else class="sales-workspace">
        <nav class="bottom-nav" aria-label="主导航">
          <div class="desktop-brand">
            <i>AI</i>
            <div>
              <strong>销冠作战台</strong>
              <span>Sales AI OS</span>
            </div>
          </div>
          <button
            v-for="(item, index) in navItems"
            :key="item"
            :class="{ active: active === index }"
            type="button"
            @click="active = index"
          >
            <b>{{ item.slice(0, 1) }}</b>
            <span>{{ item }}</span>
          </button>
          <div class="desktop-service">
            <b></b>
            <span>本地服务在线</span>
          </div>
        </nav>

        <div class="workspace-main">
          <header class="desktop-topbar">
            <label class="global-search">
              <span>⌕</span>
              <input placeholder="搜索客户、产品、报价、任务" />
            </label>
            <div class="topbar-actions">
              <span class="status-chip success">AI 已连接</span>
              <span class="status-chip info">搜索供应商 2/3</span>
              <span class="status-chip success">API 已连接</span>
              <button class="icon-button" type="button" aria-label="通知">!</button>
              <button class="create-button" type="button">+ 创建</button>
            </div>
          </header>

          <div class="desktop-layout">
            <section class="desktop-content">
              <div class="desktop-page-head">
                <div>
                  <span>{{ activeCrumb }}</span>
                  <strong>{{ activeTitle }}</strong>
                </div>
                <button type="button" @click="refreshAnalysis">AI 生成建议</button>
              </div>

              <div class="metric-strip" aria-label="关键指标">
                <article v-for="card in headerMetricCards" :key="card.label" :class="`metric-card ${card.tone}`">
                  <span>{{ card.label }}</span>
                  <strong>{{ card.value }}</strong>
                  <em>{{ card.desc }}</em>
                </article>
              </div>

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
            </section>

            <aside class="assistant-panel" aria-label="AI 上下文助手">
              <div class="assistant-title">
                <b>AI</b>
                <div>
                  <strong>AI 上下文助手</strong>
                  <span>帮你判断下一步建议</span>
                </div>
              </div>
              <section>
                <span>结论</span>
                <p>{{ assistantConclusion }}</p>
              </section>
              <section>
                <span>理由</span>
                <ul>
                  <li v-for="reason in assistantReasons" :key="reason">{{ reason }}</li>
                </ul>
              </section>
              <section>
                <span>证据</span>
                <p>{{ assistantEvidence }}</p>
              </section>
              <section>
                <span>下一步</span>
                <button type="button" @click="active = 3">{{ assistantNextStep }}</button>
              </section>
            </aside>
          </div>
        </div>
      </section>
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
  overflow-x: hidden;
  min-height: 100vh;
  width: min(100vw, var(--shell-max));
  margin: 0 auto;
  background:
    linear-gradient(180deg, oklch(1 0.004 95 / 0.64), oklch(0.96 0.018 178 / 0.72)),
    oklch(1 0.004 95 / 0.42);
  box-shadow:
    0 0 0 1px oklch(1 0 0 / 0.56),
    0 36px 110px oklch(0.16 0.046 235 / 0.13);
  isolation: isolate;
}

.shell::before {
  content: "";
  position: fixed;
  inset: 0 max(0px, calc((100vw - var(--shell-max)) / 2)) auto;
  height: 340px;
  pointer-events: none;
  background:
    radial-gradient(circle at 18% 0%, oklch(0.82 0.08 174 / 0.34), transparent 260px),
    radial-gradient(circle at 86% 6%, oklch(0.9 0.085 82 / 0.34), transparent 250px),
    linear-gradient(180deg, oklch(1 0.004 95 / 0.44), transparent);
  z-index: 0;
}

.shell > * {
  position: relative;
  z-index: 1;
}

.workspace-bar {
  position: sticky;
  top: 0;
  z-index: 25;
  display: flex;
  align-items: center;
  justify-content: space-between;
  min-height: 82px;
  padding: 14px clamp(16px, 3vw, 34px) 12px;
  color: var(--ink);
  background:
    linear-gradient(135deg, oklch(1 0.004 95 / 0.86), oklch(0.94 0.047 171 / 0.76)),
    oklch(1 0 0 / 0.72);
  border-bottom: 1px solid oklch(1 0 0 / 0.56);
  box-shadow: 0 18px 44px oklch(0.16 0.046 235 / 0.08);
  backdrop-filter: blur(24px);
}

.workspace-bar div {
  display: grid;
  gap: 3px;
}

.workspace-bar span {
  width: fit-content;
  padding: 5px 10px;
  border: 1px solid oklch(0.79 0.056 175 / 0.65);
  border-radius: 999px;
  color: var(--brand-strong);
  background: oklch(1 0 0 / 0.64);
  font-size: 10px;
  font-weight: 950;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.workspace-bar strong {
  font-size: clamp(20px, 2.2vw, 30px);
  letter-spacing: -0.05em;
}

.workspace-bar em {
  color: var(--muted);
  font-size: 12px;
  font-style: normal;
  font-weight: 700;
}

.workspace-bar button {
  height: 38px;
  border: 1px solid oklch(0.78 0.052 175 / 0.62);
  border-radius: 999px;
  padding: 0 13px;
  color: var(--brand-strong);
  background: oklch(1 0 0 / 0.58);
  font-size: 12px;
  font-weight: 900;
  box-shadow: var(--shadow-tiny);
}

.sales-workspace {
  position: relative;
}

.workspace-main {
  min-width: 0;
}

.desktop-brand,
.desktop-service,
.desktop-topbar,
.desktop-page-head,
.metric-strip,
.assistant-panel {
  display: none;
}

.desktop-layout,
.desktop-content {
  min-width: 0;
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
  min-height: calc(100vh - 150px);
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
  right: max(12px, calc((100vw - min(100vw, var(--shell-max)) + 24px) / 2));
  bottom: 12px;
  left: max(12px, calc((100vw - min(100vw, var(--shell-max)) + 24px) / 2));
  z-index: 20;
  display: grid;
  grid-template-columns: repeat(7, minmax(0, 1fr));
  gap: 5px;
  min-height: 62px;
  padding: 8px;
  padding-bottom: calc(8px + env(safe-area-inset-bottom));
  border: 1px solid oklch(1 0 0 / 0.68);
  border-radius: 24px;
  background: oklch(1 0.004 95 / 0.78);
  box-shadow: 0 20px 56px oklch(0.16 0.046 235 / 0.18);
  backdrop-filter: blur(22px);
}

.bottom-nav button {
  position: relative;
  display: grid;
  place-items: center;
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

  .bottom-nav button::before {
    content: "";
  width: 7px;
  height: 7px;
  margin-bottom: 3px;
  border-radius: 999px;
  background: currentColor;
  opacity: 0.32;
}

.bottom-nav .active {
  color: white;
  background:
    radial-gradient(circle at 80% 0%, oklch(0.78 0.13 82 / 0.55), transparent 42px),
    linear-gradient(135deg, var(--brand-strong), var(--brand));
  box-shadow: 0 10px 20px oklch(0.34 0.095 184 / 0.22);
  transform: translateY(-1px);
}

  .bottom-nav .active::before {
    opacity: 0.9;
  }

  .bottom-nav button b {
    display: none;
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

@media (min-width: 1180px) {
  .shell {
    width: 100vw;
    max-width: none;
    min-height: 100vh;
    margin: 0;
    background: #f5f7fb;
    border-inline: 0;
    box-shadow: none;
  }

  .shell::before {
    content: none;
  }

  .workspace-bar {
    display: none;
  }

  .sales-workspace {
    display: grid;
    grid-template-columns: 212px minmax(0, 1fr);
    gap: 0;
    min-height: 100vh;
    padding: 0;
    background: #f5f7fb;
  }

  .workspace-main {
    width: 100%;
    margin: 0;
    overflow: hidden;
  }

  .desktop-topbar {
    position: sticky;
    top: 0;
    z-index: 24;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 18px;
    height: 64px;
    padding: 0 16px;
    background: #ffffff;
    border-bottom: 1px solid #dbe2ea;
  }

  .global-search {
    display: grid;
    grid-template-columns: 20px minmax(0, 1fr);
    align-items: center;
    gap: 8px;
    width: min(420px, 42vw);
    height: 36px;
    padding: 0 12px;
    border: 1px solid #d7dee8;
    border-radius: 8px;
    background: #ffffff;
    color: #64748b;
  }

  .global-search span {
    font-size: 18px;
    line-height: 1;
  }

  .global-search input {
    height: 100%;
    border: 0;
    padding: 0;
    color: #0f172a;
    background: transparent;
    box-shadow: none;
    font-size: 13px;
  }

  .global-search input:focus {
    box-shadow: none;
  }

  .topbar-actions {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .status-chip {
    display: inline-flex;
    align-items: center;
    min-height: 24px;
    padding: 0 9px;
    border-radius: 999px;
    font-size: 11px;
    font-weight: 900;
    white-space: nowrap;
  }

  .status-chip.success {
    color: #047857;
    background: #dcfce7;
  }

  .status-chip.info {
    color: #1d4ed8;
    background: #dbeafe;
  }

  .icon-button,
  .create-button {
    height: 34px;
    border: 1px solid #d8e0ea;
    border-radius: 8px;
    background: #ffffff;
    color: #0f172a;
    font-weight: 900;
  }

  .icon-button {
    width: 34px;
  }

  .create-button {
    padding: 0 14px;
    color: #ffffff;
    border-color: #2456d9;
    background: #2456d9;
    box-shadow: 0 8px 18px rgb(37 86 217 / 18%);
  }

  .desktop-layout {
    display: grid;
    grid-template-columns: minmax(0, 1fr) 320px;
    min-height: calc(100vh - 64px);
  }

  .desktop-content {
    display: block;
    min-height: calc(100vh - 64px);
    padding: 16px;
    background: #f5f7fb;
  }

  .desktop-page-head {
    display: flex;
    align-items: flex-end;
    justify-content: space-between;
    gap: 16px;
    margin-bottom: 12px;
  }

  .desktop-page-head div {
    display: grid;
    gap: 3px;
  }

  .desktop-page-head span {
    color: #53657d;
    font-size: 12px;
    font-weight: 850;
  }

  .desktop-page-head strong {
    color: #0f172a;
    font-size: 22px;
    letter-spacing: -0.04em;
  }

  .desktop-page-head button {
    height: 36px;
    border: 1px solid #d8e0ea;
    border-radius: 8px;
    padding: 0 14px;
    color: #0f172a;
    background: #ffffff;
    font-size: 13px;
    font-weight: 900;
    box-shadow: 0 1px 2px rgb(15 23 42 / 6%);
  }

  .metric-strip {
    display: grid;
    grid-template-columns: repeat(4, minmax(0, 1fr));
    gap: 12px;
    margin-bottom: 12px;
  }

  .metric-card {
    min-height: 88px;
    padding: 14px 15px;
    border: 1px solid #d9e1eb;
    border-left-width: 4px;
    border-radius: 7px;
    background: #ffffff;
    box-shadow: 0 1px 2px rgb(15 23 42 / 5%);
  }

  .metric-card.green { border-left-color: #16a34a; }
  .metric-card.blue { border-left-color: #2563eb; }
  .metric-card.amber { border-left-color: #d97706; }
  .metric-card.slate { border-left-color: #64748b; }

  .metric-card span {
    display: block;
    color: #64748b;
    font-size: 13px;
    font-weight: 800;
  }

  .metric-card strong {
    display: block;
    margin-top: 4px;
    color: #0f172a;
    font-size: 26px;
    line-height: 1;
    letter-spacing: -0.04em;
  }

  .metric-card em {
    display: block;
    margin-top: 5px;
    color: #64748b;
    font-size: 12px;
    font-style: normal;
    font-weight: 750;
  }

  .content {
    min-height: auto;
    padding-bottom: 0;
  }

  .mine,
  .summary {
    grid-template-columns: repeat(2, minmax(0, 1fr));
    padding: 12px 0 0;
  }

  .workspace-main :deep(.library),
  .workspace-main :deep(.follow),
  .workspace-main :deep(.ip-builder) {
    grid-template-columns: repeat(12, minmax(0, 1fr));
    gap: var(--page-gap);
    padding: var(--page-gap);
  }

  .workspace-main :deep(.library-head),
  .workspace-main :deep(.search-box),
  .workspace-main :deep(.hero),
  .workspace-main :deep(.daily) {
    grid-column: 1 / -1;
  }

  .workspace-main :deep(.level-section) {
    grid-column: span 6;
    border-radius: var(--radius-lg);
  }

  .workspace-main :deep(.follow .composer) {
    grid-column: span 5;
    position: sticky;
    top: 108px;
  }

  .workspace-main :deep(.follow .timeline) {
    grid-column: span 7;
  }

  .workspace-main :deep(.ip-builder > .panel:not(.daily)) {
    grid-column: span 4;
  }

  .workspace-main :deep(.ip-list) {
    grid-column: span 8;
  }

  .bottom-nav {
    position: sticky;
    top: 0;
    left: auto;
    right: auto;
    bottom: auto;
    align-self: start;
    display: flex;
    flex-direction: column;
    grid-template-columns: 1fr;
    gap: 6px;
    width: 212px;
    height: 100vh;
    min-height: 100vh;
    margin: 0;
    padding: 16px 10px 14px;
    border: 0;
    border-radius: 0;
    background: #0f172a;
    box-shadow: none;
    backdrop-filter: none;
  }

  .bottom-nav::before {
    content: none;
  }

  .desktop-brand {
    display: flex;
    align-items: center;
    gap: 10px;
    min-height: 50px;
    padding: 2px 6px 14px;
    margin-bottom: 4px;
    border-bottom: 1px solid rgb(148 163 184 / 18%);
    color: #ffffff;
  }

  .desktop-brand i {
    display: grid;
    place-items: center;
    width: 32px;
    height: 32px;
    border-radius: 9px;
    background: #2456d9;
    font-size: 12px;
    font-style: normal;
    font-weight: 950;
  }

  .desktop-brand div {
    display: grid;
    gap: 2px;
    min-width: 0;
  }

  .desktop-brand strong {
    overflow: hidden;
    font-size: 15px;
    letter-spacing: -0.03em;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .desktop-brand span {
    color: #94a3b8;
    font-size: 11px;
    font-weight: 800;
  }

  .bottom-nav button {
    display: flex;
    align-items: center;
    justify-content: flex-start;
    gap: 10px;
    width: 100%;
    height: 36px;
    padding: 0 11px;
    border-radius: 6px;
    color: #cbd5e1;
    font-size: 14px;
    font-weight: 850;
  }

  .bottom-nav button::before {
    content: none;
  }

  .bottom-nav button b {
    display: grid;
    place-items: center;
    width: 18px;
    height: 18px;
    border-radius: 6px;
    color: #94a3b8;
    background: rgb(148 163 184 / 12%);
    font-size: 11px;
    font-weight: 950;
    line-height: 1;
  }

  .bottom-nav .active b {
    color: #2456d9;
    background: #ffffff;
  }

  .bottom-nav .active {
    color: #ffffff;
    background: #2456d9;
    box-shadow: none;
    transform: none;
  }

  .desktop-service {
    display: flex;
    align-items: center;
    gap: 8px;
    min-height: 32px;
    margin-top: auto;
    padding: 0 10px;
    border: 1px solid rgb(148 163 184 / 20%);
    border-radius: 7px;
    color: #cbd5e1;
    font-size: 12px;
    font-weight: 850;
  }

  .desktop-service b {
    width: 7px;
    height: 7px;
    border-radius: 50%;
    background: #22c55e;
    box-shadow: 0 0 0 3px rgb(34 197 94 / 14%);
  }

  .assistant-panel {
    position: sticky;
    top: 64px;
    display: grid;
    align-content: start;
    gap: 0;
    height: calc(100vh - 64px);
    overflow: auto;
    background: #ffffff;
    border-left: 1px solid #dbe2ea;
    box-shadow: -1px 0 0 rgb(15 23 42 / 2%);
  }

  .assistant-title {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 15px 14px;
    border-bottom: 1px solid #dbe2ea;
    background: #f8fbff;
  }

  .assistant-title b {
    display: grid;
    place-items: center;
    width: 30px;
    height: 30px;
    border-radius: 8px;
    color: #2456d9;
    background: #dbeafe;
    font-size: 12px;
  }

  .assistant-title div {
    display: grid;
    gap: 2px;
  }

  .assistant-title strong {
    color: #0f172a;
    font-size: 16px;
    letter-spacing: -0.03em;
  }

  .assistant-title span,
  .assistant-panel section > span {
    color: #475569;
    font-size: 12px;
    font-weight: 900;
  }

  .assistant-panel section {
    display: grid;
    gap: 9px;
    padding: 16px 14px;
    border-bottom: 1px solid #e4e9f0;
  }

  .assistant-panel p {
    margin: 0;
    color: #334155;
    font-size: 14px;
    line-height: 1.7;
  }

  .assistant-panel ul {
    display: grid;
    gap: 7px;
    margin: 0;
    padding-left: 18px;
    color: #334155;
    font-size: 13px;
    line-height: 1.55;
  }

  .assistant-panel button {
    min-height: 36px;
    border: 0;
    border-radius: 7px;
    padding: 9px 12px;
    color: #ffffff;
    background: #2456d9;
    font-size: 13px;
    font-weight: 900;
    line-height: 1.45;
    text-align: left;
  }
}

@media (max-width: 420px) {
  .workspace-bar {
    min-height: 72px;
  }

  .workspace-bar em {
    display: none;
  }

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

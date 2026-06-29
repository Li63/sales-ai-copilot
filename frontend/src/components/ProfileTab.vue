<script setup lang="ts">
import { computed, ref } from 'vue'
import { showToast } from 'vant'
import type { Analysis, Customer, FeedbackRecord, PersonaSource } from '../stores/sidebar'
import { useSidebarStore } from '../stores/sidebar'
import { copyPlainText } from '../utils/clipboard'
import MarkdownView from './MarkdownView.vue'

const props = defineProps<{
  customer: Customer | null
  analysis: Analysis | null
  feedbackRecords: FeedbackRecord[]
  personaSources: PersonaSource[]
}>()

const emit = defineEmits<{
  addFeedback: [payload: { ai_reply: string; customer_reply: string; sales_review: string; outcome: 'good' | 'bad' | 'neutral'; original_customer_question?: string }]
  addPersona: [payload: { title: string; content: string; source_type: string; source_url?: string }]
  updateStatus: [status: 'active' | 'closed']
}>()

const store = useSidebarStore()
const selectedReply = ref('')
const customerReply = ref('')
const salesReview = ref('')
const outcome = ref<'good' | 'bad' | 'neutral'>('good')
const personaTitle = ref('')
const personaContent = ref('')
const personaSourceType = ref<'douyin_profile' | 'douyin_content' | 'qichacha' | 'website' | 'manual'>('douyin_profile')
const personaSourceUrl = ref('')
const recognizingPersona = ref(false)
const showSourceRecords = ref(false)

const sourceTypes = [
  {
    value: 'douyin_profile',
    label: '抖音主页',
    short: '主页',
    guide: '账号定位、简介、置顶作品、主页截图',
    placeholder: '粘贴抖音主页链接、简介、账号定位、置顶作品、评论里反复出现的问题。也可以直接上传主页截图，系统会看截图里的账号结构、内容风格和互动线索。',
  },
  {
    value: 'douyin_content',
    label: '抖音内容',
    short: '内容',
    guide: '爆款标题、口播、评论、互动线索',
    placeholder: '粘贴抖音作品标题、口播摘要、评论高频问题、互动情况。重点写客户在内容里想证明什么，以及粉丝在问什么。',
  },
  {
    value: 'qichacha',
    label: '企查查',
    short: '企查',
    guide: '经营范围、风险、招聘、股权、阶段',
    placeholder: '粘贴企查查/天眼查资料摘要：经营范围、成立时间、招聘、风险、融资、股权、公开动态。不要粘贴无关长表格。',
  },
  {
    value: 'website',
    label: '官网资料',
    short: '官网',
    guide: '产品页、案例、媒体报道、服务对象',
    placeholder: '粘贴官网、产品页、案例、媒体报道或公开页面摘要。重点写业务方向、服务对象、案例和近期变化。',
  },
  {
    value: 'manual',
    label: '销售观察',
    short: '观察',
    guide: '朋友圈、线下沟通、共同好友反馈',
    placeholder: '粘贴销售自己的观察：客户朋友圈、线下沟通、共同好友反馈、客户提过但聊天记录里没有沉淀的细节。',
  },
] as const

const replyOptions = computed(() => props.analysis?.reply_suggestions || [])
const score = computed(() => props.customer?.intention_score ?? 50)
const scoreStyle = computed(() => `--score: ${Math.max(0, Math.min(100, score.value))}%`)
const selectedSource = computed(() => sourceTypes.find((item) => item.value === personaSourceType.value) || sourceTypes[0])
const completedSourceTypes = computed(() => new Set(props.personaSources.map((source) => source.source_type)))
const sourceTypeLabel = (type: string) => sourceTypes.find((item) => item.value === type)?.label || '客户资料'
const personaText = computed(() => [props.customer?.persona_profile || '', props.personaSources[0]?.persona_summary || ''].filter(Boolean).join('\n'))

const workflowSteps = computed(() => [
  {
    title: '选资料源',
    desc: '抖音、企查查、官网、观察都能补画像',
    done: Boolean(personaSourceType.value),
  },
  {
    title: '放链接和文件',
    desc: '粘贴主页/企查查链接，上传截图或文档',
    done: Boolean(personaSourceUrl.value || personaContent.value || props.personaSources.length),
  },
  {
    title: 'AI 拆解',
    desc: '提取成交机会、痛点、沟通风格',
    done: props.personaSources.length > 0,
  },
  {
    title: '生成作战卡',
    desc: '销售直接拿去破冰和跟进',
    done: Boolean(props.customer?.persona_profile),
  },
])

const sourceProgress = computed(() => {
  const done = sourceTypes.filter((item) => completedSourceTypes.value.has(item.value)).length
  return `${done}/${sourceTypes.length}`
})

const battleCards = computed(() => [
  {
    label: '企业定位',
    title: pickInsight(['企业定位', '核心判断'], props.customer?.core_demand || props.analysis?.core_demand || '等待资料判断这家公司做什么、卖给谁、处于什么业务场景'),
    hint: '先判断业务方向和服务对象，不扩大解读。',
  },
  {
    label: '实力证据',
    title: pickInsight(['实力证据', '经营线索'], '等待企查查、官网、工厂/案例截图补充企业实力证据'),
    hint: '区分真实证据和销售假设，避免过度判断。',
  },
  {
    label: '账号/人设',
    title: pickInsight(['内容定位', '沟通方式'], '等待抖音、朋友圈或公开内容判断表达风格'),
    hint: '抖音偏账号定位，朋友圈偏真实性格。',
  },
  {
    label: '采购动机',
    title: pickInsight(['采购动机', '决策逻辑'], props.analysis?.core_demand || '等待聊天记录或公开动作验证真实动机'),
    hint: '判断客户为什么可能需要我们，而不是只看表面资料。',
  },
  {
    label: '成交机会',
    title: pickInsight(['成交机会', '跟进角度', '决策逻辑', '核心判断'], props.analysis?.next_action || props.customer?.core_demand || '等待更多资料判断成交窗口'),
    hint: '从客户公开动作里找到可切入的合作窗口。',
  },
  {
    label: '客户痛点',
    title: pickInsight(['客户痛点', '风险提醒', '当前异议', '异议', '经营线索'], props.customer?.objection || props.analysis?.objection || '暂未发现明确痛点，先用低压问题验证现状'),
    hint: '先验证，不急着教育客户。',
  },
  {
    label: '跟进策略',
    title: pickInsight(['跟进策略', '销售提醒', '沟通方式', '下一步动作'], props.analysis?.next_action || '先用资料线索破冰，再确认客户当前优先级'),
    hint: '把跟进节奏从“催”变成“帮客户判断”。',
  },
  {
    label: '破冰话术',
    title: pickInsight(['破冰话术'], replyOptions.value[1] || '我看您最近在关注这个方向，我不确定现在是不是重点，想先和您确认一个小问题。'),
    hint: '低压开场，客户更容易接话。',
    copyable: true,
  },
])

function pickInsight(labels: string[], fallback: string) {
  const lines = personaText.value.split(/\n+/).map((line) => line.trim()).filter(Boolean)
  for (const label of labels) {
    const marker = `${label}：`
    const matched = lines.find((line) => line.includes(marker))
    if (matched) {
      return matched.slice(matched.indexOf(marker) + marker.length).replace(/^[-\s]+/, '').trim()
    }
  }
  return fallback || '等待 AI 结合更多资料继续拆解'
}

function extractFirstUrl(text: string) {
  return text.match(/https?:\/\/[^\s，。；;）)]+/)?.[0]?.replace(/[，。；;、,.!?！？）)]$/, '') || ''
}

function inferSourceType(text: string, url: string): typeof personaSourceType.value {
  const haystack = `${url}\n${text}`.toLowerCase()
  if (haystack.includes('douyin.com') || text.includes('复制打开抖音') || text.includes('抖音')) {
    if (text.includes('主页') && !text.includes('作品') && !text.includes('#')) return 'douyin_profile'
    return 'douyin_content'
  }
  if (haystack.includes('qcc.com') || text.includes('企查查') || text.includes('天眼查')) return 'qichacha'
  if (url) return 'website'
  return 'manual'
}

function syncSourceTypeFromInput() {
  const combined = `${personaTitle.value}\n${personaSourceUrl.value}\n${personaContent.value}`
  const url = personaSourceUrl.value.trim() || extractFirstUrl(combined)
  personaSourceType.value = inferSourceType(combined, url)
  if (!personaSourceUrl.value.trim() && url) {
    personaSourceUrl.value = url
  }
}

async function copyCard(text: string) {
  const copied = await copyPlainText(text)
  showToast(copied ? '已复制作战话术' : '复制失败，请长按文字复制')
}

function submitFeedback() {
  const reply = selectedReply.value || replyOptions.value[0] || ''
  if (!reply.trim() || (!customerReply.value.trim() && !salesReview.value.trim())) {
    showToast('请选择话术，并填写客户回复或销售看法')
    return
  }
  emit('addFeedback', {
    ai_reply: reply,
    customer_reply: customerReply.value.trim(),
    sales_review: salesReview.value.trim(),
    outcome: outcome.value,
  })
  customerReply.value = ''
  salesReview.value = ''
}

function submitPersona() {
  syncSourceTypeFromInput()
  if (!personaContent.value.trim() && !personaSourceUrl.value.trim()) {
    showToast('请粘贴客户资料、抖音分享文案、企查查摘要，或上传 Word/PDF/图片')
    return
  }
  emit('addPersona', {
    title: personaTitle.value.trim() || selectedSource.value.label,
    source_type: personaSourceType.value,
    source_url: personaSourceUrl.value.trim(),
    content: personaContent.value.trim(),
  })
  personaTitle.value = ''
  personaSourceUrl.value = ''
  personaContent.value = ''
}

async function appendPersonaImages(files: FileList | null) {
  if (!files?.length) return
  recognizingPersona.value = true
  try {
    syncSourceTypeFromInput()
    await store.analyzePersonaIntelligence(
      {
        title: personaTitle.value.trim() || `${selectedSource.value.label}截图资料`,
        source_type: personaSourceType.value,
        source_url: personaSourceUrl.value.trim(),
        content: personaContent.value.trim(),
      },
      files
    )
    personaTitle.value = ''
    personaSourceUrl.value = ''
    personaContent.value = ''
    showToast(`已上传 ${files.length} 个文件，正在生成多模态客户情报`)
  } catch (error) {
    showToast(error instanceof Error ? error.message : '客户截图分析失败')
  } finally {
    recognizingPersona.value = false
  }
}
</script>

<template>
  <section class="panorama">
    <div class="profile-hero">
      <div class="hero-copy">
        <span>客户情报中枢</span>
        <strong>{{ customer?.nickname || '请选择客户' }}</strong>
        <p>把抖音、朋友圈、企查查、官网和聊天记录分层吸收，最后沉淀成企业全方位解析和可执行打法。</p>
      </div>
      <div class="score-ring" :style="scoreStyle">
        <strong>{{ score }}</strong>
        <span>{{ customer?.category || customer?.intention_level || 'C' }} 类</span>
      </div>
    </div>

    <article class="status-strip">
      <div>
        <span>{{ customer?.lifecycle_status === 'closed' ? '已成交样本' : '跟进中客户' }}</span>
        <strong>{{ customer?.lifecycle_status === 'closed' ? '沉淀成交经验，反哺后续话术' : '还没成交，先补齐判断证据' }}</strong>
      </div>
      <button
        type="button"
        :class="{ secondary: customer?.lifecycle_status === 'closed' }"
        :disabled="!customer"
        @click="emit('updateStatus', customer?.lifecycle_status === 'closed' ? 'active' : 'closed')"
      >
        {{ customer?.lifecycle_status === 'closed' ? '恢复跟进' : '标记已成交' }}
      </button>
    </article>

    <article class="battle-board">
      <div class="board-head">
        <div>
          <span>企业全方位解析</span>
          <strong>先看真实证据，再给销售打法</strong>
        </div>
        <em>{{ customer?.persona_updated_at ? customer.persona_updated_at.slice(0, 10) : '等待资料' }}</em>
      </div>
      <div class="battle-grid">
        <article v-for="card in battleCards" :key="card.label" class="battle-card">
          <span>{{ card.label }}</span>
          <strong>{{ card.title }}</strong>
          <p>{{ card.hint }}</p>
          <button v-if="card.copyable" type="button" @click="copyCard(card.title)">复制破冰</button>
        </article>
      </div>
    </article>

    <article class="workflow-panel">
      <div class="board-head">
        <div>
          <span>投喂客户情报</span>
          <strong>粘贴链接/分享文案，或上传截图资料</strong>
        </div>
        <em>资料完成度 {{ sourceProgress }}</em>
      </div>

      <div class="workflow-steps">
        <div v-for="(step, index) in workflowSteps" :key="step.title" :class="{ done: step.done }">
          <b>{{ index + 1 }}</b>
          <strong>{{ step.title }}</strong>
          <span>{{ step.desc }}</span>
        </div>
      </div>

      <div class="source-grid">
        <button
          v-for="item in sourceTypes"
          :key="item.value"
          :class="{ active: personaSourceType === item.value, done: completedSourceTypes.has(item.value) }"
          type="button"
          @click="personaSourceType = item.value"
        >
          <strong>{{ item.short }}</strong>
          <span>{{ item.guide }}</span>
        </button>
      </div>

      <div class="intake-card">
        <div class="intake-head">
          <span>系统已识别：{{ selectedSource.label }}</span>
          <strong>截图会被直接看图分析；抖音看账号和内容，企查查看企业真实情况，朋友圈看性格和信任偏好</strong>
        </div>
        <input v-model="personaTitle" :placeholder="`资料标题：${selectedSource.label} / 客户公开资料`" @input="syncSourceTypeFromInput" />
        <input v-model="personaSourceUrl" placeholder="来源链接：抖音主页、企查查页面、官网链接，可不填" @input="syncSourceTypeFromInput" />
        <textarea
          v-model="personaContent"
          rows="6"
          :placeholder="`${selectedSource.placeholder}\n\n也可以直接粘贴抖音分享文案，例如：复制打开抖音，看看【某某厂家的作品】... https://v.douyin.com/... 系统会自动解析短链、视频 ID 和公开落地页。`"
          @input="syncSourceTypeFromInput"
        ></textarea>
        <div class="action-row">
          <label class="file-drop">
            {{ recognizingPersona ? '正在直接看图并生成客户情报...' : '上传截图并深度分析 / Word / PDF' }}
            <input accept=".doc,.docx,.pdf,image/*" multiple type="file" @change="appendPersonaImages(($event.target as HTMLInputElement).files)" />
          </label>
          <button class="primary" type="button" @click="submitPersona">保存并分析</button>
        </div>
      </div>
    </article>

    <div class="signal-grid">
      <article>
        <span>核心诉求</span>
        <strong>{{ customer?.core_demand || analysis?.core_demand || '等待分析' }}</strong>
      </article>
      <article>
        <span>当前异议</span>
        <strong>{{ customer?.objection || analysis?.objection || '暂无明确异议' }}</strong>
      </article>
      <article>
        <span>下一步动作</span>
        <MarkdownView :content="analysis?.next_action || '继续确认需求、预算与决策链路'" />
      </article>
    </div>

    <article class="panel profile-memory">
      <div class="panel-head">
        <strong>持续客户判断</strong>
        <span>{{ customer?.persona_updated_at ? customer.persona_updated_at.slice(0, 10) : '长期更新' }}</span>
      </div>
      <MarkdownView v-if="customer?.persona_profile" :content="customer.persona_profile" />
      <p v-else class="empty-text">客户判断不是一次性的。持续上传抖音、企查查、官网和聊天截图后，系统会逐步更新长期画像。</p>
    </article>

    <article class="panel">
      <div class="panel-head">
        <strong>已吸收情报</strong>
        <button class="ghost-toggle" type="button" @click="showSourceRecords = !showSourceRecords">
          {{ showSourceRecords ? '收起原始资料' : `查看原始资料 ${personaSources.length} 条` }}
        </button>
      </div>
      <div class="coverage-row">
        <span v-for="item in sourceTypes" :key="item.value" :class="{ active: completedSourceTypes.has(item.value) }">
          {{ item.label }} {{ completedSourceTypes.has(item.value) ? '已吸收' : '待补充' }}
        </span>
      </div>
      <div v-if="showSourceRecords" class="record-list">
        <div v-for="source in personaSources" :key="source.id" class="record">
          <div class="record-head">
            <strong>{{ source.title }}</strong>
            <span>{{ sourceTypeLabel(source.source_type) }}</span>
          </div>
          <a v-if="source.source_url" class="source-link" :href="source.source_url" rel="noreferrer" target="_blank">{{ source.source_url }}</a>
          <MarkdownView :content="source.persona_summary || '已保存资料，等待分析补充。'" />
        </div>
        <p v-if="!personaSources.length" class="empty">暂无资料。先上传抖音主页或企查查摘要，作战卡会更准。</p>
      </div>
    </article>

    <article class="panel">
      <div class="panel-head">
        <strong>客户标签</strong>
        <span>{{ customer?.tags?.length || 0 }} 个</span>
      </div>
      <div class="tag-cloud">
        <span v-for="tag in customer?.tags || []" :key="`${tag.tag_type}-${tag.tag_name}`">
          {{ tag.tag_name }}
        </span>
        <em v-if="!customer?.tags?.length">暂无标签，导入聊天记录后会自动生成。</em>
      </div>
    </article>

    <article class="panel">
      <div class="panel-head">
        <strong>客户反馈复盘</strong>
        <span>让销售助手越用越懂你</span>
      </div>
      <select v-model="selectedReply">
        <option value="">选择本次使用的话术</option>
        <option v-for="reply in replyOptions" :key="reply" :value="reply">{{ reply.replace(/\*\*/g, '') }}</option>
      </select>
      <div class="outcome">
        <button :class="{ active: outcome === 'good' }" type="button" @click="outcome = 'good'">效果好</button>
        <button :class="{ active: outcome === 'neutral' }" type="button" @click="outcome = 'neutral'">一般</button>
        <button :class="{ active: outcome === 'bad' }" type="button" @click="outcome = 'bad'">效果差</button>
      </div>
      <textarea v-model="customerReply" rows="3" placeholder="客户实际回复：继续问价格、愿意约时间、沉默、反感推销等"></textarea>
      <textarea v-model="salesReview" rows="3" placeholder="销售自己的看法：客户没被打动、案例方向有效、解释太早、下次需要换角度等"></textarea>
      <button class="primary" type="button" @click="submitFeedback">保存复盘</button>

      <div class="record-list">
        <div v-for="record in feedbackRecords" :key="record.id" class="record feedback">
          <span>{{ record.outcome === 'good' ? '效果好' : record.outcome === 'bad' ? '效果差' : '一般' }}</span>
          <p>{{ record.lesson }}</p>
        </div>
        <p v-if="!feedbackRecords.length" class="empty">暂无复盘记录</p>
      </div>
    </article>
  </section>
</template>

<style scoped>
.panorama {
  display: grid;
  gap: 14px;
  padding: 14px;
}

.profile-hero,
.status-strip,
.battle-board,
.workflow-panel,
.panel,
.signal-grid article {
  border: 1px solid var(--line);
  border-radius: var(--radius-lg);
  background: var(--surface);
  box-shadow: var(--shadow-soft);
}

.profile-hero {
  position: relative;
  overflow: hidden;
  display: grid;
  grid-template-columns: 1fr 94px;
  align-items: center;
  gap: 16px;
  padding: 20px;
  background:
    linear-gradient(135deg, oklch(1 0.004 95), oklch(0.955 0.026 178) 62%, oklch(0.985 0.032 86));
}

.profile-hero::before {
  content: "";
  position: absolute;
  right: -42px;
  top: -54px;
  width: 160px;
  height: 160px;
  border: 28px solid oklch(0.78 0.07 178 / 0.14);
  border-radius: 50%;
}

.hero-copy {
  position: relative;
  z-index: 1;
  display: grid;
  gap: 6px;
}

.hero-copy span,
.board-head span,
.signal-grid span,
.panel-head span,
.intake-head span,
.status-strip span,
.battle-card span {
  color: var(--brand-strong);
  font-size: 11px;
  font-weight: 950;
  letter-spacing: 0.08em;
}

.hero-copy strong {
  color: var(--ink);
  font-size: 24px;
  letter-spacing: -0.05em;
  line-height: 1.1;
}

.hero-copy p,
.battle-card p,
.empty-text,
.record p {
  margin: 0;
  color: var(--muted);
  font-size: 13px;
  line-height: 1.6;
}

.score-ring {
  position: relative;
  z-index: 1;
  display: grid;
  place-items: center;
  align-content: center;
  width: 88px;
  height: 88px;
  border-radius: 50%;
  background:
    radial-gradient(circle at center, white 58%, transparent 59%),
    conic-gradient(var(--brand) var(--score), oklch(0.9 0.018 105) 0);
  box-shadow: 0 14px 28px oklch(0.34 0.095 184 / 0.14);
}

.score-ring strong {
  color: var(--brand-strong);
  font-size: 26px;
}

.score-ring span {
  color: var(--muted);
  font-size: 11px;
  font-weight: 900;
}

.status-strip {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 14px;
  background: linear-gradient(135deg, white, oklch(0.972 0.028 86));
}

.status-strip div {
  display: grid;
  gap: 4px;
}

.status-strip strong {
  color: var(--ink);
  font-size: 14px;
}

.status-strip button,
.primary,
.battle-card button {
  min-height: 38px;
  border: 0;
  border-radius: 14px;
  color: white;
  background: linear-gradient(135deg, var(--brand-strong), var(--brand));
  font-size: 12px;
  font-weight: 950;
  box-shadow: 0 12px 24px oklch(0.34 0.095 184 / 0.18);
}

.status-strip button {
  min-width: 96px;
  padding: 0 12px;
}

.status-strip .secondary {
  color: var(--brand-strong);
  border: 1px solid var(--line-strong);
  background: var(--brand-soft);
  box-shadow: none;
}

.status-strip button:disabled {
  opacity: 0.5;
}

.battle-board,
.workflow-panel,
.panel {
  display: grid;
  gap: 14px;
  padding: 15px;
}

.board-head,
.panel-head,
.record-head,
.intake-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.board-head div,
.intake-head {
  display: grid;
  gap: 4px;
}

.board-head strong,
.panel-head strong,
.intake-head strong {
  color: var(--ink);
  font-size: 16px;
  letter-spacing: -0.03em;
}

.board-head em {
  flex: 0 0 auto;
  padding: 5px 8px;
  border-radius: 999px;
  color: var(--muted);
  background: var(--surface-soft);
  font-size: 11px;
  font-style: normal;
  font-weight: 900;
}

.battle-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}

.battle-card {
  position: relative;
  overflow: hidden;
  display: grid;
  gap: 9px;
  min-height: 152px;
  padding: 14px;
  border: 1px solid oklch(0.87 0.02 105);
  border-radius: var(--radius-md);
  background:
    linear-gradient(180deg, white, oklch(0.983 0.012 104));
}

.battle-card::after {
  content: "";
  position: absolute;
  right: -30px;
  bottom: -42px;
  width: 100px;
  height: 100px;
  border-radius: 50%;
  background: oklch(0.88 0.06 178 / 0.38);
}

.battle-card strong {
  position: relative;
  z-index: 1;
  color: var(--ink);
  font-size: 15px;
  line-height: 1.55;
}

.battle-card p,
.battle-card button {
  position: relative;
  z-index: 1;
}

.battle-card button {
  width: fit-content;
  min-height: 32px;
  padding: 0 12px;
  box-shadow: none;
}

.workflow-steps {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 8px;
}

.workflow-steps div {
  display: grid;
  gap: 5px;
  padding: 11px;
  border: 1px solid var(--line);
  border-radius: 15px;
  background: oklch(0.985 0.01 105);
}

.workflow-steps .done {
  border-color: oklch(0.78 0.06 178);
  background: var(--brand-soft);
}

.workflow-steps b {
  display: grid;
  place-items: center;
  width: 24px;
  height: 24px;
  border-radius: 999px;
  color: white;
  background: var(--brand);
  font-size: 12px;
}

.workflow-steps strong {
  color: var(--ink);
  font-size: 13px;
}

.workflow-steps span,
.source-grid span {
  color: var(--muted);
  font-size: 11px;
  line-height: 1.45;
}

.source-grid {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 8px;
}

.source-grid button {
  display: grid;
  gap: 5px;
  min-height: 76px;
  border: 1px solid var(--line);
  border-radius: 16px;
  padding: 10px;
  color: var(--muted);
  background: white;
  text-align: left;
}

.source-grid strong {
  color: var(--ink);
  font-size: 13px;
}

.source-grid .active {
  border-color: var(--brand);
  background: linear-gradient(180deg, var(--brand-soft), white);
  box-shadow: inset 0 0 0 1px oklch(0.79 0.058 178 / 0.28);
}

.source-grid .done strong::after {
  content: " 已补";
  color: var(--brand-strong);
  font-size: 11px;
}

.intake-card {
  display: grid;
  gap: 10px;
  padding: 13px;
  border: 1px solid oklch(0.86 0.02 105);
  border-radius: var(--radius-md);
  background: oklch(0.992 0.006 105);
}

select,
input,
textarea {
  width: 100%;
  border: 1px solid oklch(0.86 0.021 105);
  border-radius: 14px;
  padding: 11px 12px;
  color: var(--ink);
  background: white;
  font-size: 13px;
  line-height: 1.55;
  box-shadow: inset 0 1px 0 oklch(1 0 0 / 0.78);
}

select {
  height: 42px;
}

textarea {
  resize: vertical;
}

.action-row {
  display: grid;
  grid-template-columns: 1fr 128px;
  gap: 9px;
}

.file-drop {
  display: grid;
  place-items: center;
  min-height: 38px;
  border: 1px dashed var(--line-strong);
  border-radius: 14px;
  color: var(--brand-strong);
  background: var(--brand-soft);
  font-size: 12px;
  font-weight: 950;
}

.file-drop input {
  display: none;
}

.signal-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
}

.signal-grid article {
  padding: 14px;
}

.signal-grid strong {
  display: block;
  margin-top: 7px;
  color: var(--ink);
  font-size: 15px;
  line-height: 1.45;
}

.tag-cloud {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.tag-cloud span,
.record span {
  padding: 5px 9px;
  border: 1px solid oklch(0.84 0.04 175);
  border-radius: 999px;
  color: var(--brand-strong);
  background: var(--brand-soft);
  font-size: 12px;
  font-weight: 850;
}

.tag-cloud em,
.empty {
  color: var(--muted);
  font-style: normal;
  font-size: 13px;
}

.outcome {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px;
}

.outcome button {
  height: 35px;
  border: 1px solid var(--line);
  border-radius: 14px;
  color: var(--muted);
  background: white;
  font-weight: 850;
}

.outcome .active {
  color: var(--brand-strong);
  border-color: var(--line-strong);
  background: var(--brand-soft);
}

.record-list {
  display: grid;
  gap: 9px;
}

.ghost-toggle {
  border: 1px solid var(--line);
  border-radius: 999px;
  padding: 6px 10px;
  color: var(--brand-strong);
  background: white;
  font-size: 12px;
  font-weight: 900;
}

.coverage-row {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.coverage-row span {
  padding: 6px 9px;
  border: 1px solid var(--line);
  border-radius: 999px;
  color: var(--muted);
  background: oklch(0.985 0.01 105);
  font-size: 12px;
  font-weight: 850;
}

.coverage-row .active {
  color: var(--brand-strong);
  border-color: var(--line-strong);
  background: var(--brand-soft);
}

.record {
  display: grid;
  gap: 7px;
  padding: 12px;
  border: 1px solid oklch(0.88 0.018 105);
  border-radius: 15px;
  background: oklch(0.985 0.01 105);
}

.record-head strong {
  min-width: 0;
  overflow: hidden;
  color: var(--ink);
  font-size: 14px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.record-head span {
  flex: 0 0 auto;
}

.source-link {
  min-width: 0;
  overflow: hidden;
  color: var(--brand-strong);
  font-size: 12px;
  font-weight: 850;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.empty {
  margin: 0;
  padding: 12px;
  text-align: center;
}

@media (max-width: 760px) {
  .battle-grid,
  .workflow-steps {
    grid-template-columns: 1fr 1fr;
  }

  .source-grid {
    grid-template-columns: 1fr 1fr;
  }
}

@media (max-width: 560px) {
  .profile-hero,
  .status-strip {
    grid-template-columns: 1fr;
  }

  .status-strip {
    display: grid;
  }

  .score-ring {
    width: 78px;
    height: 78px;
  }

  .battle-grid,
  .workflow-steps,
  .signal-grid,
  .action-row {
    grid-template-columns: 1fr;
  }

  .source-grid {
    grid-template-columns: 1fr;
  }
}
</style>

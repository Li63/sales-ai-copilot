<script setup lang="ts">
import { computed, ref } from 'vue'
import { showToast } from 'vant'
import type { Analysis, Customer, FeedbackRecord, PersonaSource } from '../stores/sidebar'
import { useSidebarStore } from '../stores/sidebar'
import MarkdownView from './MarkdownView.vue'

const props = defineProps<{
  customer: Customer | null
  analysis: Analysis | null
  feedbackRecords: FeedbackRecord[]
  personaSources: PersonaSource[]
}>()

const emit = defineEmits<{
  addFeedback: [payload: { ai_reply: string; customer_reply: string; sales_review: string; outcome: 'good' | 'bad' | 'neutral'; original_customer_question?: string }]
  addPersona: [payload: { title: string; content: string; source_type: string }]
  updateStatus: [status: 'active' | 'closed']
}>()

const store = useSidebarStore()
const selectedReply = ref('')
const customerReply = ref('')
const salesReview = ref('')
const outcome = ref<'good' | 'bad' | 'neutral'>('good')
const personaTitle = ref('')
const personaContent = ref('')
const recognizingPersona = ref(false)

const replyOptions = computed(() => props.analysis?.reply_suggestions || [])
const score = computed(() => props.customer?.intention_score ?? 50)
const scoreStyle = computed(() => `--score: ${Math.max(0, Math.min(100, score.value))}%`)

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
    outcome: outcome.value
  })
  customerReply.value = ''
  salesReview.value = ''
}

function submitPersona() {
  if (!personaContent.value.trim()) {
    showToast('请粘贴客户资料，或上传 Word/PDF/图片后补充关键文字')
    return
  }
  emit('addPersona', {
    title: personaTitle.value.trim() || '客户公开资料',
    source_type: 'manual',
    content: personaContent.value.trim()
  })
  personaTitle.value = ''
  personaContent.value = ''
}

async function appendPersonaImages(files: FileList | null) {
  if (!files?.length) return
  recognizingPersona.value = true
  try {
    const text = await store.extractFiles('persona', files)
    personaContent.value = [personaContent.value.trim(), text.trim()].filter(Boolean).join('\n\n')
    showToast(`已解析 ${files.length} 个客户资料文件`)
  } catch (error) {
    showToast(error instanceof Error ? error.message : '文件解析失败')
  } finally {
    recognizingPersona.value = false
  }
}
</script>

<template>
  <section class="panorama">
    <div class="hero">
      <div>
        <span>客户全景建设</span>
        <strong>{{ customer?.nickname || '请选择客户' }}</strong>
        <p>把客户意向、人设资料、沟通反馈和下一步成交路径放在一起看，减少销售凭感觉跟进。</p>
      </div>
      <div class="score-ring" :style="scoreStyle">
        <strong>{{ score }}</strong>
        <span>{{ customer?.category || customer?.intention_level || 'C' }} 类</span>
      </div>
    </div>

    <article class="panel status-panel">
      <div>
        <strong>{{ customer?.lifecycle_status === 'closed' ? '客户已成交' : '成交状态' }}</strong>
        <p>
          {{
            customer?.lifecycle_status === 'closed'
              ? `系统会重点学习这个客户的成交节奏、客户全景和有效话术，用来优化后续建议。${customer?.closed_at ? `成交时间：${customer.closed_at.slice(0, 10)}` : ''}`
              : '确认成交后请标记为已成交，系统会把它作为高价值成功样本持续沉淀。'
          }}
        </p>
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

    <div class="insight-grid">
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

    <article class="panel profile-memory">
      <div class="panel-head">
        <strong>持续客户判断</strong>
        <span>{{ customer?.persona_updated_at ? customer.persona_updated_at.slice(0, 10) : '长期更新' }}</span>
      </div>
      <p v-if="customer?.persona_profile">{{ customer.persona_profile }}</p>
      <p v-else class="empty-text">客户判断不是一次性的。后续持续上传朋友圈、聊天截图、自媒体内容后，系统会逐步更新这个客户的长期画像和跟进判断。</p>
    </article>

    <article class="panel">
      <div class="panel-head">
        <strong>客户人设资料</strong>
        <span>长期积累，持续进化</span>
      </div>
      <input v-model="personaTitle" placeholder="资料标题：朋友圈动态、公众号文章、视频号简介" />
      <textarea v-model="personaContent" rows="5" placeholder="粘贴客户公开内容，或上传朋友圈截图、Word、PDF。资料会绑定当前客户，用于后续判断沟通风格与跟进角度。"></textarea>
      <label class="image-upload">
        {{ recognizingPersona ? '正在解析客户资料文件...' : '上传客户资料图片 / Word / PDF' }}
        <input accept=".doc,.docx,.pdf,image/*" multiple type="file" @change="appendPersonaImages(($event.target as HTMLInputElement).files)" />
      </label>
      <button class="primary" type="button" @click="submitPersona">保存人设资料</button>

      <div class="persona-ai-card">
        <div class="persona-ai-head">
          <strong>AI 对客户的实时判断</strong>
          <span>{{ customer?.persona_updated_at ? customer.persona_updated_at.slice(0, 10) : '保存后生成' }}</span>
        </div>
        <MarkdownView
          v-if="customer?.persona_profile"
          :content="customer.persona_profile"
        />
        <p v-else>
          保存客户朋友圈、聊天截图或公开资料后，这里会展示 AI 对客户性格、关注点、沟通偏好和跟进角度的判断，销售可以马上拿来参考。
        </p>
      </div>

      <div class="record-list">
        <div v-for="source in personaSources" :key="source.id" class="record">
          <div class="record-head">
            <strong>{{ source.title }}</strong>
            <span>AI 分析</span>
          </div>
          <MarkdownView :content="source.persona_summary || '已保存资料，等待分析补充。'" />
        </div>
        <p v-if="!personaSources.length" class="empty">暂无该客户的人设资料</p>
      </div>
    </article>

    <article class="panel">
      <div class="panel-head">
        <strong>客户反馈复盘</strong>
        <span>让您的销售助手更加智能好用</span>
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
  gap: 12px;
  padding: 12px;
}

.hero,
.panel,
.insight-grid article {
  border: 1px solid var(--line);
  border-radius: 8px;
  background: var(--surface);
  box-shadow: var(--shadow-soft);
}

.hero {
  display: grid;
  grid-template-columns: 1fr 92px;
  align-items: center;
  gap: 14px;
  padding: 15px;
  color: white;
  background: linear-gradient(135deg, oklch(0.29 0.055 230), oklch(0.4 0.085 175));
}

.hero span {
  color: oklch(0.84 0.055 178);
  font-size: 12px;
  font-weight: 900;
}

.hero strong {
  display: block;
  margin-top: 4px;
  font-size: 20px;
  line-height: 1.2;
}

.hero p {
  margin: 8px 0 0;
  color: oklch(0.94 0.018 190);
  font-size: 13px;
  line-height: 1.55;
}

.score-ring {
  display: grid;
  place-items: center;
  align-content: center;
  width: 86px;
  height: 86px;
  border-radius: 50%;
  background:
    radial-gradient(circle at center, white 58%, transparent 59%),
    conic-gradient(var(--brand-soft) var(--score), oklch(1 0 0 / 0.22) 0);
}

.score-ring strong {
  color: var(--brand-strong);
  font-size: 24px;
}

.score-ring span {
  margin-top: 1px;
  color: var(--muted);
  font-size: 11px;
  font-weight: 900;
}

.insight-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 8px;
}

.insight-grid article,
.panel {
  padding: 13px;
}

.insight-grid span,
.panel-head span {
  color: var(--muted);
  font-size: 12px;
  font-weight: 800;
}

.insight-grid strong {
  display: block;
  margin-top: 6px;
  color: var(--ink);
  font-size: 14px;
  line-height: 1.45;
}

.panel {
  display: grid;
  gap: 10px;
}

.panel-head {
  display: flex;
  justify-content: space-between;
  gap: 10px;
}

.panel-head strong {
  color: var(--ink);
  font-size: 15px;
}

select,
input,
textarea {
  width: 100%;
  border: 1px solid var(--line);
  border-radius: 8px;
  padding: 10px;
  color: var(--ink);
  background: var(--surface-raised);
  font-size: 13px;
  line-height: 1.55;
}

select {
  height: 40px;
}

textarea {
  resize: vertical;
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
  font-weight: 800;
}

.tag-cloud em,
.empty {
  color: var(--muted);
  font-style: normal;
  font-size: 13px;
}

.image-upload {
  display: grid;
  place-items: center;
  min-height: 38px;
  border: 1px dashed oklch(0.76 0.055 175);
  border-radius: 8px;
  color: var(--brand-strong);
  background: var(--brand-soft);
  font-size: 12px;
  font-weight: 900;
}

.image-upload input {
  display: none;
}

.primary {
  height: 39px;
  border: 0;
  border-radius: 8px;
  color: white;
  background: var(--brand);
  font-weight: 900;
}

.status-panel {
  grid-template-columns: 1fr auto;
  align-items: center;
}

.status-panel strong {
  display: block;
  color: var(--ink);
  font-size: 15px;
}

.status-panel p {
  margin: 5px 0 0;
  color: var(--muted);
  font-size: 12px;
  line-height: 1.55;
}

.status-panel button {
  min-width: 96px;
  min-height: 36px;
  border: 0;
  border-radius: 8px;
  color: white;
  background: var(--brand);
  font-size: 12px;
  font-weight: 900;
}

.status-panel button:disabled {
  opacity: 0.5;
}

.status-panel .secondary {
  color: var(--brand-strong);
  border: 1px solid oklch(0.78 0.055 175);
  background: var(--brand-soft);
}

.outcome {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px;
}

.outcome button {
  height: 34px;
  border: 1px solid var(--line);
  border-radius: 8px;
  color: var(--muted);
  background: white;
  font-weight: 800;
}

.outcome .active {
  color: var(--brand-strong);
  border-color: oklch(0.78 0.055 175);
  background: var(--brand-soft);
}

.record-list {
  display: grid;
  gap: 8px;
}

.persona-ai-card {
  display: grid;
  gap: 8px;
  padding: 11px;
  border: 1px solid oklch(0.78 0.055 175);
  border-radius: 8px;
  background: linear-gradient(180deg, var(--brand-soft), white);
}

.persona-ai-head,
.record-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.persona-ai-head strong,
.record-head strong {
  min-width: 0;
  overflow: hidden;
  color: var(--ink);
  font-size: 13px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.persona-ai-head span,
.record-head span {
  flex: 0 0 auto;
  color: var(--brand-strong);
  font-size: 12px;
  font-weight: 900;
}

.persona-ai-card p {
  margin: 0;
  color: var(--muted);
  font-size: 12px;
  line-height: 1.55;
}

.record {
  display: grid;
  gap: 6px;
  padding: 10px;
  border: 1px solid var(--line);
  border-radius: 8px;
  background: var(--surface-soft);
}

.record p,
.empty,
.profile-memory p {
  margin: 0;
  line-height: 1.55;
}

.record p,
.profile-memory p {
  color: var(--muted);
  font-size: 12px;
  white-space: pre-line;
}

.empty {
  padding: 12px;
  text-align: center;
}

.empty-text {
  color: var(--muted);
}

@media (max-width: 560px) {
  .hero {
    grid-template-columns: 1fr;
  }

  .score-ring {
    width: 78px;
    height: 78px;
  }

  .insight-grid {
    grid-template-columns: 1fr;
  }

  .status-panel {
    grid-template-columns: 1fr;
  }
}
</style>

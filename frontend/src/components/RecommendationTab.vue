<script setup lang="ts">
import { ref } from 'vue'
import { showToast } from 'vant'
import type { Analysis, Customer, IntentReply } from '../stores/sidebar'
import { useSidebarStore } from '../stores/sidebar'
import { copyPlainText } from '../utils/clipboard'
import MarkdownView from './MarkdownView.vue'

defineProps<{
  analysis: Analysis | null
  customer: Customer | null
  customers: Customer[]
}>()

const emit = defineEmits<{
  import: [transcript: string]
  selectCustomer: [externalUserId: string]
  createCustomer: [nickname: string]
  refreshAnalysis: []
}>()

const styles = ['专业正式', '亲和拉近', '引导提问']
const store = useSidebarStore()
const transcript = ref('')
const newCustomerName = ref('')
const intent = ref('')
const intentReply = ref<IntentReply | null>(null)
const recognizing = ref(false)

async function copyText(text: string) {
  const copied = await copyPlainText(text)
  showToast(copied ? '\u5df2\u590d\u5236\u8bdd\u672f' : '\u590d\u5236\u5931\u8d25\uff0c\u8bf7\u957f\u6309\u6587\u5b57\u590d\u5236')
}

function submitTranscript() {
  const value = transcript.value.trim()
  if (!value) {
    showToast('请先粘贴聊天记录')
    return
  }
  emit('import', value)
  transcript.value = ''
}

function createCustomer() {
  const value = newCustomerName.value.trim()
  if (!value) {
    showToast('客户名称是必填项')
    return
  }
  emit('createCustomer', value)
  newCustomerName.value = ''
}

function selectCustomer(event: Event) {
  const target = event.target as HTMLSelectElement
  if (target.value) {
    emit('selectCustomer', target.value)
  }
}

async function appendChatScreenshots(files: FileList | null) {
  if (!files?.length) return
  recognizing.value = true
  try {
    const text = await store.extractFiles('chat', files)
    transcript.value = [transcript.value.trim(), text.trim()].filter(Boolean).join('\n')
    showToast(`已解析 ${files.length} 个聊天文件`)
  } catch (error) {
    showToast(error instanceof Error ? error.message : '文件解析失败')
  } finally {
    recognizing.value = false
  }
}

async function generateIntentReply() {
  const value = intent.value.trim()
  if (!value) {
    showToast('请先写下你想对客户表达的意思')
    return
  }
  try {
    intentReply.value = await store.generateIntentReply(value)
    showToast('已生成定制话术')
  } catch (error) {
    showToast(error instanceof Error ? error.message : '定制话术生成失败')
  }
}
</script>

<template>
  <section class="recommendation">
    <div class="customer-panel">
      <div class="panel-head">
        <div>
          <span>当前客户</span>
          <strong>{{ customer?.nickname || '请选择客户' }}</strong>
        </div>
        <span class="level">{{ customer?.category || customer?.intention_level || 'C' }}</span>
      </div>

      <select :value="customer?.external_userid || ''" @change="selectCustomer">
        <option value="">选择已有客户</option>
        <option v-for="item in customers" :key="item.external_userid" :value="item.external_userid">
          {{ item.nickname }} · {{ item.lifecycle_status === 'closed' ? '已成交' : item.category || item.intention_level }} · {{ item.intention_score }}分
        </option>
      </select>

      <div class="new-customer">
        <input v-model="newCustomerName" placeholder="新客户名称（必填）" />
        <button type="button" @click="createCustomer">新建</button>
      </div>
    </div>

    <div class="import-panel">
      <div class="panel-head">
        <div>
          <span>聊天输入</span>
          <strong>粘贴记录或上传截图</strong>
        </div>
        <button type="button" @click="submitTranscript">分析</button>
      </div>
      <textarea
        v-model="transcript"
        rows="5"
        placeholder="客户：价格多少钱？
销售：我先给您拆一下费用。
客户：有没有同行案例？"
      ></textarea>
      <label class="image-upload">
        {{ recognizing ? '正在连续解析文件...' : '上传聊天截图 / Word / PDF 并识别' }}
        <input accept=".doc,.docx,.pdf,image/*" multiple type="file" @change="appendChatScreenshots(($event.target as HTMLInputElement).files)" />
      </label>
    </div>

    <div class="signal-grid">
      <div>
        <span>核心诉求</span>
        <strong>{{ analysis?.core_demand || '等待分析' }}</strong>
      </div>
      <div>
        <span>当前异议</span>
        <strong>{{ analysis?.objection || '暂无明确异议' }}</strong>
      </div>
    </div>

    <div class="next-action">
      <span>下一步动作</span>
      <MarkdownView :content="analysis?.next_action || '继续确认需求、预算与决策链路'" />
    </div>

    <div class="intent-panel">
      <div class="panel-head">
        <div>
          <span>不会开口时</span>
          <strong>告诉 AI 你想推进什么</strong>
        </div>
        <button type="button" @click="generateIntentReply">生成</button>
      </div>
      <textarea
        v-model="intent"
        rows="3"
        placeholder="例如：我想提醒客户尽快确认预算，但不想显得太催；我想约客户明天看方案；我想让客户把老板拉进来一起沟通。"
      ></textarea>
      <article v-if="intentReply" class="intent-result">
        <span>定制话术</span>
        <MarkdownView :content="intentReply.reply_suggestion" />
        <div class="reply-reason">
          <strong>为什么这样讲</strong>
          <p>{{ intentReply.reply_explanation }}</p>
        </div>
        <div class="reply-reason">
          <strong>下一步观察</strong>
          <p>{{ intentReply.next_action }}</p>
        </div>
        <button type="button" @click="copyText(intentReply.reply_suggestion)">复制这条</button>
      </article>
    </div>

    <div class="reply-toolbar">
      <strong>推荐回复策略</strong>
      <button type="button" @click="emit('refreshAnalysis')">刷新策略</button>
    </div>

    <div class="reply-list">
      <button
        v-for="(reply, index) in analysis?.reply_suggestions || []"
        :key="`${index}-${reply}`"
        class="reply-card"
        type="button"
        @click="copyText(reply)"
      >
        <span>{{ styles[index] || '推荐' }}</span>
        <MarkdownView :content="reply" :copyable="false" />
        <div class="reply-reason">
          <strong>回复解析</strong>
          <p>{{ analysis?.reply_explanations?.[index] || '先接住客户当前关注点，再用一个可验证的小承诺推动下一步。' }}</p>
        </div>
        <em>点击复制</em>
      </button>

      <div v-if="!analysis?.reply_suggestions?.length" class="empty-card">
        <strong>还没有话术建议</strong>
        <p>先选择客户并粘贴一段聊天记录，系统会给出三种回复风格、回复解析和下一步跟进动作。</p>
      </div>
    </div>
  </section>
</template>

<style scoped>
.recommendation {
  display: grid;
  gap: 14px;
  padding: 14px;
}

.customer-panel,
.import-panel,
.signal-grid div,
.next-action,
.intent-panel,
.intent-result,
.reply-card,
.empty-card {
  border: 1px solid oklch(1 0 0 / 0.62);
  border-radius: var(--radius-md);
  background: var(--surface-glass);
  box-shadow: var(--shadow-soft);
  backdrop-filter: blur(16px);
}

.customer-panel,
.import-panel,
.intent-panel {
  display: grid;
  gap: 12px;
  padding: 14px;
}

.customer-panel {
  position: relative;
  overflow: hidden;
  border-color: oklch(0.78 0.052 175 / 0.74);
  background:
    radial-gradient(circle at 92% 12%, oklch(0.89 0.078 82 / 0.7), transparent 170px),
    radial-gradient(circle at 10% 0%, oklch(0.82 0.08 178 / 0.22), transparent 180px),
    linear-gradient(135deg, oklch(1 0.004 95 / 0.94), var(--brand-soft) 112%);
}

.customer-panel::after {
  content: "";
  position: absolute;
  right: -30px;
  bottom: -54px;
  width: 130px;
  height: 130px;
  border: 1px solid oklch(0.79 0.055 175 / 0.42);
  border-radius: 50%;
}

.panel-head {
  position: relative;
  z-index: 1;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.panel-head div {
  display: grid;
  gap: 2px;
}

.panel-head span,
.signal-grid span,
.next-action > span,
.reply-card > span {
  display: block;
  color: var(--muted);
  font-size: 11px;
  font-weight: 950;
  letter-spacing: 0.04em;
}

.panel-head strong {
  color: var(--ink);
  font-size: 16px;
  letter-spacing: -0.02em;
}

.level {
  min-width: 30px;
  padding: 6px 9px;
  border-radius: 999px;
  color: var(--brand-strong) !important;
  background: oklch(1 0 0 / 0.68);
  text-align: center;
  font-weight: 900 !important;
  box-shadow: inset 0 0 0 1px oklch(0.79 0.052 175 / 0.6);
}

select,
input,
textarea {
  position: relative;
  z-index: 1;
  width: 100%;
  border: 1px solid oklch(0.86 0.021 105);
  border-radius: 14px;
  padding: 11px 12px;
  color: var(--ink);
  background: oklch(1 0.004 95 / 0.78);
  font-size: 13px;
  line-height: 1.55;
  box-shadow: inset 0 1px 0 oklch(1 0 0 / 0.78);
}

select {
  height: 40px;
}

textarea {
  resize: vertical;
}

.new-customer {
  position: relative;
  z-index: 1;
  display: grid;
  grid-template-columns: 1fr 72px;
  gap: 8px;
}

.panel-head button,
.new-customer button {
  height: 34px;
  border: 0;
  border-radius: 14px;
  color: white;
  background:
    radial-gradient(circle at 86% 8%, var(--accent), transparent 38px),
    linear-gradient(135deg, var(--brand-strong), var(--brand));
  font-weight: 900;
  box-shadow: 0 10px 20px oklch(0.34 0.095 184 / 0.18);
}

.image-upload {
  display: grid;
  place-items: center;
  min-height: 40px;
  border: 1px dashed oklch(0.76 0.055 175);
  border-radius: 14px;
  color: var(--brand-strong);
  background:
    linear-gradient(135deg, oklch(0.96 0.04 171), oklch(0.98 0.028 84));
  font-size: 12px;
  font-weight: 900;
}

.image-upload input {
  display: none;
}

.signal-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
}

.signal-grid div,
.next-action {
  padding: 14px;
}

.signal-grid strong {
  display: block;
  margin-top: 6px;
  color: var(--ink);
  font-size: 15px;
  line-height: 1.4;
}

.next-action {
  position: relative;
  overflow: hidden;
  border-color: oklch(0.81 0.052 175 / 0.72);
  background:
    radial-gradient(circle at 100% 0%, oklch(0.88 0.08 84 / 0.74), transparent 160px),
    linear-gradient(135deg, var(--brand-soft), white 72%);
}

.next-action::before {
  content: "NEXT";
  position: absolute;
  right: 12px;
  top: 10px;
  color: oklch(0.73 0.05 175 / 0.34);
  font-size: 22px;
  font-weight: 950;
  letter-spacing: -0.06em;
}

.intent-panel {
  background:
    linear-gradient(180deg, oklch(1 0.004 95), oklch(0.965 0.018 104));
}

.intent-result {
  display: grid;
  gap: 9px;
  padding: 12px;
  border-radius: 14px;
  background: white;
}

.intent-result > span {
  width: fit-content;
  padding: 4px 8px;
  border-radius: 999px;
  color: var(--brand-strong);
  background: var(--brand-soft);
  font-size: 12px;
  font-weight: 900;
}

.intent-result > button,
.reply-toolbar button {
  min-height: 34px;
  border: 0;
  border-radius: 8px;
  color: white;
  background: var(--brand);
  font-size: 12px;
  font-weight: 900;
}

.reply-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  padding: 0 2px;
}

.reply-toolbar strong {
  color: var(--ink);
  font-size: 17px;
  letter-spacing: -0.03em;
}

.reply-toolbar button {
  min-width: 86px;
}

.reply-list {
  display: grid;
  gap: 12px;
}

.reply-card {
  position: relative;
  width: 100%;
  padding: 15px 15px 34px;
  overflow: hidden;
  text-align: left;
  transition: transform 0.18s ease, border-color 0.18s ease, box-shadow 0.18s ease;
}

.reply-card::before {
  content: "";
  position: absolute;
  inset: 0 0 auto;
  height: 4px;
  background: linear-gradient(90deg, var(--brand), var(--accent));
}

.reply-card:active {
  transform: translateY(1px) scale(0.996);
  border-color: var(--brand);
}

.reply-card:hover {
  transform: translateY(-2px);
  border-color: oklch(0.78 0.06 178 / 0.72);
  box-shadow: var(--shadow), 0 0 0 1px oklch(1 0 0 / 0.5);
}

.reply-card > span {
  width: fit-content;
  margin-bottom: 8px;
  padding: 5px 8px;
  border-radius: 999px;
  color: var(--brand-strong);
  background: var(--brand-soft);
}

.reply-reason {
  margin-top: 10px;
  padding: 10px 11px;
  border: 1px solid oklch(0.9 0.018 105);
  border-radius: 14px;
  background: oklch(0.976 0.014 104);
}

.reply-reason strong {
  display: block;
  margin-bottom: 4px;
  color: var(--brand-strong);
  font-size: 12px;
}

.reply-reason p {
  margin: 0;
  color: var(--muted);
  font-size: 12px;
  line-height: 1.5;
}

.reply-card em {
  position: absolute;
  right: 13px;
  bottom: 10px;
  color: var(--subtle);
  font-size: 12px;
  font-style: normal;
}

.empty-card {
  padding: 18px;
  background:
    linear-gradient(135deg, white, oklch(0.97 0.018 104));
}

.empty-card strong {
  display: block;
  margin-bottom: 6px;
  color: var(--ink);
  font-size: 15px;
}

.empty-card p {
  margin: 0;
  color: var(--ink);
  font-size: 14px;
  line-height: 1.6;
}

@media (max-width: 560px) {
  .signal-grid {
    grid-template-columns: 1fr;
  }
}

@media (min-width: 760px) {
  .recommendation {
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: var(--page-gap);
    padding: var(--page-gap);
  }

  .import-panel,
  .intent-panel,
  .reply-toolbar,
  .reply-list {
    grid-column: 1 / -1;
  }

  .reply-list {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (min-width: 1180px) {
  .recommendation {
    grid-template-columns: repeat(12, minmax(0, 1fr));
    align-items: start;
    gap: 12px;
    padding: 0;
  }

  .customer-panel,
  .import-panel,
  .signal-grid div,
  .next-action,
  .intent-panel,
  .intent-result,
  .reply-card,
  .empty-card {
    border-color: #d9e1eb;
    border-radius: 7px;
    background: #ffffff;
    box-shadow: 0 1px 2px rgb(15 23 42 / 5%);
    backdrop-filter: none;
  }

  .customer-panel::after,
  .next-action::before {
    content: none;
  }

  .customer-panel {
    grid-column: span 4;
    min-height: 214px;
    padding: 16px;
    background: #ffffff;
  }

  .import-panel {
    grid-column: span 8;
    min-height: 214px;
    padding: 16px;
  }

  select,
  input,
  textarea {
    border-radius: 7px;
    background: #ffffff;
    box-shadow: none;
  }

  .image-upload {
    border-radius: 7px;
    background: #eff6ff;
  }

  .signal-grid {
    grid-column: span 4;
    align-self: stretch;
  }

  .signal-grid div,
  .next-action,
  .intent-panel {
    border-radius: 7px;
  }

  .signal-grid div {
    min-height: 116px;
    padding: 14px;
  }

  .next-action {
    grid-column: span 4;
    min-height: 116px;
    padding: 14px;
    background: #ffffff;
  }

  .intent-panel {
    grid-column: span 4;
    min-height: 116px;
    padding: 14px;
  }

  .reply-toolbar,
  .reply-list {
    grid-column: 1 / -1;
  }

  .reply-list {
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 12px;
  }

  .reply-card {
    min-height: 248px;
    border-radius: 7px;
  }

  .reply-card:hover {
    transform: translateY(-1px);
    box-shadow: 0 8px 20px rgb(15 23 42 / 8%);
  }
}
</style>

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
          {{ item.nickname }} · {{ item.category || item.intention_level }} · {{ item.intention_score }}分
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
  gap: 12px;
  padding: 12px;
}

.customer-panel,
.import-panel,
.signal-grid div,
.next-action,
.intent-panel,
.intent-result,
.reply-card,
.empty-card {
  border: 1px solid var(--line);
  border-radius: 8px;
  background: var(--surface);
  box-shadow: var(--shadow-soft);
}

.customer-panel,
.import-panel,
.intent-panel {
  display: grid;
  gap: 10px;
  padding: 12px;
}

.customer-panel {
  background: linear-gradient(135deg, var(--accent-soft), white 62%);
}

.panel-head {
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
  font-size: 12px;
  font-weight: 800;
}

.panel-head strong {
  color: var(--ink);
  font-size: 15px;
}

.level {
  min-width: 30px;
  padding: 5px 8px;
  border-radius: 8px;
  color: var(--brand-strong) !important;
  background: var(--brand-soft);
  text-align: center;
  font-weight: 900 !important;
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

.new-customer {
  display: grid;
  grid-template-columns: 1fr 72px;
  gap: 8px;
}

.panel-head button,
.new-customer button {
  height: 34px;
  border: 0;
  border-radius: 8px;
  color: white;
  background: var(--brand);
  font-weight: 900;
}

.image-upload {
  display: grid;
  place-items: center;
  min-height: 36px;
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

.signal-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
}

.signal-grid div,
.next-action {
  padding: 12px;
}

.signal-grid strong {
  display: block;
  margin-top: 6px;
  color: var(--ink);
  font-size: 14px;
  line-height: 1.4;
}

.next-action {
  border-color: oklch(0.82 0.045 175);
  background: linear-gradient(180deg, var(--brand-soft), white);
}

.intent-panel {
  background: linear-gradient(180deg, white, var(--surface-soft));
}

.intent-result {
  display: grid;
  gap: 9px;
  padding: 11px;
  background: white;
}

.intent-result > span {
  width: fit-content;
  padding: 3px 7px;
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
}

.reply-toolbar strong {
  color: var(--ink);
  font-size: 15px;
}

.reply-toolbar button {
  min-width: 86px;
}

.reply-list {
  display: grid;
  gap: 10px;
}

.reply-card {
  position: relative;
  width: 100%;
  padding: 13px 13px 30px;
  overflow: hidden;
  text-align: left;
}

.reply-card:active {
  transform: translateY(1px);
  border-color: var(--brand);
}

.reply-card > span {
  width: fit-content;
  margin-bottom: 8px;
  padding: 3px 7px;
  border-radius: 999px;
  color: var(--brand-strong);
  background: var(--brand-soft);
}

.reply-reason {
  margin-top: 10px;
  padding: 9px 10px;
  border-radius: 8px;
  background: var(--surface-soft);
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
  padding: 16px;
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
</style>

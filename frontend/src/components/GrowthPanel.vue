<script setup lang="ts">
import { ref } from 'vue'
import { showToast } from 'vant'
import type { IpContentRecord } from '../stores/sidebar'
import MarkdownView from './MarkdownView.vue'

defineProps<{
  ipContents: IpContentRecord[]
  dailyIpAdvice: string
}>()

const emit = defineEmits<{
  generateIp: [theme: string, channel: 'moments' | 'douyin']
  refreshDailyIp: []
}>()

const ipTheme = ref('')
const channel = ref<'moments' | 'douyin'>('moments')

function submitIp() {
  if (!ipTheme.value.trim()) {
    showToast(channel.value === 'douyin' ? '请填写短视频主题' : '请填写朋友圈内容主题')
    return
  }
  emit('generateIp', ipTheme.value.trim(), channel.value)
  ipTheme.value = ''
}
</script>

<template>
  <section class="ip-builder">
    <div class="hero">
      <span>个人 IP 打造</span>
      <strong>让销售每天都有内容可发</strong>
      <p>围绕行业热点、客户痛点和成交案例，持续建立专业、可信、有温度的人设。</p>
    </div>

    <article v-if="dailyIpAdvice" class="panel daily">
      <div class="panel-head">
        <strong>今日 IP 建议</strong>
        <button type="button" @click="emit('refreshDailyIp')">刷新建议</button>
      </div>
      <MarkdownView :content="dailyIpAdvice" />
    </article>

    <article class="panel">
      <div class="panel-head">
        <strong>内容生成</strong>
        <span>{{ channel === 'douyin' ? '抖音短视频文案' : '朋友圈 / 自媒体' }}</span>
      </div>
      <div class="channel-switch">
        <button :class="{ active: channel === 'moments' }" type="button" @click="channel = 'moments'">朋友圈</button>
        <button :class="{ active: channel === 'douyin' }" type="button" @click="channel = 'douyin'">抖音短视频</button>
      </div>
      <input
        v-model="ipTheme"
        :placeholder="channel === 'douyin' ? '短视频主题：客户为什么总嫌贵、报价前先问哪三件事' : '内容主题：今天行业热点观点、客户常见误区'"
      />
      <button class="primary" type="button" @click="submitIp">
        {{ channel === 'douyin' ? '生成短视频文案' : '生成朋友圈内容' }}
      </button>
    </article>

    <div class="ip-list">
      <article v-for="item in ipContents" :key="item.id" class="ip-card">
        <header>
          <div>
            <span>{{ item.channel === 'douyin' ? '抖音短视频' : '朋友圈' }}</span>
            <strong>{{ item.theme }}</strong>
          </div>
          <div class="card-actions">
            <time>{{ item.created_at.slice(0, 10) }}</time>
            <button type="button" @click="emit('generateIp', item.theme, item.channel === 'douyin' ? 'douyin' : 'moments')">再来一版</button>
          </div>
        </header>
        <MarkdownView :content="item.content" />
      </article>
      <p v-if="!ipContents.length" class="empty">暂无 IP 内容</p>
    </div>
  </section>
</template>

<style scoped>
.ip-builder {
  display: grid;
  gap: 14px;
  padding: 14px;
}

.hero,
.panel,
.ip-card,
.empty {
  border: 1px solid oklch(0.87 0.021 105 / 0.86);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-soft);
}

.hero {
  position: relative;
  overflow: hidden;
  padding: 18px;
  color: var(--ink);
  background:
    radial-gradient(circle at 90% 0%, oklch(0.9 0.09 82 / 0.76), transparent 160px),
    linear-gradient(135deg, oklch(1 0.004 95), oklch(0.92 0.052 171));
}

.hero span {
  color: var(--brand-strong);
  font-size: 11px;
  font-weight: 900;
  letter-spacing: 0.04em;
}

.hero strong {
  display: block;
  margin-top: 5px;
  font-size: 22px;
  letter-spacing: -0.04em;
}

.hero p {
  margin: 7px 0 0;
  color: var(--muted);
  font-size: 13px;
  line-height: 1.55;
}

.panel {
  display: grid;
  gap: 12px;
  padding: 15px;
  background: var(--surface);
}

.daily {
  border-color: oklch(0.82 0.045 175);
  background:
    radial-gradient(circle at 100% 0%, oklch(0.9 0.08 84 / 0.62), transparent 150px),
    linear-gradient(180deg, var(--brand-soft), white 96px);
}

.panel-head,
.ip-card header {
  display: flex;
  justify-content: space-between;
  gap: 10px;
}

.panel-head strong,
.ip-card strong {
  color: var(--ink);
  font-size: 16px;
  letter-spacing: -0.02em;
}

.panel-head span,
.ip-card span,
.ip-card time {
  color: var(--subtle);
  font-size: 12px;
  font-weight: 800;
}

.panel-head button,
.card-actions button {
  min-height: 30px;
  border: 0;
  border-radius: 14px;
  color: white;
  background: linear-gradient(135deg, var(--brand-strong), var(--brand));
  font-size: 12px;
  font-weight: 900;
}

.card-actions {
  display: grid;
  justify-items: end;
  gap: 6px;
  min-width: 82px;
}

.card-actions button {
  padding: 0 9px;
}

.channel-switch {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
}

.channel-switch button {
  min-height: 36px;
  border: 1px solid oklch(0.86 0.021 105);
  border-radius: 14px;
  color: var(--muted);
  background: oklch(1 0.004 95 / 0.8);
  font-weight: 800;
}

.channel-switch .active {
  color: var(--brand-strong);
  border-color: oklch(0.78 0.055 175);
  background: var(--brand-soft);
}

input {
  width: 100%;
  border: 1px solid oklch(0.86 0.021 105);
  border-radius: 14px;
  padding: 11px 12px;
  color: var(--ink);
  background: oklch(1 0.004 95 / 0.78);
  font-size: 13px;
}

.primary {
  height: 39px;
  border: 0;
  border-radius: 14px;
  color: white;
  background:
    radial-gradient(circle at 88% 8%, var(--accent), transparent 44px),
    linear-gradient(135deg, var(--brand-strong), var(--brand));
  font-weight: 900;
}

.ip-list {
  display: grid;
  gap: 10px;
}

.ip-card {
  display: grid;
  gap: 9px;
  padding: 14px;
  background: white;
}

.ip-card header div {
  display: grid;
  gap: 3px;
}

.empty {
  margin: 0;
  padding: 16px;
  color: var(--muted);
  background: var(--surface);
  text-align: center;
}
</style>

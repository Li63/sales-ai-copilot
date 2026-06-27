<script setup lang="ts">
import { computed } from 'vue'
import type { Customer, FollowOverview } from '../stores/sidebar'

const props = defineProps<{
  customers: Customer[]
  overview: FollowOverview | null
}>()

const levels = ['S', 'A', 'B', 'C', 'D'] as const
const levelText = { S: '高意向', A: '重点推进', B: '持续培育', C: '弱意向', D: '沉睡' }

const total = computed(() => props.customers.length)
const levelCounts = computed(() => {
  const counts: Record<string, number> = { S: 0, A: 0, B: 0, C: 0, D: 0 }
  for (const customer of props.customers) {
    const level = customer.category || customer.intention_level || 'C'
    counts[level] = (counts[level] || 0) + 1
  }
  return counts
})
const averageScore = computed(() => {
  if (!props.customers.length) return 0
  const sum = props.customers.reduce((value, customer) => value + (customer.intention_score || 0), 0)
  return Math.round(sum / props.customers.length)
})
const followedToday = computed(() => props.overview?.done.length || 0)
const pendingToday = computed(() => props.overview?.pending.length || 0)
const followRate = computed(() => {
  const base = followedToday.value + pendingToday.value
  return base ? Math.round((followedToday.value / base) * 100) : 0
})
const hotCustomers = computed(() =>
  [...props.customers]
    .sort((a, b) => (b.intention_score || 0) - (a.intention_score || 0))
    .slice(0, 5)
)

function percent(count: number) {
  return total.value ? Math.max(4, Math.round((count / total.value) * 100)) : 0
}
</script>

<template>
  <section class="summary-dashboard">
    <header class="summary-head">
      <div>
        <strong>销售复盘总览</strong>
        <span>看客户结构、跟进完成度和优先推进对象</span>
      </div>
    </header>

    <div class="metric-grid">
      <div>
        <span>客户总数</span>
        <strong>{{ total }}</strong>
      </div>
      <div>
        <span>平均意向分</span>
        <strong>{{ averageScore }}</strong>
      </div>
      <div>
        <span>今日跟进率</span>
        <strong>{{ followRate }}%</strong>
      </div>
    </div>

    <article class="panel">
      <div class="panel-title">
        <strong>客户分层</strong>
        <span>S/A 越多，近期成交机会越集中</span>
      </div>
      <div class="bar-list">
        <div v-for="level in levels" :key="level" class="bar-row">
          <label>{{ level }} · {{ levelText[level] }}</label>
          <div class="bar-track">
            <i :style="{ width: `${percent(levelCounts[level])}%` }"></i>
          </div>
          <em>{{ levelCounts[level] }}</em>
        </div>
      </div>
    </article>

    <article class="panel">
      <div class="panel-title">
        <strong>今日跟进</strong>
        <span>先清待跟进，再处理低意向培育</span>
      </div>
      <div class="follow-ring" :style="{ '--rate': `${followRate}%` }">
        <div>
          <strong>{{ followRate }}%</strong>
          <span>已完成</span>
        </div>
      </div>
      <div class="follow-counts">
        <span>已跟进 {{ followedToday }}</span>
        <span>待跟进 {{ pendingToday }}</span>
      </div>
    </article>

    <article class="panel">
      <div class="panel-title">
        <strong>优先客户</strong>
        <span>按意向分排序，适合今天优先看</span>
      </div>
      <div class="hot-list">
        <div v-for="customer in hotCustomers" :key="customer.external_userid">
          <strong>{{ customer.nickname }}</strong>
          <span>{{ customer.category || customer.intention_level }} · {{ customer.intention_score }}分</span>
        </div>
        <p v-if="!hotCustomers.length">还没有客户数据。</p>
      </div>
    </article>
  </section>
</template>

<style scoped>
.summary-dashboard {
  display: grid;
  gap: 12px;
  padding: 12px;
}

.summary-head,
.panel,
.metric-grid div {
  border: 1px solid var(--line);
  border-radius: 8px;
  background: var(--surface);
  box-shadow: var(--shadow-soft);
}

.summary-head {
  padding: 14px;
  color: white;
  background: linear-gradient(135deg, oklch(0.29 0.055 230), oklch(0.39 0.08 175));
}

.summary-head div,
.panel-title {
  display: grid;
  gap: 3px;
}

.summary-head strong {
  font-size: 17px;
}

.summary-head span {
  color: oklch(0.88 0.035 178);
  font-size: 12px;
}

.metric-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px;
}

.metric-grid div {
  padding: 10px;
}

.metric-grid span,
.panel-title span,
.follow-counts span {
  color: var(--muted);
  font-size: 12px;
  line-height: 1.4;
}

.metric-grid strong {
  display: block;
  margin-top: 4px;
  color: var(--brand-strong);
  font-size: 22px;
}

.panel {
  display: grid;
  gap: 12px;
  padding: 14px;
}

.panel-title strong {
  color: var(--ink);
  font-size: 15px;
}

.bar-list {
  display: grid;
  gap: 10px;
}

.bar-row {
  display: grid;
  grid-template-columns: 72px 1fr 26px;
  align-items: center;
  gap: 8px;
}

.bar-row label {
  color: var(--ink);
  font-size: 12px;
  font-weight: 800;
}

.bar-track {
  height: 10px;
  overflow: hidden;
  border-radius: 999px;
  background: var(--surface-soft);
}

.bar-track i {
  display: block;
  height: 100%;
  border-radius: inherit;
  background: var(--brand);
}

.bar-row em {
  color: var(--muted);
  font-size: 12px;
  font-style: normal;
  text-align: right;
}

.follow-ring {
  display: grid;
  place-items: center;
  width: 128px;
  height: 128px;
  margin: 0 auto;
  border-radius: 999px;
  background: conic-gradient(var(--brand) var(--rate), var(--surface-soft) 0);
}

.follow-ring div {
  display: grid;
  place-items: center;
  width: 92px;
  height: 92px;
  border-radius: 999px;
  background: white;
}

.follow-ring strong {
  color: var(--brand-strong);
  font-size: 24px;
}

.follow-ring span {
  color: var(--muted);
  font-size: 12px;
}

.follow-counts {
  display: flex;
  justify-content: center;
  gap: 12px;
}

.hot-list {
  display: grid;
  gap: 8px;
}

.hot-list div {
  display: flex;
  justify-content: space-between;
  gap: 10px;
  padding: 9px 10px;
  border-radius: 8px;
  background: var(--surface-soft);
}

.hot-list strong {
  min-width: 0;
  overflow: hidden;
  color: var(--ink);
  font-size: 13px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.hot-list span,
.hot-list p {
  margin: 0;
  color: var(--muted);
  font-size: 12px;
}
</style>

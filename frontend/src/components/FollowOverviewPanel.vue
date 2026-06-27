<script setup lang="ts">
import type { FollowOverview } from '../stores/sidebar'

defineProps<{
  overview: FollowOverview | null
}>()

const levelLabel: Record<string, string> = {
  S: '高意向',
  A: '重点推进',
  B: '持续培育',
  C: '低频维护',
  D: '沉睡唤醒'
}
</script>

<template>
  <section class="follow-overview">
    <header>
      <div>
        <strong>今日跟进总览</strong>
        <span>看清谁已跟、谁没跟，以及下一次沟通要留什么钩子</span>
      </div>
      <em>{{ overview?.date || '今天' }}</em>
    </header>

    <div class="stats">
      <div>
        <span>已跟进</span>
        <strong>{{ overview?.done.length || 0 }}</strong>
      </div>
      <div>
        <span>待跟进</span>
        <strong>{{ overview?.pending.length || 0 }}</strong>
      </div>
    </div>

    <div class="block">
      <h3>待跟进客户</h3>
      <article v-for="item in overview?.pending || []" :key="item.customer.external_userid">
        <div class="row">
          <strong>{{ item.customer.nickname }}</strong>
          <span>{{ item.customer.category }} · {{ levelLabel[item.customer.category] || '需判断' }}</span>
        </div>
        <p>{{ item.next_suggestion }}</p>
        <p class="hook">留钩子：{{ item.hook_suggestion }}</p>
      </article>
      <p v-if="!overview?.pending.length" class="empty">今天没有待跟进客户。</p>
    </div>

    <div class="block">
      <h3>已跟进客户</h3>
      <article v-for="item in overview?.done || []" :key="item.customer.external_userid">
        <div class="row">
          <strong>{{ item.customer.nickname }}</strong>
          <span>已完成</span>
        </div>
        <p>{{ item.next_suggestion }}</p>
        <p class="hook">下次钩子：{{ item.hook_suggestion }}</p>
      </article>
      <p v-if="!overview?.done.length" class="empty">完成跟进后，这里会给出下一次建议。</p>
    </div>
  </section>
</template>

<style scoped>
.follow-overview {
  display: grid;
  gap: 12px;
  padding: 14px;
  border: 1px solid var(--line);
  border-radius: 8px;
  background: var(--surface);
  box-shadow: var(--shadow-soft);
}

header,
.row,
.stats {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

header div {
  display: grid;
  gap: 3px;
}

header strong {
  color: var(--ink);
  font-size: 15px;
}

header span,
header em {
  color: var(--muted);
  font-size: 12px;
  font-style: normal;
  line-height: 1.45;
}

.stats {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
}

.stats div {
  padding: 10px;
  border-radius: 8px;
  background: var(--surface-soft);
}

.stats span {
  color: var(--muted);
  font-size: 12px;
  font-weight: 800;
}

.stats strong {
  display: block;
  margin-top: 4px;
  color: var(--brand-strong);
  font-size: 22px;
}

.block {
  display: grid;
  gap: 8px;
}

h3 {
  margin: 0;
  color: var(--ink);
  font-size: 13px;
}

article {
  padding: 10px;
  border: 1px solid var(--line);
  border-radius: 8px;
  background: var(--surface-raised);
}

.row strong {
  color: var(--ink);
  font-size: 13px;
}

.row span {
  color: var(--subtle);
  font-size: 12px;
}

p {
  margin: 7px 0 0;
  color: var(--muted);
  font-size: 12px;
  line-height: 1.5;
}

.hook {
  color: var(--brand-strong);
}

.empty {
  margin: 0;
  padding: 10px;
  border-radius: 8px;
  color: var(--muted);
  background: var(--surface-soft);
  text-align: center;
}
</style>

<script setup lang="ts">
import { computed, reactive, ref } from 'vue'
import type { Customer } from '../stores/sidebar'

const props = defineProps<{
  groups: Record<string, Customer[]>
}>()

const emit = defineEmits<{
  select: [externalUserId: string]
}>()

const query = ref('')
const expanded = reactive<Record<string, boolean>>({ CLOSED: true, S: true, A: true, B: false, C: false, D: false })

const levels = ['CLOSED', 'S', 'A', 'B', 'C', 'D'] as const
const levelMeta = {
  CLOSED: { title: '已成交客户', desc: '重点沉淀成交节奏和有效话术', tone: 'success' },
  S: { title: 'S 类客户', desc: '强意向，优先推进成交', tone: 'hot' },
  A: { title: 'A 类客户', desc: '中高意向，持续跟进', tone: 'warm' },
  B: { title: 'B 类客户', desc: '有兴趣但节奏不急', tone: 'steady' },
  C: { title: 'C 类客户', desc: '弱意向，需要培育', tone: 'cool' },
  D: { title: 'D 类客户', desc: '沉睡或低价值线索', tone: 'quiet' }
}

const totalCount = computed(() => Object.values(props.groups).flat().length)
const filteredGroups = computed(() => {
  const keyword = query.value.trim().toLowerCase()
  const next: Record<string, Customer[]> = {}
  for (const level of levels) {
    const customers = props.groups[level] || []
    next[level] = keyword
      ? customers.filter((customer) => {
          const haystack = [
            customer.nickname,
            customer.core_demand,
            customer.objection,
            customer.remark,
            ...customer.tags.map((tag) => tag.tag_name)
          ]
            .filter(Boolean)
            .join(' ')
            .toLowerCase()
          return haystack.includes(keyword)
        })
      : customers
  }
  return next
})

function toggle(level: string) {
  expanded[level] = !expanded[level]
}
</script>

<template>
  <section class="library">
    <header class="library-head">
      <div>
        <strong>客户库</strong>
        <span>按意向等级管理客户，搜索后可快速进入话术分析</span>
      </div>
      <em>{{ totalCount }} 位</em>
    </header>

    <div class="search-box">
      <input v-model="query" placeholder="搜索客户名称、需求、异议或标签" />
      <button v-if="query" type="button" @click="query = ''">清空</button>
    </div>

    <div v-for="level in levels" :key="level" class="level-section">
      <button class="level-head" type="button" @click="toggle(level)">
        <div>
          <strong>{{ levelMeta[level].title }}</strong>
          <span>{{ levelMeta[level].desc }}</span>
        </div>
        <em>{{ filteredGroups[level]?.length || 0 }}</em>
      </button>

      <div v-show="expanded[level]" class="customer-list">
        <button
          v-for="customer in filteredGroups[level] || []"
          :key="customer.external_userid"
          class="customer-card"
          type="button"
          @click="emit('select', customer.external_userid)"
        >
          <div class="customer-main">
            <strong>{{ customer.nickname }}</strong>
            <span>{{ customer.lifecycle_status === 'closed' ? '已成交' : `${customer.intention_score}分` }}</span>
          </div>
          <p>{{ customer.core_demand || '暂无核心诉求' }}</p>
          <div v-if="customer.lifecycle_status === 'closed'" class="closed-note">
            成交时间：{{ customer.closed_at ? customer.closed_at.slice(0, 10) : '已记录' }}
          </div>
          <div class="customer-tags">
            <span v-for="tag in customer.tags.slice(0, 3)" :key="`${customer.id}-${tag.tag_name}`">{{ tag.tag_name }}</span>
            <em v-if="!customer.tags.length">暂无标签</em>
          </div>
          <div v-if="customer.recent_follow_records?.length" class="follow-mini">
            {{ customer.recent_follow_records[0].content }}
          </div>
        </button>

        <p v-if="!filteredGroups[level]?.length" class="empty">暂无匹配客户</p>
      </div>
    </div>
  </section>
</template>

<style scoped>
.library {
  display: grid;
  gap: 12px;
  padding: 12px;
}

.library-head,
.level-section,
.search-box {
  border: 1px solid var(--line);
  border-radius: 8px;
  background: var(--surface);
  box-shadow: var(--shadow-soft);
}

.library-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px;
  color: white;
  background: linear-gradient(135deg, oklch(0.3 0.055 230), oklch(0.38 0.075 175));
}

.library-head div {
  display: grid;
  gap: 3px;
}

.library-head strong {
  font-size: 17px;
}

.library-head span {
  color: oklch(0.87 0.04 178);
  font-size: 12px;
  line-height: 1.45;
}

.library-head em {
  font-style: normal;
  font-size: 12px;
  font-weight: 900;
}

.search-box {
  display: grid;
  grid-template-columns: 1fr auto;
  gap: 8px;
  padding: 10px;
}

.search-box input {
  width: 100%;
  border: 1px solid var(--line);
  border-radius: 8px;
  padding: 10px;
  color: var(--ink);
  background: var(--surface-raised);
  font-size: 13px;
}

.search-box button {
  border: 0;
  border-radius: 8px;
  padding: 0 10px;
  color: var(--brand-strong);
  background: var(--brand-soft);
  font-size: 12px;
  font-weight: 900;
}

.level-section {
  overflow: hidden;
}

.level-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  gap: 10px;
  padding: 12px 14px;
  border: 0;
  border-bottom: 1px solid var(--line);
  background: var(--surface-soft);
  text-align: left;
}

.level-head div {
  display: grid;
  gap: 3px;
}

.level-head strong {
  color: var(--ink);
  font-size: 15px;
}

.level-head span {
  color: var(--muted);
  font-size: 12px;
}

.level-head em {
  display: grid;
  place-items: center;
  min-width: 28px;
  height: 28px;
  border-radius: 8px;
  color: var(--brand-strong);
  background: var(--brand-soft);
  font-style: normal;
  font-weight: 900;
}

.customer-list {
  display: grid;
}

.customer-card {
  display: grid;
  gap: 8px;
  width: 100%;
  padding: 12px 14px;
  border: 0;
  border-bottom: 1px solid var(--line);
  background: white;
  text-align: left;
}

.customer-card:last-child {
  border-bottom: 0;
}

.customer-card:active {
  background: var(--brand-soft);
}

.customer-main {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.customer-main strong {
  min-width: 0;
  overflow: hidden;
  color: var(--ink);
  font-size: 14px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.customer-main span {
  color: var(--brand-strong);
  font-size: 12px;
  font-weight: 900;
}

.customer-card p {
  margin: 0;
  color: var(--muted);
  font-size: 13px;
  line-height: 1.45;
}

.customer-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.closed-note {
  width: fit-content;
  padding: 5px 8px;
  border-radius: 8px;
  color: oklch(0.38 0.1 150);
  background: oklch(0.94 0.055 150);
  font-size: 12px;
  font-weight: 900;
}

.customer-tags span {
  padding: 3px 7px;
  border-radius: 999px;
  color: var(--brand-strong);
  background: var(--brand-soft);
  font-size: 11px;
  font-weight: 800;
}

.customer-tags em,
.empty {
  color: var(--subtle);
  font-style: normal;
  font-size: 12px;
}

.follow-mini {
  padding: 8px 10px;
  border-radius: 8px;
  color: var(--ink);
  background: var(--surface-soft);
  font-size: 12px;
  line-height: 1.45;
}

.empty {
  margin: 0;
  padding: 14px;
  text-align: center;
}
</style>

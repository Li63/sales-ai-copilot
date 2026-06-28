<script setup lang="ts">
import type { Customer, UserProfile } from '../stores/sidebar'

defineProps<{
  customer: Customer | null
  user?: UserProfile | null
}>()

const levelClass = (level?: string) => `level level-${level || 'C'}`
</script>

<template>
  <header class="customer-header">
    <div class="identity-row">
      <div class="avatar">
        <img v-if="customer?.avatar" :src="customer.avatar" alt="" />
        <span v-else>{{ (customer?.nickname || '客').slice(0, 1) }}</span>
      </div>
      <div class="identity">
        <div class="name-row">
          <strong>{{ customer?.nickname || '当前客户' }}</strong>
          <span v-if="customer?.lifecycle_status === 'closed'" class="closed-badge">已成交</span>
          <span :class="levelClass(customer?.category || customer?.intention_level)">
            {{ customer?.category || customer?.intention_level || 'C' }}
          </span>
        </div>
        <p>{{ customer?.remark || customer?.external_userid || '导入聊天记录后建设客户全景' }}</p>
      </div>
    </div>

    <div class="meta-row">
      <span>{{ user?.industry || '行业待完善' }}</span>
      <span>{{ customer?.last_chat_time ? customer.last_chat_time.slice(0, 10) : '等待沟通' }}</span>
    </div>
  </header>
</template>

<style scoped>
.customer-header {
  display: grid;
  gap: 12px;
  padding: 14px;
  background: var(--surface);
  border-bottom: 1px solid var(--line);
}

.identity-row {
  display: flex;
  gap: 12px;
  align-items: center;
}

.avatar {
  display: grid;
  place-items: center;
  width: 46px;
  height: 46px;
  flex: 0 0 auto;
  border-radius: 8px;
  color: white;
  background:
    linear-gradient(135deg, var(--brand), var(--accent));
  font-weight: 900;
  box-shadow: 0 8px 16px oklch(0.34 0.09 190 / 0.16);
}

.avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  border-radius: 8px;
}

.identity {
  min-width: 0;
}

.name-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.name-row strong {
  min-width: 0;
  overflow: hidden;
  color: var(--ink);
  font-size: 17px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.identity p {
  margin: 5px 0 0;
  color: var(--muted);
  font-size: 12px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.meta-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
}

.meta-row span {
  min-width: 0;
  padding: 7px 9px;
  border: 1px solid var(--line);
  border-radius: 8px;
  color: var(--muted);
  background: var(--surface-soft);
  font-size: 12px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.level {
  min-width: 26px;
  padding: 3px 7px;
  border-radius: 6px;
  text-align: center;
  font-size: 12px;
  font-weight: 900;
}

.closed-badge {
  flex: 0 0 auto;
  padding: 3px 7px;
  border-radius: 6px;
  color: oklch(0.38 0.1 150);
  background: oklch(0.94 0.055 150);
  font-size: 12px;
  font-weight: 900;
}

.level-S { color: oklch(0.43 0.16 25); background: oklch(0.93 0.055 35); }
.level-A { color: oklch(0.45 0.11 70); background: oklch(0.94 0.065 85); }
.level-B { color: oklch(0.34 0.11 160); background: oklch(0.93 0.045 160); }
.level-C { color: oklch(0.42 0.025 245); background: oklch(0.92 0.012 245); }
.level-D { color: oklch(0.42 0.04 25); background: oklch(0.92 0.025 25); }
</style>

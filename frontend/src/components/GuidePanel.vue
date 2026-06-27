<script setup lang="ts">
import { ref, watch } from 'vue'
import { showToast } from 'vant'
import type { UserProfile } from '../stores/sidebar'
import MarkdownView from './MarkdownView.vue'

const props = defineProps<{
  user: UserProfile | null
}>()

const emit = defineEmits<{
  save: [industry: string, customerGroup: string]
}>()

const industry = ref(props.user?.industry || '')
const customerGroup = ref(props.user?.customer_group || '')

watch(
  () => props.user,
  (user) => {
    industry.value = user?.industry || ''
    customerGroup.value = user?.customer_group || ''
  }
)

function submit() {
  if (!industry.value.trim() || !customerGroup.value.trim()) {
    showToast('请填写行业和目标客户')
    return
  }
  emit('save', industry.value.trim(), customerGroup.value.trim())
}
</script>

<template>
  <section class="guide-panel">
    <div class="form">
      <div class="section-title">
        <span>{{ user?.sales_guide ? '个人策略' : '初始化' }}</span>
        <h2>{{ user?.sales_guide ? '我的销售指南' : '生成你的销售指南' }}</h2>
      </div>

      <p class="intro">
        AI 会先理解你的行业、客户群体、常见异议和成交路径，再用这份指南指导后续聊天分析。
      </p>

      <label>
        <span>你的行业</span>
        <input v-model="industry" placeholder="例如：企业软件、招商加盟、装修、教育培训" />
      </label>

      <label>
        <span>面向的客户群体</span>
        <textarea
          v-model="customerGroup"
          rows="4"
          placeholder="例如：中小企业老板、门店加盟商、宝妈家庭、制造业采购负责人"
        ></textarea>
      </label>

      <button type="button" @click="submit">
        {{ user?.sales_guide ? '重新生成指南' : '生成指南' }}
      </button>
    </div>

    <article v-if="user?.sales_guide" class="guide">
      <header>
        <span>{{ user.industry || '行业' }}</span>
        <strong>长期可查看</strong>
      </header>
      <MarkdownView :content="user.sales_guide" />
    </article>
  </section>
</template>

<style scoped>
.guide-panel {
  display: grid;
  gap: 12px;
}

.form,
.guide {
  padding: 14px;
  border: 1px solid var(--line);
  border-radius: 8px;
  background: var(--surface);
  box-shadow: var(--shadow-soft);
}

.section-title {
  display: grid;
  gap: 3px;
  margin-bottom: 8px;
}

.section-title span,
.guide header span {
  color: var(--brand-strong);
  font-size: 11px;
  font-weight: 900;
}

h2 {
  margin: 0;
  color: var(--ink);
  font-size: 18px;
  line-height: 1.25;
}

.intro {
  margin: 0 0 14px;
  color: var(--muted);
  font-size: 13px;
  line-height: 1.55;
}

label {
  display: grid;
  gap: 6px;
  margin-bottom: 12px;
}

label span {
  color: var(--muted);
  font-size: 12px;
  font-weight: 700;
}

input,
textarea {
  width: 100%;
  border: 1px solid var(--line);
  border-radius: 8px;
  padding: 10px 11px;
  color: var(--ink);
  background: var(--surface-raised);
  line-height: 1.5;
}

textarea {
  resize: vertical;
}

button {
  width: 100%;
  height: 40px;
  border: 0;
  border-radius: 8px;
  color: white;
  background: var(--brand);
  font-weight: 800;
}

.guide {
  border-color: oklch(0.86 0.035 175);
  background:
    linear-gradient(180deg, var(--brand-soft), white 92px);
}

.guide header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 10px;
}

.guide header strong {
  color: var(--muted);
  font-size: 12px;
}
</style>

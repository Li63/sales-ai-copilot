<script setup lang="ts">
import { ref } from 'vue'
import MarkdownView from './MarkdownView.vue'

defineProps<{
  content: string
}>()

const open = ref(false)
</script>

<template>
  <section class="software-guide">
    <button class="fold-head" type="button" @click="open = !open">
      <span>
        <strong>软件使用指南</strong>
        <em>一套完整 SOP：从建客户到复盘，让销售每天照着做</em>
      </span>
      <b>{{ open ? '收起' : '展开' }}</b>
    </button>
    <div v-show="open" class="fold-body">
      <MarkdownView :content="content || '指南加载中...'" />
    </div>
  </section>
</template>

<style scoped>
.software-guide {
  display: grid;
  gap: 10px;
  padding: 14px;
  border: 1px solid var(--line);
  border-radius: 8px;
  background: var(--surface);
  box-shadow: var(--shadow-soft);
}

.fold-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  border: 0;
  padding: 0;
  color: inherit;
  background: transparent;
  text-align: left;
}

.fold-head span {
  display: grid;
  gap: 3px;
  min-width: 0;
}

.fold-head strong {
  color: var(--ink);
  font-size: 15px;
}

.fold-head em {
  color: var(--muted);
  font-size: 12px;
  font-style: normal;
  line-height: 1.45;
}

.fold-head b {
  flex: 0 0 auto;
  min-width: 44px;
  padding: 6px 9px;
  border-radius: 8px;
  color: var(--brand-strong);
  background: var(--brand-soft);
  font-size: 12px;
  text-align: center;
}

.fold-body {
  padding-top: 12px;
  border-top: 1px solid var(--line);
}
</style>

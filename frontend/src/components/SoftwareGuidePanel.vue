<script setup lang="ts">
import MarkdownView from './MarkdownView.vue'

defineProps<{
  content: string
}>()
</script>

<template>
  <section class="software-guide">
    <header>
      <strong>软件使用指南</strong>
      <span>一套完整 SOP：从建客户到复盘，让销售每天照着做</span>
    </header>
    <MarkdownView :content="content || '指南加载中...'" />
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

header {
  display: grid;
  gap: 3px;
}

header strong {
  color: var(--ink);
  font-size: 15px;
}

header span {
  color: var(--muted);
  font-size: 12px;
  line-height: 1.45;
}
</style>

<script setup lang="ts">
import { computed } from 'vue'
import { showToast } from 'vant'
import { copyPlainText } from '../utils/clipboard'

const props = withDefaults(defineProps<{
  content: string
  copyable?: boolean
}>(), {
  copyable: true,
})

async function copyContent() {
  if (!props.content?.trim()) return
  const copied = await copyPlainText(props.content)
  showToast(copied ? '\u5df2\u590d\u5236' : '\u590d\u5236\u5931\u8d25\uff0c\u8bf7\u957f\u6309\u6587\u5b57\u590d\u5236')
}

function escapeHtml(value: string) {
  return value
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;')
}

function inlineMarkdown(value: string) {
  return escapeHtml(value).replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
}

const html = computed(() => {
  const lines = props.content.split(/\r?\n/)
  const output: string[] = []
  let listOpen = false

  function closeList() {
    if (listOpen) {
      output.push('</ul>')
      listOpen = false
    }
  }

  for (const raw of lines) {
    const line = raw.trim()
    if (!line) {
      closeList()
      continue
    }
    if (line.startsWith('### ')) {
      closeList()
      output.push(`<h3>${inlineMarkdown(line.slice(4))}</h3>`)
      continue
    }
    if (line.startsWith('## ')) {
      closeList()
      output.push(`<h2>${inlineMarkdown(line.slice(3))}</h2>`)
      continue
    }
    if (line.startsWith('# ')) {
      closeList()
      output.push(`<h1>${inlineMarkdown(line.slice(2))}</h1>`)
      continue
    }
    if (line.startsWith('> ')) {
      closeList()
      output.push(`<blockquote>${inlineMarkdown(line.slice(2))}</blockquote>`)
      continue
    }
    if (/^[-*]\s+/.test(line) || /^\d+\.\s+/.test(line)) {
      if (!listOpen) {
        output.push('<ul>')
        listOpen = true
      }
      output.push(`<li>${inlineMarkdown(line.replace(/^[-*]\s+/, '').replace(/^\d+\.\s+/, ''))}</li>`)
      continue
    }
    closeList()
    output.push(`<p>${inlineMarkdown(line)}</p>`)
  }
  closeList()
  return output.join('')
})
</script>

<template>
  <div class="markdown-wrap">
    <div v-if="copyable && content" class="markdown-actions">
      <button class="copy" type="button" @click.stop="copyContent">{{ '\u590d\u5236' }}</button>
    </div>
    <div class="markdown-view" v-html="html"></div>
  </div>
</template>

<style scoped>
.markdown-wrap {
  display: grid;
  gap: 7px;
}

.markdown-actions {
  display: flex;
  justify-content: flex-end;
}

.copy {
  min-width: 44px;
  min-height: 28px;
  padding: 0 10px;
  border: 1px solid var(--line);
  border-radius: 8px;
  color: var(--brand-strong);
  background: var(--surface);
  font-size: 12px;
  font-weight: 900;
}

.markdown-view {
  color: var(--ink);
  font-size: 13px;
  line-height: 1.72;
  word-break: break-word;
}

.markdown-view :deep(h1),
.markdown-view :deep(h2),
.markdown-view :deep(h3) {
  margin: 14px 0 8px;
  color: var(--ink);
  line-height: 1.3;
  text-wrap: pretty;
}

.markdown-view :deep(h1) {
  margin-top: 0;
  font-size: 19px;
}

.markdown-view :deep(h2) {
  font-size: 16px;
}

.markdown-view :deep(h3) {
  font-size: 14px;
}

.markdown-view :deep(p) {
  margin: 7px 0;
}

.markdown-view :deep(strong) {
  color: var(--brand-strong);
  font-weight: 900;
}

.markdown-view :deep(ul) {
  display: grid;
  gap: 6px;
  margin: 8px 0 10px;
  padding: 0;
  list-style: none;
}

.markdown-view :deep(li) {
  position: relative;
  padding-left: 16px;
}

.markdown-view :deep(li::before) {
  position: absolute;
  top: 0.72em;
  left: 2px;
  width: 5px;
  height: 5px;
  border-radius: 50%;
  background: var(--brand);
  content: "";
}

.markdown-view :deep(blockquote) {
  margin: 10px 0;
  padding: 10px 12px;
  border: 1px solid oklch(0.84 0.035 175);
  border-radius: 8px;
  color: var(--brand-strong);
  background: var(--brand-soft);
}
</style>

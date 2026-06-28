<script setup lang="ts">
import { ref } from 'vue'
import { showToast } from 'vant'
import type { CompanyMaterial } from '../stores/sidebar'
import { useSidebarStore } from '../stores/sidebar'

defineProps<{
  materials: CompanyMaterial[]
}>()

const emit = defineEmits<{
  add: [payload: { title: string; content: string; source_type: string }]
}>()

const title = ref('')
const content = ref('')
const mode = ref<'full_replace' | 'delta_update'>('full_replace')
const store = useSidebarStore()
const recognizing = ref(false)

async function appendFileNotes(files: FileList | null) {
  if (!files?.length) return
  recognizing.value = true
  try {
    const text = await store.extractFiles('company', files)
    content.value = [content.value.trim(), text.trim()].filter(Boolean).join('\n\n')
    showToast(`已解析 ${files.length} 个公司资料文件`)
  } catch (error) {
    showToast(error instanceof Error ? error.message : '文件解析失败')
  } finally {
    recognizing.value = false
  }
}

async function importTextFile(files: FileList | null) {
  const file = files?.[0]
  if (!file) return
  if (file.type.startsWith('image/') || ['.pdf', '.doc', '.docx'].some((suffix) => file.name.toLowerCase().endsWith(suffix))) {
    await appendFileNotes(files)
    return
  }
  const text = await file.text()
  title.value = title.value || file.name.replace(/\.[^.]+$/, '')
  content.value = [content.value.trim(), text.trim()].filter(Boolean).join('\n\n')
}

function submit() {
  const nextTitle = title.value.trim() || (mode.value === 'full_replace' ? '公司完整资料' : '公司资料变更')
  const nextContent = content.value.trim()
  if (!nextContent) {
    showToast(mode.value === 'full_replace' ? '请上传或粘贴完整公司资料' : '请填写本次变化内容')
    return
  }
  emit('add', { title: nextTitle, content: nextContent, source_type: mode.value })
  title.value = ''
  content.value = ''
}
</script>

<template>
  <section class="company-material">
    <header class="section-head">
      <div>
        <strong>公司资料库</strong>
        <span>让回复更贴近你的产品、报价、案例和服务边界</span>
      </div>
    </header>

    <div class="mode-switch">
      <button :class="{ active: mode === 'full_replace' }" type="button" @click="mode = 'full_replace'">全量更新</button>
      <button :class="{ active: mode === 'delta_update' }" type="button" @click="mode = 'delta_update'">只写变化</button>
    </div>
    <p class="hint">
      {{
        mode === 'full_replace'
          ? '上传新的公司完整资料后，AI 会以这份最新资料为准。请提醒销售：每次选全量更新，都要把产品、价格、案例、售后等完整资料重新上传。'
          : '只填写变化内容即可，例如“某某产品价格由 100 变成 120”。AI 会在最新完整资料基础上，用这条变化覆盖旧信息。'
      }}
    </p>

    <input
      v-model="title"
      :placeholder="mode === 'full_replace' ? '资料标题：2026 最新公司完整资料' : '变更标题：某某产品价格调整'"
    />
    <textarea
      v-model="content"
      rows="5"
      :placeholder="mode === 'full_replace' ? '粘贴或上传公司完整资料：产品介绍、报价规则、成功案例、售后政策。' : '填写变化：例如某某产品价格由100变成120，某服务新增7天售后，某案例不再使用。'"
    ></textarea>

    <div class="upload-row">
      <label>
        上传 Word/PDF/图片
        <input accept=".doc,.docx,.pdf,image/*,.txt,.md,.csv,.json" multiple type="file" @change="importTextFile(($event.target as HTMLInputElement).files)" />
      </label>
      <label>
        连续解析资料
        <input accept=".doc,.docx,.pdf,image/*" multiple type="file" @change="appendFileNotes(($event.target as HTMLInputElement).files)" />
      </label>
      <button type="button" @click="submit">保存资料</button>
    </div>
    <p v-if="recognizing" class="status">正在解析文件，请稍等...</p>

    <div class="material-list">
      <article v-for="item in materials" :key="item.id">
        <strong>{{ item.title }}</strong>
        <span>{{ item.source_type === 'delta_update' ? '变更记录' : '完整资料' }}</span>
        <p>{{ item.content.slice(0, 96) }}{{ item.content.length > 96 ? '...' : '' }}</p>
      </article>
      <p v-if="!materials.length" class="empty">还没有公司资料。先放入产品、价格、案例，话术会明显更像你们公司。</p>
    </div>
  </section>
</template>

<style scoped>
.company-material {
  display: grid;
  gap: 10px;
  padding: 14px;
  border: 1px solid var(--line);
  border-radius: 8px;
  background: var(--surface);
  box-shadow: var(--shadow-soft);
}

.section-head div {
  display: grid;
  gap: 3px;
}

.section-head strong {
  color: var(--ink);
  font-size: 15px;
}

.section-head span {
  color: var(--muted);
  font-size: 12px;
  line-height: 1.45;
}

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

textarea {
  resize: vertical;
}

.mode-switch {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
}

.mode-switch button {
  min-height: 36px;
  border: 1px solid var(--line);
  border-radius: 8px;
  color: var(--muted);
  background: white;
  font-size: 12px;
  font-weight: 900;
}

.mode-switch .active {
  color: var(--brand-strong);
  border-color: oklch(0.78 0.055 175);
  background: var(--brand-soft);
}

.hint {
  margin: 0;
  padding: 10px;
  border-radius: 8px;
  color: var(--brand-strong);
  background: var(--brand-soft);
  font-size: 12px;
  line-height: 1.55;
}

.upload-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
}

.upload-row label,
.upload-row button {
  min-height: 36px;
  border-radius: 8px;
  font-size: 12px;
  font-weight: 900;
}

.upload-row label {
  display: grid;
  place-items: center;
  border: 1px solid var(--line);
  color: var(--brand-strong);
  background: var(--brand-soft);
}

.upload-row label input {
  display: none;
}

.upload-row button {
  grid-column: 1 / -1;
  border: 0;
  color: white;
  background: var(--brand);
}

.material-list {
  display: grid;
  gap: 8px;
}

.material-list article {
  padding: 10px;
  border: 1px solid var(--line);
  border-radius: 8px;
  background: var(--surface-soft);
}

.material-list strong {
  display: inline;
  color: var(--ink);
  font-size: 13px;
}

.material-list article span {
  display: inline-block;
  margin-left: 6px;
  padding: 2px 6px;
  border-radius: 999px;
  color: var(--brand-strong);
  background: var(--brand-soft);
  font-size: 11px;
  font-weight: 800;
}

.material-list p,
.empty {
  margin: 5px 0 0;
  color: var(--muted);
  font-size: 12px;
  line-height: 1.5;
}

.empty {
  margin: 0;
  padding: 10px;
  text-align: center;
}

.status {
  margin: 0;
  color: var(--brand-strong);
  font-size: 12px;
  font-weight: 800;
}
</style>

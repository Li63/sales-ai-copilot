<script setup lang="ts">
import { ref } from 'vue'
import { showToast } from 'vant'
import type { FollowRecord } from '../stores/sidebar'
import { useSidebarStore } from '../stores/sidebar'

const props = defineProps<{
  records: FollowRecord[]
}>()

const emit = defineEmits<{
  add: [content: string]
}>()

const content = ref('')
const recognizing = ref(false)
const store = useSidebarStore()

async function submit() {
  const value = content.value.trim()
  if (!value) {
    showToast('请输入跟进内容')
    return
  }
  emit('add', value)
  content.value = ''
}

async function appendFollowImages(files: FileList | null) {
  if (!files?.length) return
  recognizing.value = true
  try {
    const text = await store.extractFiles('chat', files)
    content.value = [content.value.trim(), `本次沟通文件解析：\n${text.trim()}`].filter(Boolean).join('\n\n')
    showToast(`已解析 ${files.length} 个跟进文件`)
  } catch (error) {
    showToast(error instanceof Error ? error.message : '文件解析失败')
  } finally {
    recognizing.value = false
  }
}
</script>

<template>
  <section class="follow">
    <div class="composer">
      <div class="composer-head">
        <strong>新增跟进</strong>
        <span>文本 / Word / PDF / 图片</span>
      </div>
      <textarea v-model="content" rows="5" placeholder="记录本次沟通结果、客户顾虑、下次要推进的动作。也可以上传聊天截图、Word 或 PDF，解析后直接保存为跟进记录。"></textarea>
      <label class="image-upload">
        {{ recognizing ? '正在解析文件...' : '上传聊天截图 / Word / PDF 并写入跟进' }}
        <input accept=".doc,.docx,.pdf,image/*" multiple type="file" @change="appendFollowImages(($event.target as HTMLInputElement).files)" />
      </label>
      <button type="button" @click="submit">保存跟进</button>
    </div>

    <div class="timeline">
      <article v-for="record in props.records" :key="record.id">
        <time>{{ record.created_at.slice(0, 10) }}</time>
        <p>{{ record.content }}</p>
      </article>
      <p v-if="!props.records.length" class="empty">暂无跟进记录</p>
    </div>
  </section>
</template>

<style scoped>
.follow {
  display: grid;
  gap: 12px;
  padding: 12px;
}

.composer,
article,
.empty {
  border: 1px solid var(--line);
  border-radius: 8px;
  background: var(--surface);
  box-shadow: var(--shadow-soft);
}

.composer {
  display: grid;
  gap: 10px;
  padding: 14px;
}

.composer-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.composer-head strong {
  color: var(--ink);
  font-size: 15px;
}

.composer-head span {
  color: var(--subtle);
  font-size: 12px;
  font-weight: 800;
}

textarea {
  width: 100%;
  resize: vertical;
  border: 1px solid var(--line);
  border-radius: 8px;
  padding: 10px;
  color: var(--ink);
  background: var(--surface-raised);
  line-height: 1.55;
}

button {
  width: 100%;
  height: 40px;
  border: 0;
  border-radius: 8px;
  color: white;
  background: var(--brand);
  font-weight: 900;
}

.image-upload {
  display: grid;
  place-items: center;
  min-height: 38px;
  border: 1px dashed oklch(0.76 0.055 175);
  border-radius: 8px;
  color: var(--brand-strong);
  background: var(--brand-soft);
  font-size: 12px;
  font-weight: 900;
}

.image-upload input {
  display: none;
}

.timeline {
  display: grid;
  gap: 10px;
  padding-left: 8px;
}

article {
  position: relative;
  padding: 12px 12px 12px 16px;
}

article::before {
  position: absolute;
  top: 15px;
  left: -8px;
  width: 9px;
  height: 9px;
  border: 2px solid var(--bg);
  border-radius: 50%;
  background: var(--brand);
  content: "";
}

time {
  color: var(--muted);
  font-size: 12px;
  font-weight: 800;
}

article p,
.empty {
  margin: 6px 0 0;
  color: var(--ink);
  font-size: 14px;
  line-height: 1.55;
}

.empty {
  margin: 0;
  padding: 16px;
  color: var(--muted);
  text-align: center;
}
</style>

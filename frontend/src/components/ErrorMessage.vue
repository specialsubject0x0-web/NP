<!-- 錯誤訊息：顯示後端回傳的 message。role="alert" 讓螢幕閱讀器會念出來。 -->
<script setup lang="ts">
defineProps<{ message: string | null }>()
</script>

<template>
  <p v-if="message" class="error" role="alert">{{ message }}</p>
</template>

<style scoped>
.error {
  margin: var(--space-3) 0;
  padding: var(--space-3) var(--space-4);
  border-left: 4px solid var(--color-error);
  background: #fbecee;
  color: var(--color-error);
}
</style>

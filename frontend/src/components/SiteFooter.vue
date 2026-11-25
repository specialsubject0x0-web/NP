<!-- 頁尾：文字來自 content/footer.json（【手動修改區】）。 -->
<script setup lang="ts">
import footer from '@/content/footer.json'
</script>

<template>
  <footer class="footer">
    <div class="inner">
      <p>{{ footer.about }}</p>
      <p>{{ footer.contact }}</p>
      <p class="muted">{{ footer.copyright }}</p>
    </div>
  </footer>
</template>

<style scoped>
.footer {
  border-top: 1px solid var(--color-line);
  font-size: var(--text-sm);
}
.inner {
  max-width: var(--page-width);
  margin: 0 auto;
  padding: var(--space-5) var(--space-4);
}
p {
  margin: 0 0 var(--space-1);
  max-width: 60ch;
}
</style>

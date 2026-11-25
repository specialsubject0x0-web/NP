<!--
  商品圖（佔位圖）：沒有授權的商品照片（假設 A-11），所以用「色塊＋商品名第一個字」做成像招牌或印章的圖。
  顏色來自後端商品資料的 image_color。
  【可修改】想換成真的照片：把下面 <div> 換成 <img :src="..." :alt="name">（記得一定要有 alt）。
-->
<script setup lang="ts">
import { computed } from 'vue'

const props = withDefaults(defineProps<{ name: string; color: string; size?: 'sm' | 'md' | 'lg' }>(), {
  size: 'md',
})

// Array.from 才能正確取出中文字（避免把一個字切成兩半）
const glyph = computed(
  () => Array.from(props.name.replace(/^[\s\d.\-A-Za-z]+/, ''))[0] ?? props.name.charAt(0),
)
</script>

<template>
  <div
    class="image"
    :class="`image--${size}`"
    :style="{ backgroundColor: color }"
    role="img"
    :aria-label="name"
  >
    <span class="glyph" aria-hidden="true">{{ glyph }}</span>
  </div>
</template>

<style scoped>
.image {
  aspect-ratio: 1;
  display: grid;
  place-items: center;
  border-radius: var(--radius);
  overflow: hidden;
  position: relative;
}
/* 內框線，讓色塊有一點印章、招牌的感覺 */
.image::after {
  content: '';
  position: absolute;
  inset: 8%;
  border: 1px solid rgb(255 255 255 / 0.35);
  border-radius: 2px;
}
.glyph {
  font-family: var(--font-display);
  color: #fff;
  font-weight: 700;
  line-height: 1;
}
.image--sm .glyph {
  font-size: 1.6rem;
}
.image--md .glyph {
  font-size: clamp(3rem, 9vw, 5rem);
}
.image--lg .glyph {
  font-size: clamp(6rem, 20vw, 11rem);
}
</style>

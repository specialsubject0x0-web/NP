<!-- 數量選擇：− 數字 ＋。上限 99（R-05），也不會超過 max（庫存）。 -->
<script setup lang="ts">
const props = withDefaults(defineProps<{ modelValue: number; max?: number; label?: string }>(), {
  max: 99,
  label: '數量',
})
const emit = defineEmits<{ 'update:modelValue': [value: number] }>()

function set(value: number): void {
  const limit = Math.min(props.max, 99)
  emit('update:modelValue', Math.max(1, Math.min(limit, Math.floor(value) || 1)))
}
</script>

<template>
  <div class="qty" role="group" :aria-label="label">
    <button type="button" :disabled="modelValue <= 1" aria-label="減少一件" @click="set(modelValue - 1)">
      −
    </button>
    <input
      type="number"
      :value="modelValue"
      min="1"
      :max="Math.min(max, 99)"
      :aria-label="label"
      @change="set(Number(($event.target as HTMLInputElement).value))"
    />
    <button
      type="button"
      :disabled="modelValue >= Math.min(max, 99)"
      aria-label="增加一件"
      @click="set(modelValue + 1)"
    >
      ＋
    </button>
  </div>
</template>

<style scoped>
.qty {
  display: inline-flex;
  border: 1px solid var(--color-line);
  border-radius: var(--radius);
  background: var(--color-surface);
}
button {
  width: 36px;
  border: 0;
  background: none;
  font-size: var(--text-lg);
  cursor: pointer;
  color: var(--color-ink);
}
button:disabled {
  color: var(--color-line);
  cursor: not-allowed;
}
input {
  width: 3.2em;
  border: 0;
  text-align: center;
  font: inherit;
  -moz-appearance: textfield;
}
input::-webkit-inner-spin-button {
  -webkit-appearance: none;
}
</style>

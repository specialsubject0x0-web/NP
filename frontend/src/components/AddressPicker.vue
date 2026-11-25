<!--
  收件地址：列出我的地址讓使用者選一個，也可以新增。選到的地址編號用 v-model 傳回結帳頁。
  電話與郵遞區號格式由後端檢查（前端的 pattern 只是先提醒，不是防線）。
-->
<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { createAddress, fetchAddresses } from '@/api/cart'
import { ApiError } from '@/api/client'
import type { Address, AddressInput } from '@/api/types'
import ErrorMessage from './ErrorMessage.vue'

const selected = defineModel<number | null>({ required: true })
const addresses = ref<Address[]>([])
const adding = ref(false)
const error = ref<string | null>(null)
const form = reactive<AddressInput>({ recipient: '', phone: '', postal_code: '', city: '', line: '' })

async function load(): Promise<void> {
  addresses.value = await fetchAddresses()
  adding.value = addresses.value.length === 0
  if (selected.value === null && addresses.value[0]) selected.value = addresses.value[0].id
}

async function save(): Promise<void> {
  error.value = null
  try {
    const created = await createAddress({ ...form })
    addresses.value.push(created)
    selected.value = created.id
    adding.value = false
    Object.assign(form, { recipient: '', phone: '', postal_code: '', city: '', line: '' })
  } catch (e) {
    error.value =
      e instanceof ApiError && e.code === 'VALIDATION_ERROR'
        ? '請檢查電話（09 開頭 10 碼）與郵遞區號格式'
        : (e as Error).message
  }
}

onMounted(() => void load().catch((e: Error) => (error.value = e.message)))
</script>

<template>
  <fieldset class="picker">
    <legend>收件地址</legend>
    <label v-for="a in addresses" :key="a.id" class="option">
      <input v-model="selected" type="radio" name="address" :value="a.id" />
      <span>
        <strong>{{ a.recipient }}</strong> {{ a.phone }}<br />
        <span class="muted">{{ a.postal_code }} {{ a.city }}{{ a.line }}</span>
      </span>
    </label>

    <button v-if="!adding" type="button" class="btn btn--ghost btn--small" @click="adding = true">
      新增地址
    </button>
    <form v-else class="new" @submit.prevent="save">
      <div class="field">
        <label for="a-name">收件人</label
        ><input id="a-name" v-model="form.recipient" required maxlength="50" />
      </div>
      <div class="field">
        <label for="a-phone">電話</label>
        <input
          id="a-phone"
          v-model="form.phone"
          required
          pattern="0\d{8,9}"
          inputmode="tel"
          placeholder="0912345678"
        />
      </div>
      <div class="field">
        <label for="a-zip">郵遞區號</label>
        <input id="a-zip" v-model="form.postal_code" required pattern="\d{3}(\d{2,3})?" inputmode="numeric" />
      </div>
      <div class="field">
        <label for="a-city">縣市</label><input id="a-city" v-model="form.city" required maxlength="20" />
      </div>
      <div class="field wide">
        <label for="a-line">地址</label><input id="a-line" v-model="form.line" required maxlength="200" />
      </div>
      <div class="wide actions">
        <button type="submit" class="btn btn--small">儲存地址</button>
        <button
          v-if="addresses.length"
          type="button"
          class="btn btn--ghost btn--small"
          @click="adding = false"
        >
          取消
        </button>
      </div>
    </form>
    <ErrorMessage :message="error" />
  </fieldset>
</template>

<style scoped>
.picker {
  border: 0;
  padding: 0;
  margin: 0 0 var(--space-5);
}
legend {
  font-family: var(--font-display);
  font-size: var(--text-lg);
  font-weight: 700;
  margin-bottom: var(--space-3);
}
.option {
  display: flex;
  gap: var(--space-3);
  align-items: flex-start;
  padding: var(--space-3);
  border: 1px solid var(--color-line);
  border-radius: var(--radius);
  margin-bottom: var(--space-2);
  background: var(--color-surface);
  cursor: pointer;
}
.option:has(input:checked) {
  border-color: var(--color-ink);
  background: var(--color-ink-soft);
}
.new {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0 var(--space-3);
}
.wide {
  grid-column: 1 / -1;
}
.actions {
  display: flex;
  gap: var(--space-2);
}
</style>

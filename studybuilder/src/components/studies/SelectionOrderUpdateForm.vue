<template>
  <SimpleFormDialog
    ref="form"
    :title="$t('SelectionOrderUpdateForm.title')"
    @submit="submit"
  >
    <template #body>
      <v-form ref="observer">
        <v-text-field
          v-model="order"
          type="number"
          :label="$t('SelectionOrderUpdateForm.order')"
          clearable
          :rules="[formRules.required]"
        />
      </v-form>
    </template>
  </SimpleFormDialog>
</template>

<script setup lang="js">
import { inject, ref, watch } from 'vue'
import SimpleFormDialog from '@/components/tools/SimpleFormDialog.vue'

const props = defineProps({
  initialValue: {
    type: Number,
    default: 0,
  },
})
const emit = defineEmits(['submit'])
const order = ref(0)
const formRules = inject('formRules')

function submit() {
  emit('submit', order.value)
}

watch(
  () => props.initialValue,
  (value) => {
    order.value = value
  },
  { immediate: true }
)
</script>

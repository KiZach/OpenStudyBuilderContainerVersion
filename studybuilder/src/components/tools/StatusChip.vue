<template>
  <v-chip :color="color" :variant="variant">
    {{ status }}
  </v-chip>
</template>

<script setup>
import { computed } from 'vue'
import statuses from '@/constants/statuses'

const props = defineProps({
  status: {
    type: String,
    default: '',
  },
  outlined: {
    type: Boolean,
    default: true,
  },
})

const color = computed(() => {
  if (
    props.status === statuses.FINAL ||
    props.status === statuses.STUDY_DRAFT
  ) {
    return 'green'
  }
  if (props.status === statuses.RETIRED) {
    return 'orange'
  }
  if (props.status === statuses.RELEASED) {
    return 'info'
  }
  if (props.status === statuses.STUDY_LOCKED) {
    return 'red'
  }
  return 'secondary'
})
const variant = computed(() => {
  return props.outlined ? 'outlined' : 'flat'
})
</script>

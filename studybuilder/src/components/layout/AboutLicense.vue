<template>
  <v-card color="bg-dfltBackground">
    <v-card-actions>
      <v-card-title class="dialog-about-title">
        {{ title }}
      </v-card-title>
      <v-spacer />
      <v-btn class="secondary-btn" color="white" @click="$emit('close')">
        {{ $t('_global.close') }}
      </v-btn>
    </v-card-actions>
    <v-card-text>
      <span v-html="licenseContent" />
    </v-card-text>
  </v-card>
</template>

<script>
import { marked } from 'marked'

export default {
  props: {
    rawMarkdown: {
      type: String,
      default: '',
    },
    title: {
      type: String,
      default: '',
    },
  },
  emits: ['close'],
  computed: {
    licenseContent() {
      return marked.parse(this.rawMarkdown)
    },
  },
}
</script>

<template>
  <div class="mt-6 text-center">
    <h1>{{ message }}</h1>
    <v-btn class="mt-4" color="primary" variant="text" @click="navigateToRoot">
      {{ $t('UnderConstruction.back_home') }}
    </v-btn>
  </div>
</template>

<script>
import { useAppStore } from '@/stores/app'
import { i18n } from '@/plugins/i18n'

export default {
  props: {
    message: {
      type: String,
      default: () => i18n.t('UnderConstruction.title'),
    },
  },
  setup() {
    const appStore = useAppStore()

    return {
      section: appStore.section,
    }
  },
  methods: {
    navigateToRoot() {
      this.section = ''
      this.$router.push('/')
    },
  },
}
</script>

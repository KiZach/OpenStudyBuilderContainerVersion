<template>
  <v-menu
    v-model="open"
    persistent
    :close-on-content-click="false"
    max-height="800px"
    max-width="500px"
    location="bottom"
    no-click-animation
    content-class="right"
  >
    <template #activator="{ props }">
      <div>
        <v-btn
          icon="mdi-help-circle-outline"
          v-bind="props"
          color="primary"
          variant="text"
        />
      </div>
    </template>
    <v-card max-width="500px">
      <v-card-title class="dialog-title d-flex align-center">
        {{ $t('_global.online_help') }}
        <v-spacer />
        <v-btn
          color="secondary"
          icon="mdi-close"
          variant="text"
          @click="open = false"
        />
      </v-card-title>
      <v-divider />
      <v-list>
        <v-list-item>
          <v-expansion-panels>
            <v-expansion-panel v-for="item in items" :key="item.key || item">
              <v-expansion-panel-title>
                {{ getItemLabel(item) }}
              </v-expansion-panel-title>
              <v-expansion-panel-text>
                <div v-html="getItemHelp(item)" />
              </v-expansion-panel-text>
            </v-expansion-panel>
          </v-expansion-panels>
        </v-list-item>
      </v-list>
    </v-card>
  </v-menu>
</template>

<script>
export default {
  components: {},
  props: {
    items: {
      type: Array,
      default: () => [],
    },
  },
  data() {
    return {
      open: false,
    }
  },
  methods: {
    getItemLabel(item) {
      if (typeof item === 'string') {
        return this.$t(item)
      }
      return this.$t(item.key)
    },
    getItemHelp(item) {
      if (typeof item === 'string') {
        return this.$t(`_help.${item}`)
      }
      return this.$t(`_help.${item.key}`, item.context())
    },
  },
}
</script>
<style>
.right {
  right: 10px;
  left: auto !important;
}
</style>

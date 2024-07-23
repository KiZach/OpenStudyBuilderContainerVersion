<template>
  <div>
    {{ pageTitle }}
    <v-btn
      data-cy="help-button"
      icon="mdi-help-circle-outline"
      color="primary"
      variant="text"
      @click="showHelp = true"
    />
    <v-dialog
      v-model="showHelp"
      :width="width"
      persistent
      hide-overlay
      content-class="upperRight"
      class="rounded-0"
      @keydown.esc="showHelp = false"
    >
      <v-card>
        <v-card-title class="d-flex dialog-title align-center">
          {{ title }}
          <v-spacer />
          <v-btn
            color="secondary"
            icon="mdi-close"
            variant="text"
            @click="showHelp = false"
          />
        </v-card-title>
        <v-card-text>
          <slot>
            {{ helpText }}
          </slot>
        </v-card-text>
      </v-card>
    </v-dialog>
  </div>
</template>

<script>
export default {
  props: {
    pageTitle: {
      type: String,
      default: null,
    },
    helpText: {
      type: String,
      default: '',
    },
    title: {
      type: String,
      default: 'Online help',
    },
    width: {
      type: String,
      default: '495px',
    },
  },
  data() {
    return {
      showHelp: false,
    }
  },
}
</script>
<style>
.upperRight {
  position: absolute;
  top: 50px;
  right: 0;
  border-radius: 0px;
}
</style>

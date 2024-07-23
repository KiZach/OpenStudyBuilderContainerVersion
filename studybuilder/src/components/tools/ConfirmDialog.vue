<template>
  <v-dialog
    :model-value="dialog"
    :max-width="options.width"
    :style="{ zIndex: options.zIndex }"
    @keydown.esc="cancel"
  >
    <v-card :class="cardClasses">
      <v-card-text v-if="message" class="pt-2 text-white">
        <v-row no-gutters class="align-center pa-2">
          <v-col cols="2">
            <v-icon
              class="mr-4"
              color="white"
              size="x-large"
              :icon="getIcon()"
            />
          </v-col>
          <v-col cols="10">
            <div class="text-body-1 mt-1" v-html="message" />
          </v-col>
        </v-row>
        <v-divider class="pa-2" />
        <v-row>
          <v-col class="text-center">
            <v-btn
              v-if="!options.noCancel"
              color="white"
              variant="outlined"
              data-cy="cancel-popup"
              class="mr-4 text-white"
              elevation="2"
              @click="cancel"
            >
              {{ options.cancelLabel }}
            </v-btn>
            <slot name="actions">
              <v-btn
                v-if="options.redirect === null"
                color="white"
                variant="outlined"
                data-cy="continue-popup"
                class="text-white"
                elevation="2"
                @click="agree"
              >
                {{ options.agreeLabel }}
              </v-btn>
              <v-btn
                v-else
                color="white"
                data-cy="continue-popup"
                variant="outlined"
                elevation="2"
                @click="agreeAndRedirect"
              >
                {{ options.agreeLabel }}
              </v-btn>
            </slot>
          </v-col>
        </v-row>
      </v-card-text>
    </v-card>
  </v-dialog>
</template>

<script>
export default {
  data() {
    return {
      dialog: false,
      resolve: null,
      reject: null,
      message: null,
      type: null,
      options: {
        type: 'success',
        width: 450,
        zIndex: 3000,
        noCancel: false,
        agreeLabel: this.$t('_global.continue'),
        cancelLabel: this.$t('_global.cancel'),
        cancelIsPrimaryAction: false,
        redirect: null,
      },
    }
  },
  computed: {
    cardClasses() {
      const result = { 'pa-1': true }
      if (this.options.type === 'warning') {
        result['bg-warning'] = true
      } else if (this.options.type === 'info') {
        result['bg-info'] = true
      } else {
        result['bg-green'] = true
      }
      return result
    },
  },
  methods: {
    getIcon() {
      if (this.options.type === 'info') {
        return 'mdi-information-outline'
      }
      if (this.options.type === 'warning') {
        return 'mdi-alert-outline'
      }
      if (this.options.type === 'error') {
        return 'mdi-alert-octagon-outline'
      }
      return 'mdi-check-circle-outline'
    },
    open(message, options) {
      this.dialog = true
      this.message = message
      this.options = Object.assign(this.options, options)
      return new Promise((resolve, reject) => {
        this.resolve = resolve
        this.reject = reject
      })
    },
    agree() {
      this.resolve(true)
      this.dialog = false
    },
    agreeAndRedirect() {
      this.dialog = false
      this.$router.push(this.options.redirect)
    },
    cancel() {
      this.resolve(false)
      this.dialog = false
    },
  },
}
</script>

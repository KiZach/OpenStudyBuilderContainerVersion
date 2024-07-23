<template>
  <v-card color="greyBackground">
    <v-card-title class="d-flex align-center">
      <span class="headline">{{ $t('Settings.title') }}</span>
      <HelpButtonWithPanels :title="$t('_global.help')" :items="helpItems" />
    </v-card-title>
    <v-card-text>
      <div class="bg-white pa-4">
        <v-switch
          v-model="form.darkTheme"
          color="primary"
          :label="$t('Settings.toggle')"
          class="mt-4"
          @change="toggleDarkTheme()"
        />
        <v-select
          v-model="form.rows"
          :label="$t('Settings.rows')"
          :items="rows"
          item-title="name"
          item-value="value"
          clearable
        />
        <v-text-field
          v-model="form.studyNumberLength"
          :label="$t('Settings.study_number_length')"
          type="number"
          clearable
        />
        <v-switch
          v-model="form.multilingual"
          color="primary"
          :label="$t('Settings.multilingual_crf')"
          data-cy="settings-multilingual-crf"
          class="mt-4"
        />
      </div>
    </v-card-text>
    <v-card-actions class="pb-4">
      <v-spacer />
      <v-btn class="secondary-btn" color="white" @click="close">
        {{ $t('_global.cancel') }}
      </v-btn>
      <v-btn
        color="secondary"
        data-cy="save-settings-button"
        :loading="working"
        @click="save"
      >
        {{ $t('_global.save') }}
      </v-btn>
    </v-card-actions>
  </v-card>
</template>

<script>
import { useAppStore } from '@/stores/app'
import HelpButtonWithPanels from '@/components/tools/HelpButtonWithPanels.vue'

export default {
  components: {
    HelpButtonWithPanels,
  },
  emits: ['close'],
  setup() {
    const appStore = useAppStore()
    return {
      appStore,
    }
  },
  data() {
    return {
      darkTheme: localStorage.getItem('userData.darkTheme') || false,
      helpItems: ['Settings.rows', 'Settings.study_number_length'],
      rows: [
        {
          value: 5,
          name: '5',
        },
        {
          value: 10,
          name: '10',
        },
        {
          value: 15,
          name: '15',
        },
        {
          value: 0,
          name: this.$t('_global.all'),
        },
      ],
      title: this.$t('Settings.title'),
      form: {},
      working: false,
    }
  },
  watch: {
    'appStore.userData': {
      handler: function (val) {
        this.form = JSON.parse(JSON.stringify(val))
      },
      immediate: true,
    },
  },
  methods: {
    close() {
      this.$emit('close')
    },
    save() {
      this.working = true
      this.appStore.saveUserData(this.form)
      this.close()
      this.working = false
    },
    toggleDarkTheme() {
      this.$vuetify.theme.dark = !this.$vuetify.theme.dark
    },
  },
}
</script>

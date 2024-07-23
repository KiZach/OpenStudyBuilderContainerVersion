<template>
  <v-card data-cy="form-body" color="dfltBackground">
    <v-card-title class="d-flex align-center">
      <span class="dialog-title">{{ $t('CodelistTermNamesForm.title') }}</span>
      <HelpButtonWithPanels :title="$t('_global.help')" :items="helpItems" />
    </v-card-title>
    <v-card-text class="mt-4">
      <div class="bg-white pa-4">
        <v-form ref="observer">
          <v-text-field
            v-model="form.sponsor_preferred_name"
            data-cy="term-sponsor-preffered-name"
            :label="$t('CodelistTermCreationForm.sponsor_pref_name')"
            :rules="[formRules.required]"
            clearable
            @blur="setSentenceCase"
          />
          <v-text-field
            v-model="form.sponsor_preferred_name_sentence_case"
            data-cy="term-sponsor-sentence-case-name"
            :label="$t('CodelistTermCreationForm.sponsor_sentence_case_name')"
            :rules="[formRules.required]"
            clearable
          />
          <v-text-field
            v-model="form.order"
            data-cy="term-order"
            :label="$t('CodelistTermCreationForm.order')"
            :rules="[formRules.required]"
            clearable
          />
          <v-textarea
            v-model="form.change_description"
            data-cy="change-description"
            :label="$t('HistoryTable.change_description')"
            class="white py-2"
            :rules="[formRules.required]"
            :rows="1"
            auto-grow
          />
        </v-form>
      </div>
    </v-card-text>
    <v-card-actions>
      <v-spacer />
      <v-btn class="secondary-btn" color="white" @click="close">
        {{ $t('_global.cancel') }}
      </v-btn>
      <v-btn
        data-cy="save-button"
        color="secondary"
        :loading="working"
        @click="submit"
      >
        {{ $t('_global.save') }}
      </v-btn>
    </v-card-actions>
  </v-card>
</template>

<script>
import controlledTerminology from '@/api/controlledTerminology'
import HelpButtonWithPanels from '@/components/tools/HelpButtonWithPanels.vue'
import codelists from '@/utils/codelists'

export default {
  components: {
    HelpButtonWithPanels,
  },
  inject: ['formRules', 'eventBusEmit'],
  props: {
    modelValue: {
      type: Object,
      default: null,
    },
    codelistUid: {
      type: String,
      default: null,
    },
  },
  emits: ['close', 'update:modelValue'],
  setup() {
    return {
      getTermOrderInCodelist: codelists.getTermOrderInCodelist,
    }
  },
  data() {
    return {
      form: {},
      helpItems: [
        'CodelistTermCreationForm.sponsor_pref_name',
        'CodelistTermCreationForm.sponsor_sentence_case_name',
        'CodelistTermCreationForm.order',
      ],
      working: false,
    }
  },
  watch: {
    modelValue: {
      handler(val) {
        if (val) {
          this.form = {
            sponsor_preferred_name: val.sponsor_preferred_name,
            sponsor_preferred_name_sentence_case:
              val.sponsor_preferred_name_sentence_case,
            order: this.getTermOrderInCodelist(val, this.codelistUid),
          }
        }
      },
      immediate: true,
    },
  },
  methods: {
    close() {
      this.$emit('close')
      this.form.change_description = ''
    },
    setSentenceCase() {
      if (this.form.sponsor_preferred_name) {
        this.form.sponsor_preferred_name_sentence_case =
          this.form.sponsor_preferred_name.toLowerCase()
      }
    },
    async submit() {
      const { valid } = await this.$refs.observer.validate()

      if (!valid) return
      this.working = true
      try {
        let resp = await controlledTerminology.updateCodelistTermNames(
          this.modelValue.term_uid,
          this.form
        )
        const orderData = {
          codelist_uid: this.codelistUid,
          new_order: this.form.order,
        }
        resp = await controlledTerminology.updateCodelistTermOrder(
          this.modelValue.term_uid,
          orderData
        )
        resp = await controlledTerminology.getCodelistTermNames(
          this.modelValue.term_uid
        )
        this.$emit('update:modelValue', resp.data)
        this.eventBusEmit('notification', {
          msg: this.$t('CodelistTermNamesForm.update_success'),
        })
        this.close()
      } finally {
        this.working = false
      }
    },
  },
}
</script>

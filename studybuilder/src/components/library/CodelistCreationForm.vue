<template>
  <StepperForm
    ref="stepper"
    :title="$t('CodelistCreationForm.title')"
    :steps="steps"
    :form-observer-getter="getObserver"
    :help-items="helpItems"
    @close="cancel"
    @save="submit"
  >
    <template #[`step.catalogue`]="{ step }">
      <v-form :ref="`observer_${step}`">
        <v-row>
          <v-col>
            <v-select
              v-model="form.catalogue_name"
              data-cy="catalogue-dropdown"
              :label="$t('CodelistCreationForm.catalogue')"
              :items="catalogues"
              item-title="name"
              item-value="name"
              clearable
              density="compact"
              persistent-hint
              :rules="[formRules.required]"
            />
          </v-col>
        </v-row>
      </v-form>
    </template>
    <template #[`step.names`]="{ step }">
      <v-form :ref="`observer_${step}`">
        <v-row>
          <v-col>
            <v-text-field
              v-model="form.sponsor_preferred_name"
              data-cy="sponsor-preffered-name"
              :label="$t('CodelistSponsorValuesForm.pref_name')"
              clearable
              density="compact"
              class="mt-2"
              :rules="[formRules.required]"
            />
          </v-col>
        </v-row>
        <v-row>
          <v-col>
            <v-switch
              v-model="form.template_parameter"
              color="primary"
              :label="$t('CodelistSponsorValuesForm.tpl_parameter')"
              density="compact"
            />
          </v-col>
        </v-row>
      </v-form>
    </template>
    <template #[`step.attributes`]="{ step }">
      <v-form :ref="`observer_${step}`">
        <v-row>
          <v-col>
            <v-text-field
              v-model="form.name"
              data-cy="codelist-name"
              :label="$t('CodelistAttributesForm.name')"
              clearable
              density="compact"
              :rules="[formRules.required]"
            />
          </v-col>
        </v-row>
        <v-row>
          <v-col>
            <v-text-field
              v-model="form.submission_value"
              data-cy="submission-value"
              :label="$t('CodelistAttributesForm.subm_value')"
              density="compact"
              clearable
              :rules="[formRules.required]"
            />
          </v-col>
        </v-row>
        <v-row>
          <v-col>
            <v-text-field
              v-model="form.nci_preferred_name"
              data-cy="nci-preffered-name"
              :label="$t('CodelistAttributesForm.nci_pref_name')"
              density="compact"
              clearable
              :rules="[formRules.required]"
            />
          </v-col>
        </v-row>
        <v-row>
          <v-col>
            <v-switch
              v-model="form.extensible"
              color="primary"
              data-cy="extensible-toggle"
              :label="$t('CodelistAttributesForm.extensible')"
              density="compact"
            />
          </v-col>
        </v-row>
        <v-row>
          <v-col>
            <v-textarea
              v-model="form.definition"
              data-cy="definition"
              :label="$t('CodelistAttributesForm.definition')"
              rows="1"
              clearable
              auto-grow
              density="compact"
              :rules="[formRules.required]"
            />
          </v-col>
        </v-row>
      </v-form>
    </template>
  </StepperForm>
  <ConfirmDialog ref="confirm" :text-cols="6" :action-cols="5" />
</template>

<script>
import { computed } from 'vue'
import { useCtCataloguesStore } from '@/stores/library-ctcatalogues'
import controlledTerminology from '@/api/controlledTerminology'
import StepperForm from '@/components/tools/StepperForm.vue'
import ConfirmDialog from '@/components/tools/ConfirmDialog.vue'

export default {
  components: {
    StepperForm,
    ConfirmDialog,
  },
  inject: ['formRules'],
  emits: ['close', 'created'],
  setup() {
    const ctCataloguesStore = useCtCataloguesStore()

    return {
      catalogues: computed(() => ctCataloguesStore.catalogues),
    }
  },
  data() {
    return {
      form: {
        extensible: false,
        library_name: 'Sponsor',
        template_parameter: false,
      },
      helpItems: [
        'CodelistCreationForm.catalogue',
        'CodelistSponsorValuesForm.pref_name',
        'CodelistSponsorValuesForm.tpl_parameter',
        'CodelistAttributesForm.name',
        'CodelistAttributesForm.subm_value',
        'CodelistAttributesForm.nci_pref_name',
        'CodelistAttributesForm.extensible',
        'CodelistAttributesForm.definition',
      ],
      steps: [
        {
          name: 'catalogue',
          title: this.$t('CodelistCreationForm.step1_title'),
        },
        { name: 'names', title: this.$t('CodelistCreationForm.step2_title') },
        {
          name: 'attributes',
          title: this.$t('CodelistCreationForm.step3_title'),
        },
      ],
    }
  },
  methods: {
    async cancel() {
      if (this.form.catalogue_name === 'All') {
        this.close()
      } else {
        const options = {
          type: 'warning',
          cancelLabel: this.$t('_global.cancel'),
          agreeLabel: this.$t('_global.continue'),
        }
        if (
          await this.$refs.confirm.open(
            this.$t('_global.cancel_changes'),
            options
          )
        ) {
          this.close()
        }
      }
    },
    close() {
      this.$emit('close')
      this.form = {}
      this.$refs.stepper.reset()
    },
    getObserver(step) {
      return this.$refs[`observer_${step}`]
    },
    async submit() {
      this.form.terms = []
      const data = JSON.parse(JSON.stringify(this.form))
      try {
        const resp = await controlledTerminology.createCodelist(data)
        this.$emit('created', resp.data)
        this.close()
      } finally {
        this.$refs.stepper.loading = false
      }
    },
  },
}
</script>

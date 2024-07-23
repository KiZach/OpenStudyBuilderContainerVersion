<template>
  <HorizontalStepperForm
    ref="stepper"
    :title="title"
    :steps="steps"
    :form-observer-getter="getObserver"
    :editable="studyCompound !== undefined && studyCompound !== null"
    :help-items="helpItems"
    :edit-data="form"
    @close="close"
    @save="submit"
  >
    <template #[`step.type_of_treatment`]="{ step }">
      <v-form :ref="`observer_${step}`">
        <NotApplicableField
          ref="naField"
          :clean-function="cleanTypeOfTreatment"
          :disabled="typeOfTreatment_uidNADisabled"
          :checked="studyCompound && !studyCompound.compound"
        >
          <template #mainField="{ notApplicable }">
            <v-autocomplete
              v-model="form.type_of_treatment"
              :data-cy="$t('StudyCompoundForm.type_of_treatment')"
              :label="$t('StudyCompoundForm.type_of_treatment')"
              :items="typeOfTreatments"
              item-title="name.sponsor_preferred_name"
              item-value="term_uid"
              return-object
              :rules="[
                (value) => formRules.requiredIfNotNA(value, notApplicable),
              ]"
              density="compact"
              clearable
              class="required"
            />
          </template>
        </NotApplicableField>
      </v-form>
    </template>
    <template #[`step.compoundAlias`]="{ step }">
      <v-form :ref="`observer_${step}`">
        <v-row>
          <v-col cols="6">
            <v-autocomplete
              v-model="form.compoundSimple"
              :label="$t('StudyCompoundForm.compound')"
              :items="compounds"
              item-title="name"
              item-value="uid"
              return-object
              :rules="[formRules.required]"
              density="compact"
              clearable
              class="required"
            />
          </v-col>
          <v-col cols="6">
            <v-autocomplete
              v-model="form.compound_alias"
              :label="$t('StudyCompoundForm.compound_alias')"
              :items="compoundAliases"
              item-title="name"
              item-value="uid"
              return-object
              :rules="[formRules.required]"
              density="compact"
              clearable
              class="required"
            />
          </v-col>
        </v-row>
        <template v-if="form.compound">
          <v-row>
            <v-col cols="6">
              <YesNoField
                :model-value="form.compound.is_sponsor_compound"
                :label="$t('StudyCompoundForm.sponsor_compound')"
                inline
                disabled
                hide-details
              />
            </v-col>
            <v-col v-if="form.compound_alias" cols="6">
              <YesNoField
                :model-value="form.compound_alias.is_preferred_synonym"
                :label="$t('StudyCompoundForm.is_preferred_synonym')"
                inline
                disabled
                hide-details
              />
            </v-col>
          </v-row>
          <v-row>
            <v-col cols="6">
              <v-text-field
                :model-value="form.compound.nnc_long_number"
                :label="$t('CompoundForm.long_number')"
                density="compact"
                disabled
                variant="filled"
                hide-details
              />
            </v-col>
            <v-col cols="6">
              <v-text-field
                :model-value="form.compound.nnc_short_number"
                :label="$t('CompoundForm.short_number')"
                density="compact"
                disabled
                variant="filled"
                hide-details
              />
            </v-col>
          </v-row>
          <v-row>
            <v-col cols="6">
              <v-textarea
                :model-value="form.compound.definition"
                :label="$t('StudyCompoundForm.compound_definition')"
                density="compact"
                auto-grow
                rows="1"
                disabled
                variant="filled"
                hide-details
              />
            </v-col>
            <v-col v-if="form.compound_alias" cols="6">
              <v-textarea
                :model-value="form.compound_alias.definition"
                :label="$t('StudyCompoundForm.alias_definition')"
                density="compact"
                auto-grow
                rows="1"
                disabled
                variant="filled"
                hide-details
              />
            </v-col>
          </v-row>
          <v-row>
            <v-col cols="12">
              <v-text-field
                :model-value="substances"
                :label="$t('CompoundAliasForm.substance')"
                density="compact"
                disabled
                variant="filled"
                hide-details
              />
            </v-col>
          </v-row>
          <v-row>
            <v-col cols="12">
              <v-text-field
                :model-value="pharmacologicalClass"
                :label="$t('CompoundAliasForm.pharmacological_class')"
                density="compact"
                disabled
                variant="filled"
                hide-details
              />
            </v-col>
          </v-row>
        </template>
      </v-form>
    </template>
    <template #[`step.compound`]="{ step }">
      <v-form v-if="form.compound" :ref="`observer_${step}`">
        <v-row>
          <v-col>
            <v-autocomplete
              v-model="form.dosage_form_uid"
              :label="$t('StudyCompoundForm.dosage_form')"
              :items="form.compound.dosage_forms"
              item-title="name"
              item-value="term_uid"
              density="compact"
              clearable
            />
          </v-col>
        </v-row>
        <v-row>
          <v-col>
            <v-autocomplete
              v-model="form.strength_value_uid"
              :label="$t('StudyCompoundForm.compound_strength_value')"
              :items="form.compound.strength_values"
              :item-title="(item) => `${item.value} ${item.unit_label}`"
              item-value="uid"
              density="compact"
              clearable
            />
          </v-col>
        </v-row>
        <v-row>
          <v-col>
            <v-autocomplete
              v-model="form.route_of_administration_uid"
              :data-cy="$t('StudyCompoundForm.route_of_admin')"
              :label="$t('StudyCompoundForm.route_of_admin')"
              :items="form.compound.routes_of_administration"
              item-title="name"
              item-value="term_uid"
              density="compact"
              clearable
            />
          </v-col>
        </v-row>
        <v-row>
          <v-col>
            <v-autocomplete
              v-model="form.dispensed_in_uid"
              :data-cy="$t('StudyCompoundForm.dispensed_in')"
              :label="$t('StudyCompoundForm.dispensed_in')"
              :items="form.compound.dispensers"
              item-title="name"
              item-value="term_uid"
              density="compact"
              clearable
            />
          </v-col>
        </v-row>
        <v-row>
          <v-col>
            <v-autocomplete
              v-model="form.device_uid"
              :data-cy="$t('StudyCompoundForm.device')"
              :label="$t('StudyCompoundForm.device')"
              :items="form.compound.delivery_devices"
              item-title="name"
              item-value="term_uid"
              density="compact"
              clearable
            />
          </v-col>
        </v-row>
        <v-row>
          <v-col>
            <v-textarea
              v-model="form.other_info"
              :data-cy="$t('StudyCompoundForm.other')"
              :label="$t('StudyCompoundForm.other')"
              auto-grow
              rows="1"
              density="compact"
              clearable
            />
          </v-col>
        </v-row>
      </v-form>
    </template>
  </HorizontalStepperForm>
</template>

<script>
import compoundAliases from '@/api/concepts/compoundAliases'
import compounds from '@/api/concepts/compounds'
import compoundsSimple from '@/api/concepts/compoundsSimple'
import constants from '@/constants/studyCompounds'
import HorizontalStepperForm from '@/components/tools/HorizontalStepperForm.vue'
import NotApplicableField from '@/components/tools/NotApplicableField.vue'
import statuses from '@/constants/statuses'
import studyConstants from '@/constants/study'
import terms from '@/api/controlledTerminology/terms'
import YesNoField from '@/components/tools/YesNoField.vue'
import { useStudiesCompoundsStore } from '@/stores/studies-compounds'
import { useStudiesGeneralStore } from '@/stores/studies-general'

export default {
  components: {
    HorizontalStepperForm,
    NotApplicableField,
    YesNoField,
  },
  inject: ['eventBusEmit', 'formRules'],
  props: {
    studyCompound: {
      type: Object,
      default: undefined,
    },
  },
  emits: ['added', 'close'],
  setup() {
    const studiesCompoundsStore = useStudiesCompoundsStore()
    const studiesGeneralStore = useStudiesGeneralStore()

    return {
      studiesCompoundsStore,
      studiesGeneralStore,
    }
  },
  data() {
    return {
      compoundAliases: [],
      compounds: [],
      helpItems: [
        'StudyCompoundForm.type_of_treatment',
        'StudyCompoundForm.compound',
        'StudyCompoundForm.compound_alias',
        'StudyCompoundForm.pharma_class',
        'StudyCompoundForm.substance',
        'StudyCompoundForm.unii',
        'StudyCompoundForm.route_of_admin',
        'StudyCompoundForm.dosage_form',
        'StudyCompoundForm.dispensed_in',
        'StudyCompoundForm.device',
        'StudyCompoundForm.formulation',
        'StudyCompoundForm.other',
      ],
      form: this.getInitialForm(),
      typeOfTreatments: [],
      steps: this.getInitialSteps(),
    }
  },
  computed: {
    substances() {
      if (
        this.form.compound &&
        this.form.compound.substances &&
        this.form.compound.substances.length
      ) {
        return this.form.compound.substances
          .map((item) => `${item.substance_name} (${item.substance_unii})`)
          .join(', ')
      }
      return ''
    },
    pharmacologicalClass() {
      if (
        this.form.compound &&
        this.form.compound.substances &&
        this.form.compound.substances.length
      ) {
        return this.form.compound.substances
          .map((item) => item.pclass_name)
          .filter((pclass) => pclass !== undefined && pclass !== null)
          .join(', ')
      }
      return ''
    },
    title() {
      if (this.studyCompound) {
        return this.$t('StudyCompoundForm.edit_title')
      }
      return this.$t('StudyCompoundForm.add_title')
    },
    typeOfTreatment_uidNADisabled() {
      if (
        (this.$refs.naField && this.$refs.naField.notApplicable) ||
        (this.studyCompound && !this.studyCompound.compound)
      ) {
        return false
      }
      if (!this.form.type_of_treatment) {
        return true
      }
      const types = [
        constants.TYPE_OF_TREATMENT_INVESTIGATIONAL_PRODUCT,
        constants.TYPE_OF_TREATMENT_CURRENT_TREATMENT,
        constants.TYPE_OF_TREATMENT_COMPARATIVE_TREATMENT,
      ]
      if (
        !types.find(
          (item) => item === this.form.type_of_treatment.sponsor_preferred_name
        )
      ) {
        return true
      }
      const studyCompounds =
        this.studiesCompoundsStore.getStudyCompoundsByTypeOfTreatment(
          this.form.type_of_treatment.term_uid
        )
      if (studyCompounds.length) {
        return true
      }
      const NAstudyCompounds =
        this.studiesCompoundsStore.getNAStudyCompoundsByTypeOfTreatment(
          this.form.type_of_treatment.term_uid
        )
      if (NAstudyCompounds.length) {
        return true
      }
      return false
    },
  },
  watch: {
    studyCompound: {
      handler: function (val) {
        if (val) {
          this.form.type_of_treatment = val.type_of_treatment
          this.form.other_info = val.other_info
          if (val.compound) {
            this.form.compound = val.compound
            this.form.compoundSimple = {
              uid: val.compound.uid,
              name: val.compound.name,
            }
            const filters = {
              compound_uid: { v: [val.compound.uid] },
              status: { v: [statuses.FINAL] },
            }
            compoundAliases.getFiltered({ filters }).then((resp) => {
              this.compoundAliases = resp.data.items
            })
          } else {
            this.steps = [
              {
                name: 'type_of_treatment',
                title: this.$t('StudyCompoundForm.step1_title'),
              },
            ]
          }
          if (val.compound_alias) {
            this.form.compound_alias = val.compound_alias
          }
          if (val.dosage_form) {
            this.form.dosage_form_uid = val.dosage_form.term_uid
          }
          if (val.route_of_administration) {
            this.form.route_of_administration_uid =
              val.route_of_administration.term_uid
          }
          if (val.dispensed_in) {
            this.form.dispensed_in_uid = val.dispensed_in.term_uid
          }
          if (val.device) {
            this.form.device_uid = val.device.term_uid
          }
          if (val.strength_value) {
            this.form.strength_value_uid = val.strength_value.uid
          }
        }
      },
      immediate: true,
    },
    'form.compoundSimple'(newValue) {
      if (newValue) {
        if (
          !this.studyCompound ||
          this.studyCompound.compound.uid !== newValue.uid
        ) {
          this.form.compound_alias = null
        }
        const filters = {
          compound_uid: { v: [newValue.uid] },
          status: { v: [statuses.FINAL] },
        }
        compoundAliases.getFiltered({ filters }).then((resp) => {
          this.compoundAliases = resp.data.items
        })
        if (newValue.uid) {
          compounds.getObject(newValue.uid).then((resp) => {
            this.form.compound = resp.data
          })
        }
      }
    },
  },
  mounted() {
    const filters = {
      status: { v: [statuses.FINAL] },
    }
    compoundsSimple.getFiltered({ filters }).then((resp) => {
      this.compounds = resp.data.items
    })
    terms.getByCodelist('typeOfTreatment').then((resp) => {
      this.typeOfTreatments = resp.data.items
    })
  },
  methods: {
    close() {
      this.$emit('close')
      this.form = this.getInitialForm()
      this.$refs.stepper.reset()
      this.$refs.naField.reset()
    },
    getInitialForm() {
      return {
        compound: null,
        compoundSimple: null,
        compound_alias: null,
        type_of_treatment: null,
        dosage_form_uid: null,
        strength_value_uid: null,
        route_of_administration_uid: null,
        dispensed_in_uid: null,
        device_uid: null,
        other_info: null,
      }
    },
    getInitialSteps() {
      return [
        {
          name: 'type_of_treatment',
          title: this.$t('StudyCompoundForm.step1_title'),
        },
        {
          name: 'compoundAlias',
          title: this.$t('StudyCompoundForm.step2_title'),
        },
        { name: 'compound', title: this.$t('StudyCompoundForm.step3_title') },
      ]
    },
    getObserver(step) {
      return this.$refs[`observer_${step}`]
    },
    cleanTypeOfTreatment(value) {
      if (value) {
        this.steps = [
          {
            name: 'type_of_treatment',
            title: this.$t('StudyCompoundForm.step1_title'),
          },
        ]
      } else {
        this.steps = this.getInitialSteps()
      }
    },
    async submit() {
      const data = JSON.parse(JSON.stringify(this.form))
      data.type_of_treatment_uid = data.type_of_treatment.term_uid
      delete data.type_of_treatment
      delete data.compound
      if (data.compound_alias) {
        data.compound_alias_uid = data.compound_alias.uid || null
      } else {
        data.reason_for_missing_null_value_uid =
          studyConstants.TERM_NOT_APPLICABLE
      }

      let action = null
      let notification = null
      let args = null
      let event
      if (!this.studyCompound) {
        action = 'addStudyCompound'
        notification = 'add_success'
        event = 'added'
        args = { studyUid: this.studiesGeneralStore.selectedStudy.uid, data }
      } else {
        action = 'updateStudyCompound'
        notification = 'update_success'
        args = {
          studyUid: this.studiesGeneralStore.selectedStudy.uid,
          studyCompoundUid: this.studyCompound.study_compound_uid,
          data,
        }
      }
      try {
        await this.studiesCompoundsStore[action](args)
        this.eventBusEmit('notification', {
          msg: this.$t(`StudyCompoundForm.${notification}`),
        })
        if (event) {
          this.$emit(event)
        }
        this.close()
      } finally {
        this.$refs.stepper.loading = false
      }
    },
  },
}
</script>

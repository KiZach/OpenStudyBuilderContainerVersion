<template>
  <SimpleFormDialog
    ref="form"
    :title="title"
    :help-items="helpItems"
    :open="open"
    @close="cancel"
    @submit="submit"
  >
    <template #body>
      <v-form ref="observer">
        <v-row>
          <v-col cols="12">
            <v-autocomplete
              v-model="form.arm_uids"
              :label="$t('StudyCohorts.study_arm')"
              data-cy="study-arm"
              :items="arms"
              item-title="name"
              item-value="arm_uid"
              clearable
              multiple
              density="compact"
            />
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="12">
            <v-autocomplete
              v-model="form.branch_arm_uids"
              :label="$t('StudyCohorts.study_branch_arm')"
              data-cy="branch-arm"
              :items="branches"
              item-title="name"
              item-value="branch_arm_uid"
              clearable
              multiple
              density="compact"
            />
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="12">
            <v-text-field
              v-model="form.name"
              :label="$t('StudyCohorts.cohort_name')"
              data-cy="study-cohort-name"
              :rules="[formRules.required, formRules.max(form.name, 200)]"
              clearable
              class="required"
              density="compact"
            />
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="12">
            <v-text-field
              v-model="form.short_name"
              :label="$t('StudyCohorts.cohort_short_name')"
              data-cy="study-cohort-short-name"
              :rules="[formRules.required, formRules.max(form.name, 20)]"
              clearable
              class="required"
              density="compact"
            />
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="12">
            <v-text-field
              v-model="form.code"
              :label="$t('StudyCohorts.cohort_code')"
              :rules="[
                formRules.required,
                formRules.numeric,
                formRules.max_value(form.code, 99),
                formRules.min_value(form.code, 1),
              ]"
              data-cy="study-cohort-code"
              type="number"
              clearable
              class="required"
              density="compact"
            />
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="12">
            <v-text-field
              :disabled="!form.arm_uids"
              :model-value="form.number_of_subjects"
              :label="$t('StudyCohorts.number_of_subjects')"
              :rules="[
                formRules.min_value(form.number_of_subjects, 1),
                numberOfSubjectsMaxValueRule(
                  form.number_of_subjects,
                  findMaxNuberOfSubjects()
                ),
              ]"
              data-cy="study-cohort-planned-number-of-subjects"
              type="number"
              clearable
              density="compact"
              @update:model-value="
                form.number_of_subjects = $event !== '' ? $event : null
              "
            />
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="12">
            <v-text-field
              v-model="form.description"
              :label="$t('_global.description')"
              data-cy="study-cohort-description"
              clearable
              density="compact"
            />
          </v-col>
        </v-row>
        <div class="mt-4">
          <label class="v-label">{{ $t('StudyCohorts.colour') }}</label>
          <v-color-picker
            v-model="colorHash"
            clearable
            show-swatches
            hide-canvas
            hide-sliders
            swatches-max-height="300px"
          />
        </div>
      </v-form>
    </template>
  </SimpleFormDialog>
</template>

<script>
import arms from '@/api/arms'
import SimpleFormDialog from '@/components/tools/SimpleFormDialog.vue'
import { useStudiesGeneralStore } from '@/stores/studies-general'
import { useFormStore } from '@/stores/form'

export default {
  components: {
    SimpleFormDialog,
  },
  inject: ['eventBusEmit', 'formRules'],
  props: {
    editedCohort: {
      type: Object,
      default: undefined,
    },
    arms: {
      type: Array,
      default: () => [],
    },
    branches: {
      type: Array,
      default: () => [],
    },
    open: Boolean,
  },
  emits: ['close'],
  setup() {
    const studiesGeneralStore = useStudiesGeneralStore()
    const formStore = useFormStore()
    return {
      selectedStudy: studiesGeneralStore.selectedStudy,
      formStore,
    }
  },
  data() {
    return {
      form: {},
      helpItems: [],
      colorHash: null,
    }
  },
  computed: {
    title() {
      return Object.keys(this.editedCohort).length !== 0
        ? this.$t('StudyCohorts.edit_cohort')
        : this.$t('StudyCohorts.add_cohort')
    },
  },
  watch: {
    editedCohort(value) {
      if (Object.keys(value).length !== 0) {
        this.form = JSON.parse(JSON.stringify(value))
        this.form.arm_uids = value.arm_roots
          ? value.arm_roots.map((el) => el.arm_uid)
          : null
        this.form.branch_arm_uids = value.branch_arm_roots
          ? value.branch_arm_roots.map((el) => el.branch_arm_uid)
          : null
        if (value.colour_code) {
          this.colorHash = value.colour_code
        }
        this.formStore.save(this.form)
      }
    },
  },
  mounted() {
    if (Object.keys(this.editedCohort).length !== 0) {
      this.form = JSON.parse(JSON.stringify(this.editedCohort))
      this.form.arm_uids = this.editedCohort.arm_roots
        ? this.editedCohort.arm_roots.map((el) => el.arm_uid)
        : null
      this.form.branch_arm_uids = this.editedCohort.branch_arm_roots
        ? this.editedCohort.branch_arm_roots.map((el) => el.branch_arm_uid)
        : null
      if (this.editedCohort.colour_code) {
        this.colorHash = this.editedCohort.colour_code
      }
      this.formStore.save(this.form)
    }
  },
  methods: {
    // This rule is same as max_value generic rule but with custom message
    numberOfSubjectsMaxValueRule(value, max) {
      let result = true
      if (value !== undefined && value !== null) {
        if (Array.isArray(value)) {
          result =
            value.length > 0 &&
            value.every((val) => this.formRules.max_value(val, max))
        } else {
          result = Number(value) <= Number(max)
        }
      }
      return result || this.$t('StudyCohorts.number_of_subjects_exceeds')
    },
    async submit() {
      if (Object.keys(this.editedCohort).length !== 0) {
        this.edit()
      } else {
        this.create()
      }
    },
    async create() {
      if (this.colorHash) {
        this.form.colour_code = this.colorHash.hexa
      } else {
        this.form.colour_code = '#BDBDBD'
      }
      arms.createCohort(this.selectedStudy.uid, this.form).then(
        () => {
          this.eventBusEmit('notification', {
            msg: this.$t('StudyCohorts.cohort_created'),
          })
          this.close()
        },
        () => {
          this.$refs.form.working = false
        }
      )
    },
    edit() {
      if (this.colorHash) {
        this.form.colour_code =
          this.colorHash.hexa !== undefined
            ? this.colorHash.hexa
            : this.colorHash
      } else {
        this.form.colour_code = '#BDBDBD'
      }
      arms
        .editCohort(
          this.selectedStudy.uid,
          this.editedCohort.cohort_uid,
          this.form
        )
        .then(
          () => {
            this.eventBusEmit('notification', {
              msg: this.$t('StudyCohorts.cohort_updated'),
            })
            this.close()
          },
          () => {
            this.$refs.form.working = false
          }
        )
    },
    close() {
      this.form = {}
      this.formStore.reset()
      this.colorHash = null
      this.$refs.observer.reset()
      this.$emit('close')
    },
    async cancel() {
      if (this.formStore.isEmpty || this.formStore.isEqual(this.form)) {
        this.close()
      } else {
        const options = {
          type: 'warning',
          cancelLabel: this.$t('_global.cancel'),
          agreeLabel: this.$t('_global.continue'),
        }
        if (
          await this.$refs.form.confirm(
            this.$t('_global.cancel_changes'),
            options
          )
        ) {
          this.close()
        }
      }
    },
    findMaxNuberOfSubjects() {
      let subjectsSum = 0
      if (this.form.arm_uids) {
        this.form.arm_uids.forEach((el) => {
          subjectsSum += this.arms.find(
            (e) => e.arm_uid === el
          ).number_of_subjects
        })
      }
      return subjectsSum
    },
  },
}
</script>

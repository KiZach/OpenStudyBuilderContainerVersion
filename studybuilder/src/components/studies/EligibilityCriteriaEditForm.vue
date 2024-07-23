<template>
  <StudySelectionEditForm
    v-if="studyCriteria"
    ref="form"
    :title="$t('EligibilityCriteriaEditForm.title')"
    :study-selection="studyCriteria"
    :template="template"
    :library-name="library.name"
    object-type="criteria"
    max-template-length
    :open="open"
    :get-object-from-selection="(selection) => selection.criteria"
    :prepare-template-payload-func="prepareTemplatePayload"
    @init-form="initForm"
    @submit="submit"
    @close="$emit('close')"
  >
    <template #formFields="{ editTemplate, form }">
      <p class="mt-6 text-secondary text-h6">
        {{ $t('EligibilityCriteriaEditForm.key_criteria') }}
      </p>
      <v-row>
        <v-col cols="11">
          <YesNoField v-model="form.key_criteria" :disabled="editTemplate" />
        </v-col>
      </v-row>
    </template>
  </StudySelectionEditForm>
</template>

<script>
import { computed } from 'vue'
import instances from '@/utils/instances'
import study from '@/api/study'
import StudySelectionEditForm from './StudySelectionEditForm.vue'
import YesNoField from '@/components/tools/YesNoField.vue'
import { useStudiesGeneralStore } from '@/stores/studies-general'

export default {
  components: {
    StudySelectionEditForm,
    YesNoField,
  },
  inject: ['eventBusEmit'],
  props: {
    studyCriteria: {
      type: Object,
      default: undefined,
    },
    open: Boolean,
  },
  emits: ['close', 'updated'],
  setup() {
    const studiesGeneralStore = useStudiesGeneralStore()
    return {
      selectedStudy: computed(() => studiesGeneralStore.selectedStudy),
    }
  },
  computed: {
    template() {
      return this.studyCriteria.criteria
        ? this.studyCriteria.criteria.criteria_template
        : this.studyCriteria.criteria_template
    },
    library() {
      return this.studyCriteria.criteria
        ? this.studyCriteria.criteria.library
        : this.studyCriteria.criteria_template.library
    },
  },
  methods: {
    initForm(form) {
      form.key_criteria = this.studyCriteria.key_criteria
      this.originalForm = JSON.parse(JSON.stringify(form))
    },
    prepareTemplatePayload(data) {
      data.type_uid = this.studyCriteria.criteria_type.term_uid
    },
    async getStudyCriteriaNamePreview(parameters) {
      const criteriaData = {
        criteria_template_uid:
          this.studyCriteria.criteria.criteria_template.uid,
        parameter_terms: await instances.formatParameterValues(parameters),
        library_name: this.studyCriteria.criteria.library.name,
      }
      const resp = await study.getStudyCriteriaPreview(this.selectedStudy.uid, {
        criteria_data: criteriaData,
      })
      return resp.data.criteria.name
    },
    async submit(newTemplate, form, parameters) {
      const payload = { ...form }
      // FIXME:
      // The PATCH endpoint does not behave properly since it expects a complete payload...
      // It's going to be fixed in the API but I don't know when so, for now, I commented
      // out the following lines.
      //
      // const payload = formUtils.getDifferences(this.originalForm, form)
      // if (!this.studyCriteria.criteria) {
      //   payload.parameters = parameters
      // } else {
      //   const namePreview = await this.getStudyCriteriaNamePreview(parameters)
      //   if (namePreview !== this.studyCriteria.criteria.name) {
      //     payload.parameters = parameters
      //   }
      // }
      // if (_isEmpty(payload)) {
      //   this.eventBusEmit('notification', { msg: this.$t('_global.no_changes'), type: 'info' })
      //   this.$refs.form.close()
      //   return
      // }
      // if (payload.parameters) {
      payload.parameter_terms =
        await instances.formatParameterValues(parameters)
      payload.criteria_template_uid = newTemplate
        ? newTemplate.uid
        : this.template.uid
      payload.library_name = this.library.name
      //   delete payload.parameters
      // }
      await study.patchStudyCriteria(
        this.selectedStudy.uid,
        this.studyCriteria.study_criteria_uid,
        payload
      )
      this.eventBusEmit('notification', {
        msg: this.$t('EligibilityCriteriaEditForm.update_success'),
      })
      this.$emit('updated')
      this.$refs.form.close()
    },
  },
}
</script>

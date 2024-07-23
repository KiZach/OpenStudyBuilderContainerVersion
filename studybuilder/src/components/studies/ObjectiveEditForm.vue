<template>
  <StudySelectionEditForm
    v-if="studyObjective"
    ref="form"
    :title="$t('StudyObjectiveEditForm.title')"
    :study-selection="studyObjective"
    :template="template"
    :library-name="library.name"
    object-type="objective"
    :open="open"
    :get-object-from-selection="(selection) => selection.objective"
    @init-form="initForm"
    @submit="submit"
    @close="$emit('close')"
  >
    <template #formFields="{ editTemplate, form }">
      <p class="mt-6 text-secondary text-h6">
        {{ $t('StudyObjectiveEditForm.select_level') }}
      </p>
      <v-row>
        <v-col cols="11">
          <v-select
            v-model="form.objective_level"
            :label="$t('StudyObjectiveForm.objective_level')"
            :items="objectiveLevels"
            item-title="sponsor_preferred_name"
            return-object
            dense
            clearable
            style="max-width: 400px"
            :disabled="editTemplate"
          />
        </v-col>
      </v-row>
    </template>
  </StudySelectionEditForm>
</template>

<script>
import _isEmpty from 'lodash/isEmpty'
import formUtils from '@/utils/forms'
import instances from '@/utils/instances'
import study from '@/api/study'
import StudySelectionEditForm from './StudySelectionEditForm.vue'
import { useStudiesGeneralStore } from '@/stores/studies-general'
import { useStudiesObjectivesStore } from '@/stores/studies-objectives'
import { computed } from 'vue'

export default {
  components: {
    StudySelectionEditForm,
  },
  inject: ['eventBusEmit'],
  props: {
    studyObjective: {
      type: Object,
      default: undefined,
    },
    open: Boolean,
  },
  emits: ['close', 'updated'],
  setup() {
    const studiesGeneralStore = useStudiesGeneralStore()
    const studiesObjectivesStore = useStudiesObjectivesStore()
    return {
      selectedStudy: computed(() => studiesGeneralStore.selectedStudy),
      objectiveLevels: computed(() => studiesGeneralStore.objectiveLevels),
      updateStudyObjective: studiesObjectivesStore.updateStudyObjective,
    }
  },
  computed: {
    template() {
      return this.studyObjective.objective
        ? this.studyObjective.objective.objective_template
        : this.studyObjective.objective_template
    },
    library() {
      return this.studyObjective.objective
        ? {
            name: this.studyObjective.objective.objective_template.library_name,
          }
        : this.studyObjective.objective_template.library
    },
  },
  methods: {
    initForm(form) {
      form.objective_level = this.studyObjective.objective_level
      this.originalForm = JSON.parse(JSON.stringify(form))
    },
    async getStudyObjectiveNamePreview(parameters) {
      const objectiveData = {
        objective_template_uid:
          this.studyObjective.objective.objective_template.uid,
        parameter_terms: await instances.formatParameterValues(parameters),
        library_name: this.studyObjective.objective.library.name,
      }
      const resp = await study.getStudyObjectivePreview(
        this.selectedStudy.uid,
        { objective_data: objectiveData }
      )
      return resp.data.objective.name
    },
    async submit(newTemplate, form, parameters) {
      const data = formUtils.getDifferences(this.originalForm, form)

      if (newTemplate) {
        data.parameters = parameters
      } else if (!this.studyObjective.objective) {
        data.parameters = parameters
      } else {
        const namePreview = await this.getStudyObjectiveNamePreview(parameters)
        if (namePreview !== this.studyObjective.objective.name) {
          data.parameters = parameters
        }
      }
      if (_isEmpty(data)) {
        this.eventBusEmit('notification', {
          msg: this.$t('_global.no_changes'),
          type: 'info',
        })
        this.$refs.form.close()
        return
      }
      const args = {
        studyUid: this.selectedStudy.uid,
        studyObjectiveUid: this.studyObjective.study_objective_uid,
        form: data,
        library: this.library,
      }
      if (newTemplate) {
        args.template = newTemplate
      } else {
        args.template = this.template
      }
      this.updateStudyObjective(args)
        .then(() => {
          this.eventBusEmit('notification', {
            msg: this.$t('StudyObjectiveEditForm.objective_updated'),
          })
          this.$emit('updated')
          this.$refs.form.close()
        })
        .catch((err) => {
          console.log(err)
        })
    },
  },
}
</script>

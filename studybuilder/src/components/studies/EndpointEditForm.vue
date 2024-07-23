<template>
  <StudySelectionEditForm
    v-if="studyEndpoint"
    ref="formRef"
    :title="$t('StudyEndpointEditForm.title')"
    :study-selection="studyEndpoint"
    :template="template"
    :library-name="library.name"
    object-type="endpoint"
    :open="open"
    :get-object-from-selection="(selection) => selection.endpoint"
    :with-unformatted-version="false"
    @init-form="initForm"
    @submit="submit"
    @close="close"
  >
    <template #formFields="{ editTemplate, form }">
      <v-form ref="observer">
        <p class="mt-6 text-secondary text-h6">
          {{ $t('StudyEndpointEditForm.units_section') }}
        </p>
        <v-row>
          <v-col cols="9">
            <MultipleSelect
              v-model="form.endpoint_units.units"
              :label="$t('StudyEndpointEditForm.unit')"
              :items="studiesGeneralStore.allUnits"
              :rules="[(value) => formRules.requiredIfNotNA(value, skipUnits)]"
              item-title="name"
              return-object
              :disabled="skipUnits || editTemplate"
            />
          </v-col>
          <v-col cols="3">
            <v-select
              v-if="form.endpoint_units.units.length > 1"
              v-model="form.endpoint_units.separator"
              :label="$t('ParameterValueSelector.separator')"
              :items="separators"
              clearable
              :rules="[formRules.required]"
            />
          </v-col>
        </v-row>
        <p class="mt-6 text-secondary text-h6">
          {{ $t('StudyEndpointEditForm.timeframe_section') }}
        </p>
        <v-row>
          <v-col cols="11">
            <v-autocomplete
              v-model="timeframeTemplate"
              :label="$t('StudyEndpointEditForm.timeframe')"
              :items="timeframeTemplates"
              item-title="name_plain"
              return-object
              :rules="[formRules.required]"
              :disabled="editTemplate"
            />
          </v-col>
        </v-row>
        <div v-if="timeframeTemplate" class="mt-2">
          <v-progress-circular
            v-if="loadingParameters"
            indeterminate
            color="secondary"
          />

          <template v-else>
            <ParameterValueSelector
              ref="timeframeParamSelector"
              :model-value="timeframeTemplateParameters"
              :template="timeframeTemplate.name"
              color="white"
              stacked
              :disabled="editTemplate"
              :with-unformatted-version="false"
            />
          </template>
        </div>
        <p class="mt-6 text-secondary text-h6">
          {{ $t('StudyEndpointEditForm.unformatted_preview_section') }}
        </p>
        <v-card flat class="bg-parameterBackground">
          <v-card-text>
            <template v-if="$refs.form && $refs.form.$refs.paramSelector">
              {{ $refs.form.$refs.paramSelector.namePlainPreview }} ({{
                unitsDisplay(form.endpoint_units.units)
              }}).
            </template>
            <template v-if="$refs.timeframeParamSelector">
              {{ $t('StudyEndpointEditForm.timeframe') }}:
              {{ $refs.timeframeParamSelector.namePlainPreview }}.
            </template>
          </v-card-text>
        </v-card>
        <p class="mt-6 text-secondary text-h6">
          {{ $t('StudyEndpointEditForm.level_section') }}
        </p>
        <v-row>
          <v-col cols="6">
            <v-select
              v-model="form.endpoint_level"
              :label="$t('StudyEndpointForm.endpoint_level')"
              :items="studiesGeneralStore.endpointLevels"
              item-title="sponsor_preferred_name"
              return-object
              clearable
              :disabled="editTemplate"
            />
          </v-col>
          <v-col cols="6">
            <v-select
              v-model="form.endpoint_sublevel"
              :label="$t('StudyEndpointForm.endpoint_sub_level')"
              :items="studiesGeneralStore.endpointSubLevels"
              item-title="sponsor_preferred_name"
              return-object
              clearable
              :disabled="editTemplate"
            />
          </v-col>
        </v-row>
        <p class="mt-6 text-secondary text-h6">
          {{ $t('StudyEndpointEditForm.objective_section') }}
        </p>
        <v-row>
          <v-col cols="11">
            <v-autocomplete
              v-model="form.study_objective"
              :label="$t('StudyEndpointForm.objective')"
              :items="studyObjectives"
              item-title="objective.name_plain"
              return-object
              clearable
              :disabled="editTemplate"
            />
          </v-col>
        </v-row>
      </v-form>
    </template>
  </StudySelectionEditForm>
</template>

<script setup>
import _isEmpty from 'lodash/isEmpty'
import constants from '@/constants/libraries'
import formUtils from '@/utils/forms'
import instances from '@/utils/instances'
import MultipleSelect from '@/components/tools/MultipleSelect.vue'
import ParameterValueSelector from '@/components/tools/ParameterValueSelector.vue'
import statuses from '@/constants/statuses'
import study from '@/api/study'
import StudySelectionEditForm from './StudySelectionEditForm.vue'
import timeframes from '@/api/timeframes'
import timeframeTemplatesApi from '@/api/timeframeTemplates'
import { useStudiesGeneralStore } from '@/stores/studies-general'
import { useStudiesEndpointsStore } from '@/stores/studies-endpoints'
import { inject, ref, watch, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'

const props = defineProps({
  studyEndpoint: {
    type: Object,
    default: undefined,
  },
  open: Boolean,
})
const { t } = useI18n()
const emit = defineEmits(['close', 'updated'])
const eventBusEmit = inject('eventBusEmit')
const formRules = inject('formRules')
const studiesGeneralStore = useStudiesGeneralStore()
const studiesEndpointsStore = useStudiesEndpointsStore()
const loadingParameters = ref(false)
const skipUnits = ref(false)
const studyObjectives = ref([])
const timeframeTemplate = ref(null)
const timeframeTemplates = ref([])
const originalForm = ref({})
const timeframeTemplateParameters = ref([])
const separators = ref([' and ', ' or ', ' and/or '])
const formRef = ref()
const observer = ref()

const template = computed(() => {
  return props.studyEndpoint.endpoint
    ? props.studyEndpoint.endpoint.endpoint_template
    : props.studyEndpoint.endpoint_template
})
const library = computed(() => {
  return props.studyEndpoint.endpoint
    ? props.studyEndpoint.endpoint.library
    : props.studyEndpoint.endpoint_template.library
})

watch(timeframeTemplate, (value) => {
  if (!value) {
    return
  }
  if (
    props.studyEndpoint.timeframe &&
    props.studyEndpoint.timeframe.timeframe_template.uid === value.uid
  ) {
    return
  }
  loadingParameters.value = true
  timeframeTemplatesApi
    .getParameters(value.uid, {
      study_uid: studiesGeneralStore.selectedStudy.uid,
    })
    .then((resp) => {
      timeframeTemplateParameters.value = resp.data
      loadingParameters.value = false
    })
})

onMounted(() => {
  getTimeframeTemplates()
  study
    .getStudyObjectives(studiesGeneralStore.selectedStudy.uid)
    .then((resp) => {
      studyObjectives.value = resp.data.items
    })
})

function close() {
  timeframeTemplate.value = null
  emit('close')
}

function initForm(form) {
  form.endpoint_units = props.studyEndpoint.endpoint_units
  form.endpoint_level = props.studyEndpoint.endpoint_level
  form.endpoint_sublevel = props.studyEndpoint.endpoint_sublevel
  if (props.studyEndpoint.timeframe) {
    timeframeTemplate.value = props.studyEndpoint.timeframe.timeframe_template
    timeframes
      .getObjectParameters(props.studyEndpoint.timeframe.uid, {
        study_uid: studiesGeneralStore.selectedStudy.uid,
      })
      .then((resp) => {
        timeframeTemplateParameters.value = resp.data
        instances.loadParameterValues(
          props.studyEndpoint.timeframe.parameter_terms,
          timeframeTemplateParameters.value
        )
      })
  }
  if (props.studyEndpoint.study_objective) {
    form.study_objective = props.studyEndpoint.study_objective
  }
  originalForm.value = JSON.parse(JSON.stringify(form))
}

async function getStudyEndpointNamePreview(parameters) {
  const endpointData = {
    endpoint_template_uid: props.studyEndpoint.endpoint.endpoint_template.uid,
    parameter_terms: await instances.formatParameterValues(parameters),
    library_name: props.studyEndpoint.endpoint.library.name,
  }
  const resp = await study.getStudyEndpointPreview(
    studiesGeneralStore.selectedStudy.uid,
    { endpoint_data: endpointData }
  )
  return resp.data.endpoint.name
}

async function getTimeframeNamePreview(parameters) {
  const data = {
    timeframe_template_uid:
      props.studyEndpoint.timeframe.timeframe_template.uid,
    parameter_terms: await instances.formatParameterValues(parameters),
    library_name: props.studyEndpoint.timeframe.library.name,
  }
  const resp = await timeframes.getPreview(data)
  return resp.data.name
}

function getTimeframeTemplates() {
  const params = {
    filters: { 'library.name': { v: [constants.LIBRARY_SPONSOR] } },
    page_size: 0,
    status: statuses.FINAL,
  }
  timeframeTemplatesApi.get(params).then((resp) => {
    timeframeTemplates.value = resp.data.items
  })
}

function unitsDisplay(units) {
  let result = ''
  if (units) {
    units.forEach((unit) => {
      result +=
        studiesGeneralStore.allUnits.find((u) => u.uid === unit.uid).name + ', '
    })
  }
  return result.slice(0, -2)
}

async function submit(newTemplate, form, parameters) {
  const { valid } = await observer.value.validate()
  if (!valid) {
    formRef.value.$refs.form.working = false
    return
  }
  const data = formUtils.getDifferences(originalForm.value, form)

  if (newTemplate) {
    data.endpoint_template = newTemplate
    data.endpoint_parameters = parameters
  } else if (!props.studyEndpoint.endpoint) {
    data.endpoint_template = props.studyEndpoint.endpoint_template
    data.endpoint_parameters = parameters
  } else {
    const namePreview = await getStudyEndpointNamePreview(parameters)
    if (namePreview !== props.studyEndpoint.endpoint.name) {
      data.endpoint_template = props.studyEndpoint.endpoint.endpoint_template
      // Hotfix because we don't have the template library here...
      data.endpoint_template.library = {
        name: constants.LIBRARY_SPONSOR,
      }
      data.endpoint_parameters = parameters
    }
  }
  if (!props.studyEndpoint.timeframe) {
    if (timeframeTemplate.value) {
      data.timeframe_template = timeframeTemplate.value
      data.timeframe_parameters = timeframeTemplateParameters.value
    }
  } else {
    const namePreview = await getTimeframeNamePreview(
      timeframeTemplateParameters.value
    )
    if (namePreview !== props.studyEndpoint.timeframe.name) {
      data.timeframe_template = timeframeTemplate.value
      // Hotfix because we don't have the template library here...
      data.timeframe_template.library = {
        name: constants.LIBRARY_SPONSOR,
      }
      data.timeframe_parameters = timeframeTemplateParameters.value
    }
  }
  if (_isEmpty(data)) {
    eventBusEmit('notification', { msg: t('_global.no_changes'), type: 'info' })
    formRef.value.close()
    return
  }
  const args = {
    studyUid: studiesGeneralStore.selectedStudy.uid,
    studyEndpointUid: props.studyEndpoint.study_endpoint_uid,
    form: data,
  }
  studiesEndpointsStore
    .updateStudyEndpoint(args)
    .then(() => {
      eventBusEmit('notification', {
        msg: t('StudyEndpointEditForm.endpoint_updated'),
      })
      emit('updated')
      formRef.value.close()
    })
    .catch((err) => {
      formRef.value.$refs.form.working = false
      console.log(err)
    })
}
</script>

<template>
  <v-card
    data-cy="form-body"
    color="dfltBackground"
    class="bg-dfltBackground fullscreen-dialog"
  >
    <v-card-title class="d-flex align-center">
      <span class="dialog-title ml-6">{{ title }}</span>
      <HelpButton v-if="helpText" :help-text="helpText" />
      <HelpButtonWithPanels
        v-if="helpItems"
        :title="$t('_global.help')"
        :items="helpItems"
      />
      <v-btn
        v-if="formUrl"
        color="secondary"
        class="ml-2"
        size="small"
        @click="copyUrl"
      >
        {{ $t('_global.copy_link') }}
      </v-btn>
    </v-card-title>
    <v-card-text class="mt-4 bg-dfltBackground">
      <v-stepper
        v-model="currentStep"
        bg-color="white"
        :items="stepTitles"
        :non-linear="editable"
        :editable="editable"
        hide-actions
      >
        <template
          v-for="(step, index) in stepTitles"
          :key="`content-${index}`"
          #[`item.${index+1}`]
        >
          <v-sheet elevation="0" class="ma-2 pa-4">
            <v-row>
              <v-col
                v-if="step.belowDisplay"
                cols="12"
                class="d-flex align-start justify-end py-4"
              >
                <div v-if="currentStep === 1">
                  <slot name="actions" />
                </div>
                <div class="mx-2">
                  <v-btn
                    v-if="currentStep < steps.length"
                    :data-cy="steps[index].name + '-continue-button'"
                    color="secondary"
                    class="ml-2"
                    :loading="loadingContinue"
                    elevation="2"
                    width="120px"
                    @click="goToStep(index + 1, index + 2)"
                  >
                    {{ $t('_global.continue') }}
                  </v-btn>
                  <v-btn
                    v-if="currentStep >= steps.length || saveFromAnyStep"
                    :data-cy="steps[index].name + '-save-button'"
                    color="secondary"
                    class="ml-2"
                    :loading="loading"
                    elevation="2"
                    width="120px"
                    @click="submit"
                  >
                    {{ $t('_global.save') }}
                  </v-btn>
                  <slot
                    :name="`step.${steps[index].name}.actions.middle`"
                    :step="index + 1"
                  />
                  <v-btn
                    class="secondary-btn"
                    variant="outlined"
                    elevation="2"
                    width="120px"
                    @click="cancel"
                  >
                    {{ $t('_global.cancel') }}
                  </v-btn>
                  <v-btn
                    v-if="currentStep > 1"
                    class="secondary-btn ml-2"
                    variant="outlined"
                    elevation="2"
                    width="120px"
                    @click="currentStep = index"
                  >
                    {{ $t('_global.previous') }}
                  </v-btn>
                  <slot
                    :name="`step.${steps[index].name}.afterActions`"
                    :step="index + 1"
                  />
                </div>
              </v-col>
              <v-col :cols="step.belowDisplay ? 12 : 10" class="pr-0">
                <slot :name="`step.${steps[index].name}`" :step="index + 1" />
              </v-col>
              <v-col
                v-if="!step.belowDisplay"
                cols="2"
                class="d-flex align-start justify-end py-4"
              >
                <div v-if="currentStep === 1">
                  <slot name="actions" />
                </div>
                <div class="mx-2">
                  <v-col v-if="currentStep < steps.length" cols="12">
                    <v-btn
                      :data-cy="steps[index].name + '-continue-button'"
                      color="secondary"
                      :loading="loadingContinue"
                      elevation="2"
                      width="120px"
                      @click="goToStep(index + 1, index + 2)"
                    >
                      {{ $t('_global.continue') }}
                    </v-btn>
                  </v-col>
                  <v-col
                    v-if="currentStep >= steps.length || saveFromAnyStep"
                    cols="12"
                  >
                    <v-btn
                      :data-cy="steps[index].name + '-save-button'"
                      color="secondary"
                      :loading="loading"
                      elevation="2"
                      width="120px"
                      @click="submit"
                    >
                      {{ $t('_global.save') }}
                    </v-btn>
                  </v-col>
                  <v-col cols="12">
                    <v-btn
                      class="secondary-btn"
                      variant="outlined"
                      elevation="2"
                      width="120px"
                      @click="cancel"
                    >
                      {{ $t('_global.cancel') }}
                    </v-btn>
                  </v-col>
                  <v-col v-if="currentStep > 1" cols="12">
                    <v-btn
                      class="secondary-btn"
                      variant="outlined"
                      elevation="2"
                      width="120px"
                      @click="currentStep = index"
                    >
                      {{ $t('_global.previous') }}
                    </v-btn>
                  </v-col>
                  <v-col cols="12">
                    <slot
                      :name="`step.${steps[index].name}.afterActions`"
                      :step="index + 1"
                    />
                  </v-col>
                </div>
              </v-col>
              <slot
                :name="`step.${steps[index].name}.after`"
                :step="index + 1"
              />
            </v-row>
          </v-sheet>
        </template>
      </v-stepper>
    </v-card-text>
    <ConfirmDialog ref="confirm" :text-cols="6" :action-cols="5" />
    <template v-if="debug">
      <div class="debug">
        {{ editData }}
      </div>
    </template>
  </v-card>
</template>

<script setup>
import { computed, nextTick, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import HelpButton from '@/components/tools/HelpButton.vue'
import HelpButtonWithPanels from '@/components/tools/HelpButtonWithPanels.vue'
import ConfirmDialog from '@/components/tools/ConfirmDialog.vue'
import { useFormStore } from '@/stores/form'

const { t } = useI18n()
const props = defineProps({
  title: {
    type: String,
    default: '',
  },
  steps: {
    type: Array,
    default: () => [],
  },
  formObserverGetter: {
    type: Function,
    default: undefined,
  },
  editable: {
    type: Boolean,
    default: false,
  },
  extraStepValidation: {
    type: Function,
    required: false,
    default: undefined,
  },
  helpText: {
    type: String,
    required: false,
    default: '',
  },
  helpItems: {
    type: Array,
    required: false,
    default: null,
  },
  editData: {
    type: Object,
    default: undefined,
  },
  debug: Boolean,
  formUrl: {
    type: String,
    default: '',
  },
  saveFromAnyStep: {
    type: Boolean,
    default: false,
  },
  loadingContinue: {
    type: Boolean,
    default: false,
  },
  resetLoading: {
    type: Number,
    default: 0,
  },
})
const emit = defineEmits(['close', 'change', 'save', 'stepLoaded'])
const formStore = useFormStore()

const currentStep = ref(1)
const loading = ref(false)
const confirm = ref()

const stepTitles = computed(() => {
  return props.steps.map((step) => step.title)
})

watch(currentStep, (value) => {
  emit('change', value)
})
watch(
  () => props.resetLoading,
  () => {
    loading.value = false
  }
)

onMounted(() => {
  formStore.save(props.editData)
  document.addEventListener('keydown', (evt) => {
    if (evt.code === 'Escape') {
      cancel()
    }
  })
})

function copyUrl() {
  navigator.clipboard.writeText(props.formUrl)
}
async function cancel() {
  if (formStore.isEmpty || formStore.isEqual(props.editData)) {
    close()
  } else {
    const options = {
      type: 'warning',
      cancelLabel: t('_global.cancel'),
      agreeLabel: t('_global.continue'),
    }
    if (await confirm.value.open(t('_global.cancel_changes'), options)) {
      close()
    }
  }
}
function close() {
  emit('close')
  formStore.reset()
  reset()
}
function reset() {
  currentStep.value = 1
  props.steps.forEach((item, index) => {
    const observer = props.formObserverGetter(index + 1)
    if (observer !== undefined && observer !== null) {
      observer.reset()
    }
  })
  loading.value = false
}
async function validateStepObserver(step) {
  const observer = props.formObserverGetter(step)
  if (observer !== undefined && observer !== null) {
    const { valid } = await observer.validate()
    return valid
  }
  return true
}
async function goToStep(step, nextStep) {
  if (!(await validateStepObserver(step))) {
    return
  }
  if (props.extraStepValidation) {
    if (!(await props.extraStepValidation(step))) {
      return
    }
  }
  currentStep.value = nextStep
  nextTick(() => {
    emit('stepLoaded', nextStep)
  })
}
async function submit() {
  if (!(await validateStepObserver(currentStep.value))) {
    return
  }
  loading.value = true
  emit('save')
}

defineExpose({
  reset,
  loading,
  close,
})
</script>

<style lang="scss">
.v-stepper-item {
  font-size: large;
  color: rgba(0, 0, 0, 0.6);

  .v-avatar {
    background-color: rgba(0, 0, 0, 0.6) !important;
  }

  &--selected {
    background: rgb(233, 233, 233);
    color: rgb(var(--v-theme-secondary)) !important;

    .v-avatar {
      background-color: rgb(var(--v-theme-secondary)) !important;
    }
  }
}

.debug {
  padding: 1% 10%;
  background: lightgray;
  white-space: pre-wrap;
}
</style>

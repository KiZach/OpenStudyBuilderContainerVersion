<template>
  <SimpleFormDialog
    ref="formRef"
    :title="title"
    :help-items="helpItems"
    :help-text="$t('HelpMessages.units')"
    :open="open"
    @close="cancel"
    @submit="submit"
  >
    <template #body>
      <v-form ref="observer">
        <v-row>
          <v-col>
            <v-select
              v-model="form.library_name"
              :label="$t('_global.library')"
              data-cy="unit-library"
              :items="libraries"
              item-title="name"
              item-value="name"
              density="compact"
              clearable
              :rules="[formRules.required]"
            />
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="12">
            <v-text-field
              v-model="form.name"
              autocomplete="off"
              :label="$t('_global.name')"
              data-cy="unit-name"
              density="compact"
              clearable
              :rules="[formRules.required]"
            />
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="12">
            <v-autocomplete
              v-model="form.ct_units"
              :label="$t('UnitForm.ct_term')"
              data-cy="unit-codelist-term"
              :items="unitTerms"
              item-title="name.sponsor_preferred_name"
              item-value="term_uid"
              single-line
              multiple
              density="compact"
              clearable
              :rules="[formRules.required]"
            />
          </v-col>
        </v-row>
        <v-row>
          <v-col>
            <v-select
              v-model="form.unit_subsets"
              label="Unit Subset"
              data-cy="unit-subset"
              :items="unitSubsets"
              item-title="name.sponsor_preferred_name"
              item-value="term_uid"
              single-line
              multiple
              density="compact"
              clearable
            />
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="6">
            <v-switch
              v-model="form.convertible_unit"
              :label="$t('UnitForm.convertible_unit')"
              data-cy="convertible-unit"
              density="compact"
              color="primary"
            />
            <v-switch
              v-model="form.display_unit"
              :label="$t('UnitForm.display_unit')"
              data-cy="display-unit"
              density="compact"
              color="primary"
            />
            <v-switch
              v-model="form.master_unit"
              :label="$t('UnitForm.master_unit')"
              data-cy="master-unit"
              density="compact"
              color="primary"
            />
            <v-switch
              v-model="form.si_unit"
              :label="$t('UnitForm.si_unit')"
              data-cy="si-unit"
              density="compact"
              color="primary"
            />
            <v-switch
              v-model="form.us_conventional_unit"
              :label="$t('UnitForm.us_unit')"
              data-cy="us-unit"
              density="compact"
              color="primary"
            />
          </v-col>
          <v-col>
            <StudybuilderUCUMField
              v-model="form.ucum"
              :error-messages="errors"
            />
          </v-col>
        </v-row>
        <v-row>
          <v-col>
            <v-autocomplete
              v-model="form.unit_dimension"
              :label="$t('UnitForm.dimension')"
              data-cy="unit-dimension"
              :items="unitDimensions"
              item-title="name.sponsor_preferred_name"
              item-value="term_uid"
              clearable
              density="compact"
            />
          </v-col>
        </v-row>
        <v-row>
          <v-col>
            <v-text-field
              v-model="form.legacy_code"
              :label="$t('UnitForm.legacy_code')"
              data-cy="unit-legacy-code"
              density="compact"
              clearable
            />
          </v-col>
        </v-row>
        <v-row>
          <v-col>
            <v-text-field
              v-model="form.molecular_weight_conv_expon"
              :label="$t('UnitForm.molecular_weight')"
              data-cy="unit-molecular-weight"
              density="compact"
              clearable
            />
          </v-col>
        </v-row>
        <v-row>
          <v-col>
            <v-text-field
              v-model="form.conversion_factor_to_master"
              :label="$t('UnitForm.conversion_factor')"
              data-cy="unit-conversion-factor"
              density="compact"
              clearable
            />
          </v-col>
        </v-row>
        <v-row v-if="editing">
          <v-col>
            <label class="v-label">{{
              $t('UnitForm.reason_for_change')
            }}</label>
            <v-textarea
              v-model="form.change_description"
              density="compact"
              clearable
              auto-grow
              rows="1"
              :rules="[formRules.required]"
            />
          </v-col>
        </v-row>
      </v-form>
    </template>
  </SimpleFormDialog>
</template>

<script setup>
import { computed, inject, onMounted, ref, watch } from 'vue'
import terms from '@/api/controlledTerminology/terms'
import _isEmpty from 'lodash/isEmpty'
import librariesApi from '@/api/libraries'
import SimpleFormDialog from '@/components/tools/SimpleFormDialog.vue'
import StudybuilderUCUMField from '@/components/tools/StudybuilderUCUMField.vue'
import { useUnitsStore } from '@/stores/units'
import { useI18n } from 'vue-i18n'

const eventBusEmit = inject('eventBusEmit')
const formRules = inject('formRules')
const { t } = useI18n()
const formRef = ref()

const props = defineProps({
  unit: {
    type: Object,
    default: null,
  },
  open: Boolean,
})

const emit = defineEmits(['close'])
const unitsStore = useUnitsStore()

const form = ref(getInitialForm())
const helpItems = [
  'UnitForm.ct_term',
  'UnitForm.convertible_unit',
  'UnitForm.display_unit',
  'UnitForm.master_unit',
  'UnitForm.si_unit',
  'UnitForm.us_unit',
  'UnitForm.dimension',
  'UnitForm.legacy_code',
  'UnitForm.add_success',
  'UnitForm.molecular_weight',
  'UnitForm.conversion_factor',
]
const libraries = ref([])
const unitTerms = ref([])
const unitDimensions = ref([])
const unitSubsets = ref([])

const title = computed(() => {
  return props.unit.uid ? t('UnitForm.edit_title') : t('UnitForm.add_title')
})

const editing = computed(() => {
  return !_isEmpty(props.unit)
})

watch(
  () => props.unit,
  (value) => {
    if (Object.keys(value).length !== 0) {
      form.value = JSON.parse(JSON.stringify(value))
      form.value.ct_units = value.ct_units.map((el) => el.term_uid)
      form.value.unit_subsets = value.unit_subsets.map((el) => el.term_uid)
      value.ucum
        ? (form.value.ucum = value.ucum.term_uid)
        : (form.value.ucum = '')
      form.value.unit_dimension = value.unit_dimension.term_uid
    }
  }
)

onMounted(() => {
  terms.getByCodelist('units', true).then((resp) => {
    unitTerms.value = resp.data.items
  })
  terms.getByCodelist('unitDimensions').then((resp) => {
    unitDimensions.value = resp.data.items
  })
  terms.getByCodelist('unitSubsets').then((resp) => {
    unitSubsets.value = resp.data.items
  })
  librariesApi.get(1).then((resp) => {
    libraries.value = resp.data
  })
  if (Object.keys(props.unit).length !== 0) {
    form.value = JSON.parse(JSON.stringify(props.unit))
    form.value.ct_units = props.unit.ct_units.map((el) => el.term_uid)
    form.value.unit_subsets = props.unit.unit_subsets.map((el) => el.term_uid)
    props.unit.ucum
      ? (form.value.ucum = props.unit.ucum.term_uid)
      : (form.value.ucum = '')
    form.value.unit_dimension = props.unit.unit_dimension.term_uid
  }
})

function getInitialForm() {
  return {
    convertible_unit: false,
    display_unit: false,
    master_unit: false,
    si_unit: false,
    us_conventional_unit: false,
  }
}

async function cancel() {
  if (form.value.library_name === undefined) {
    close()
  } else {
    const options = {
      type: 'warning',
      cancelLabel: t('_global.cancel'),
      agreeLabel: t('_global.continue'),
    }
    if (await formRef.value.confirm(t('_global.cancel_changes'), options)) {
      close()
    }
  }
}

function close() {
  emit('close')
  form.value = getInitialForm()
}

async function submit() {
  if (form.value.ucum && form.value.ucum.term_uid) {
    form.value.ucum = form.value.ucum.term_uid
  }
  if (form.value.unit_dimension && form.value.unit_dimension.term_uid) {
    form.value.unit_dimension = form.value.unit_dimension.term_uid
  }
  if (Object.keys(props.unit).length !== 0) {
    try {
      const data = {
        uid: props.unit.uid,
        data: form.value,
      }
      unitsStore.updateUnit(data)
      eventBusEmit('notification', { msg: t('UnitForm.update_success') })
      close()
    } finally {
      formRef.value.working = false
    }
  } else {
    try {
      unitsStore.addUnit(form.value)
      eventBusEmit('notification', { msg: t('UnitForm.add_success') })
      close()
    } finally {
      formRef.value.working = false
    }
  }
}
</script>

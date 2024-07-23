<template>
  <SimpleFormDialog
    :title="$t('SponsorCTPackageForm.title')"
    :open="open"
    @close="close"
    @submit="submit"
  >
    <template #body>
      <v-form ref="formRef">
        <v-row>
          <v-col>
            <v-autocomplete
              v-model="form.extends_package"
              :label="$t('SponsorCTPackageForm.package_label')"
              :items="packages"
              item-title="name"
              item-value="uid"
              :rules="[formRules.required]"
            />
          </v-col>
        </v-row>
      </v-form>
    </template>
  </SimpleFormDialog>
</template>

<script setup>
import { inject, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import controlledTerminology from '@/api/controlledTerminology'
import SimpleFormDialog from '@/components/tools/SimpleFormDialog.vue'

const props = defineProps({
  open: Boolean,
})
const emit = defineEmits(['close'])
const { t } = useI18n()
const eventBusEmit = inject('eventBusEmit')
const formRules = inject('formRules')

const form = ref({})
const formRef = ref()
const packages = ref([])

function close() {
  formRef.value.resetValidation()
  form.value = {}
  emit('close')
}

async function submit() {
  const { valid } = await formRef.value.validate()
  if (!valid) {
    return
  }
  const today = new Date()
  const data = {
    ...form.value,
    effective_date: today.toISOString().split('T')[0],
  }
  controlledTerminology.createSponsorPackage(data).then(() => {
    eventBusEmit('notification', {
      msg: t('SponsorCTPackageForm.creation_success'),
    })
    close()
  })
}

controlledTerminology
  .getPackages({ catalogue_name: 'SDTM CT' })
  .then((resp) => {
    packages.value = resp.data
  })
</script>

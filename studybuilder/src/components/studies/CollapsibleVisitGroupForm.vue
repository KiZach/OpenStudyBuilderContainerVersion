<template>
  <SimpleFormDialog
    ref="form"
    :title="$t('CollapsibleVisitGroupForm.title')"
    :open="open"
    @close="close"
    @submit="submit"
  >
    <template #body>
      <v-alert type="warning" :text="$t('CollapsibleVisitGroupForm.warning')" />
      <v-form ref="observer">
        <v-row>
          <v-col>
            <v-select
              v-model="visitTemplate"
              :items="visits"
              :label="$t('CollapsibleVisitGroupForm.visit_template')"
              item-title="text"
              item-value="refs[0].uid"
              :rules="[formRules.required]"
            />
          </v-col>
        </v-row>
      </v-form>
    </template>
  </SimpleFormDialog>
</template>

<script>
import SimpleFormDialog from '@/components/tools/SimpleFormDialog.vue'
import studyEpochs from '@/api/studyEpochs'
import { useStudiesGeneralStore } from '@/stores/studies-general'

export default {
  components: {
    SimpleFormDialog,
  },
  inject: ['formRules'],
  props: {
    open: Boolean,
    visits: {
      type: Array,
      default: () => [],
    },
  },
  emits: ['close', 'created'],
  setup() {
    const studiesGeneralStore = useStudiesGeneralStore()
    return {
      selectedStudy: studiesGeneralStore.selectedStudy,
    }
  },
  data() {
    return {
      visitTemplate: null,
    }
  },
  methods: {
    close() {
      this.$emit('close')
      this.visitTemplate = null
      this.$refs.observer.reset()
      this.$refs.form.working = false
    },
    async submit() {
      const visitUids = this.visits.map((item) => item.refs[0].uid)
      await studyEpochs.createCollapsibleVisitGroup(
        this.selectedStudy.uid,
        visitUids,
        this.visitTemplate
      )
      this.$emit('created')
      this.close()
    },
  },
}
</script>

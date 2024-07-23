<template>
  <StudyActivitySelectionBaseForm
    ref="baseForm"
    :help-items="helpItems"
    :selection="selection"
    :open="open"
    @close="close"
    @submit="submit"
  >
    <template #body>
      <v-form ref="observer">
        <v-autocomplete
          v-model="selectedVisits"
          :items="studyVisits"
          :label="$t('StudyActivityScheduleBatchEditForm.studyVisits')"
          item-title="visit_short_name"
          return-object
          multiple
          clearable
          :rules="[formRules.required]"
          class="mt-4"
        />
      </v-form>
    </template>
  </StudyActivitySelectionBaseForm>
</template>

<script>
import { computed } from 'vue'
import study from '@/api/study'
import StudyActivitySelectionBaseForm from './StudyActivitySelectionBaseForm.vue'
import studyEpochs from '@/api/studyEpochs'
import { useStudiesGeneralStore } from '@/stores/studies-general'

export default {
  components: {
    StudyActivitySelectionBaseForm,
  },
  inject: ['eventBusEmit', 'formRules'],
  props: {
    selection: {
      type: Array,
      default: () => [],
    },
    currentSelectionMatrix: {
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
  data() {
    return {
      helpItems: [],
      selectedVisits: [],
      studyVisits: [],
    }
  },
  mounted() {
    // Only retrieve ungrouped visits since groups are already used
    // for batch operations...
    const params = {
      page_size: 0,
      filters: {
        consecutive_visit_group: { v: [null], op: 'eq' },
      },
    }
    studyEpochs.getStudyVisits(this.selectedStudy.uid, params).then((resp) => {
      this.studyVisits = resp.data.items
    })
  },
  methods: {
    close() {
      this.$emit('close')
      this.selectedVisits = []
    },
    async submit() {
      const { valid } = await this.$refs.observer.validate()
      if (!valid) {
        return
      }
      this.$refs.baseForm.loading = true
      const data = []
      for (const item of this.selection) {
        // First: delete any existing study activity schedule for the given selection
        for (const cell of Object.values(
          this.currentSelectionMatrix[item.study_activity_uid]
        )) {
          if (cell.uid) {
            cell.value = false
            data.push({
              method: 'DELETE',
              content: { uid: cell.uid },
            })
          }
        }
        // Second: create new activity schedules
        for (const visit of this.selectedVisits) {
          data.push({
            method: 'POST',
            content: {
              study_activity_uid: item.study_activity_uid,
              study_visit_uid: visit.uid,
            },
          })
        }
      }
      study
        .studyActivityScheduleBatchOperations(this.selectedStudy.uid, data)
        .then(
          () => {
            this.eventBusEmit('notification', {
              type: 'success',
              msg: this.$t('DetailedFlowchart.update_success'),
            })
            this.$emit('updated')
            this.close()
            this.$refs.baseForm.loading = false
          },
          () => {
            this.$refs.baseForm.loading = false
          }
        )
    },
  },
}
</script>

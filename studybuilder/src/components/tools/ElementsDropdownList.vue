<template>
  <div>
    <v-row v-if="editMode">
      <v-select
        v-model="element"
        :items="studyElements"
        label="Element"
        item-title="name"
        item-value="element_uid"
        density="compact"
        clearable
        class="mt-6 cellWidth"
        @update:model-value="updateElement"
        @click:clear="deleteElement"
      />
    </v-row>
    <div v-else>
      <v-tooltip bottom>
        <template #activator="{ props }">
          <span v-bind="props">
            <router-link
              v-if="element"
              :to="{
                name: 'StudyElementOverview',
                params: { study_id: selectedStudy.uid, id: element },
              }"
            >
              {{ getElementShortName(element) }}
            </router-link>
            <div v-else>{{ getElementShortName(element) }}</div>
          </span>
        </template>
        <span>{{ getElementName(element) }}</span>
      </v-tooltip>
    </div>
  </div>
</template>
<script>
import { useStudiesGeneralStore } from '@/stores/studies-general'
import { useAccessGuard } from '@/composables/accessGuard'

export default {
  props: {
    epoch: {
      type: String,
      default: '',
    },
    arm: {
      type: String,
      default: '',
    },
    armBranch: {
      type: String,
      default: '',
    },
    studyElements: {
      type: Array,
      default: () => [],
    },
    cells: {
      type: Object,
      default: undefined,
    },
    editMode: Boolean,
    saveObject: {
      type: Boolean,
      default: undefined,
    },
  },
  emits: ['addToObject'],
  setup() {
    const studiesGeneralStore = useStudiesGeneralStore()
    return {
      ...useAccessGuard(),
      selectedStudy: studiesGeneralStore.selectedStudy,
    }
  },
  data() {
    return {
      element: '',
      cell: {},
      data: {},
    }
  },
  watch: {
    saveObject(value) {
      if (value) {
        this.$emit('addToObject', this.data)
        this.data = {}
      }
    },
    cells(value) {
      this.cell = value.data.find(this.findCell)
      if (this.cell) {
        this.element = this.cell.study_element_uid
      }
    },
  },
  mounted() {
    if (this.cells.data) {
      this.cell = this.cells.data.find(this.findCell)
    }
    if (this.cell) {
      this.element = this.cell.study_element_uid
    }
  },
  methods: {
    updateElement() {
      if (this.cell && this.element) {
        this.data = {
          method: 'PATCH',
          content: {
            study_element_uid: this.element,
            study_design_cell_uid: this.cell.design_cell_uid,
          },
        }
        this.armBranch
          ? (this.data.study_branch_arm_uid = this.armBranch)
          : (this.data.study_arm_uid = this.arm)
      } else if (this.element) {
        this.data = {
          method: 'POST',
          content: {
            study_arm_uid: this.arm,
            study_epoch_uid: this.epoch,
            study_element_uid: this.element,
            study_branch_arm_uid: this.armBranch,
          },
        }
      }
    },
    deleteElement() {
      if (this.cell) {
        this.data = {
          method: 'DELETE',
          content: {
            uid: this.cell.design_cell_uid,
          },
        }
        this.cell = undefined
      }
    },
    findCell(cell) {
      return (
        cell.study_epoch_uid === this.epoch &&
        (cell.study_arm_uid
          ? cell.study_arm_uid === this.arm
          : cell.study_branch_arm_uid === this.armBranch)
      )
    },
    getElementShortName(elementUid) {
      const element = this.studyElements.find(
        (el) => el.element_uid === elementUid
      )
      return element ? element.short_name : ''
    },
    getElementName(elementUid) {
      const element = this.studyElements.find(
        (el) => el.element_uid === elementUid
      )
      return element ? element.name : ''
    },
  },
}
</script>
<style scoped>
.cellWidth {
  max-width: 250px;
  min-width: 150px;
}
</style>

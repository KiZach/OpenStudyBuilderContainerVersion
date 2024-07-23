<template>
  <div>
    <p class="text-grey text-subtitle-1 font-weight-bold ml-3">
      {{ $t('DesignMatrix.matrix_guide') }}
    </p>
    <NNTable
      :headers="headers"
      item-value="id"
      :items-length="total"
      disable-filtering
      :items="matrix"
      :loading="loading"
      @filter="fetchStudyArms"
    >
      <template #actions>
        <v-btn
          v-if="!editMode"
          size="small"
          color="primary"
          :title="$t('_global.edit')"
          :disabled="
            !checkPermission($roles.STUDY_WRITE) ||
            selectedStudyVersion !== null
          "
          icon="mdi-pencil-outline"
          @click.stop="edit"
        />
        <v-btn
          v-if="editMode"
          size="small"
          color="primary"
          :title="$t('_global.save')"
          :loading="editLoading"
          @click.stop="save"
        >
          {{ $t('_global.save') }}
        </v-btn>
        <v-btn
          v-if="editMode"
          size="small"
          class="secondary-btn ml-2"
          color="white"
          :title="$t('_global.cancel')"
          @click.stop="cancel"
        >
          {{ $t('_global.cancel') }}
        </v-btn>
      </template>
      <template
        v-for="header in headers"
        :key="header.key"
        #[`item.${header.key}`]="item"
      >
        <td>
          <div v-if="header.key === 'arms'">
            <v-chip
              v-if="item.item.armColor"
              size="small"
              variant="flat"
              density="compact"
              :color="item.item.armColor"
              class="mr-1"
            />
            <router-link
              v-if="item.item.uid"
              :to="{
                name: 'StudyArmOverview',
                params: { study_id: selectedStudy.uid, id: item.item.uid },
              }"
            >
              {{ item.value }}
            </router-link>
            <div v-else>
              {{ item.value }}
            </div>
          </div>
          <div v-else-if="header.key === 'branches'">
            <v-chip
              v-if="item.item.branchColor"
              size="small"
              variant="flat"
              :color="item.item.branchColor"
              class="mr-1"
              density="compact"
            />
            <router-link
              v-if="item.item.id"
              :to="{
                name: 'StudyBranchArmOverview',
                params: { study_id: selectedStudy.uid, id: item.item.id },
              }"
            >
              {{ item.value }}
            </router-link>
            <div v-else>
              {{ item.value }}
            </div>
          </div>
          <ElementsDropdownList
            v-else
            :key="header.key"
            :save-object="saveObject"
            :edit-mode="editMode"
            :cells="cells"
            :study-elements="elements"
            :epoch="header.key"
            :arm="item.item.id ? null : item.item.uid"
            :arm-branch="item.item.id"
            @add-to-object="prepareUpdateObject"
          />
        </td>
      </template>
    </NNTable>
  </div>
</template>

<script>
import arms from '@/api/arms'
import ElementsDropdownList from '@/components/tools/ElementsDropdownList.vue'
import NNTable from '@/components/tools/NNTable.vue'
import visitConstants from '@/constants/visits'
import { useAccessGuard } from '@/composables/accessGuard'
import { useStudiesGeneralStore } from '@/stores/studies-general'
import { useEpochsStore } from '@/stores/studies-epochs'
import { computed } from 'vue'
import filteringParameters from '@/utils/filteringParameters'

export default {
  components: {
    NNTable,
    ElementsDropdownList,
  },
  inject: ['eventBusEmit'],
  props: {
    refresh: {
      type: Number,
      default: 0,
    },
  },
  setup() {
    const studiesGeneralStore = useStudiesGeneralStore()
    const epochsStore = useEpochsStore()
    return {
      ...useAccessGuard(),
      selectedStudy: studiesGeneralStore.selectedStudy,
      selectedStudyVersion: studiesGeneralStore.selectedStudyVersion,
      studyEpochs: computed(() => epochsStore.studyEpochs),
      fetchStudyEpochs: epochsStore.fetchStudyEpochs,
    }
  },
  data() {
    return {
      headers: [
        { title: this.$t('DesignMatrix.study_arm'), key: 'arms' },
        { title: this.$t('DesignMatrix.branches'), key: 'branches' },
      ],
      total: 0,
      arms: [],
      branchArms: {},
      elements: [],
      cells: {},
      matrix: [],
      editMode: false,
      loading: true,
      updateObject: [],
      saveObject: false,
      editLoading: false,
    }
  },
  computed: {
    exportDataUrl() {
      return `studies/${this.selectedStudy.uid}/study-design-cells`
    },
    filteredStudyEpochs() {
      return this.studyEpochs.filter(
        (item) => item.epoch_name !== visitConstants.EPOCH_BASIC
      )
    },
  },
  watch: {
    studyEpochs() {
      this.headers = [
        { title: this.$t('DesignMatrix.study_arm'), key: 'arms' },
        { title: this.$t('DesignMatrix.branches'), key: 'branches' },
      ]
      this.filteredStudyEpochs.forEach((el) =>
        this.headers.push({
          title: el.epoch_name,
          key: el.uid,
          color: el.color_hash,
        })
      )
    },
    refresh() {
      arms.getAllStudyCells(this.selectedStudy.uid).then((resp) => {
        this.cells = resp
        this.fetchStudyArms()
        this.fetchStudyElements()
      })
    },
  },
  async mounted() {
    this.fetchStudyEpochs({ studyUid: this.selectedStudy.uid })
    await this.fetchStudyElements()
    await arms
      .getAllStudyCells(this.selectedStudy.uid)
      .then((resp) => {
        this.cells = resp
      })
  },
  methods: {
    async matrixPushCalls(matrixPushStack) {
      // this method is created to be sure that this.matrix is being pushed in the correct order, so the ElementsDropdownList won't have "Uncaught Promises"
      // we define the method as async
      // await for the sort to then await for each push in the correct order
      this.matrix = []
      // await for the sort
      await matrixPushStack.sort((a, b) => {
        return a.order - b.order
      })
      // await for each push in the correct order
      for (const iMatrix of matrixPushStack) {
        this.matrix.push(iMatrix)
      }
    },
    async fetchStudyArms(filters, options, filtersUpdated) {
      const params = filteringParameters.prepareParameters(
        options,
        filters,
        filtersUpdated
      )
      await arms
        .getAllForStudy(this.selectedStudy.uid, { params })
        .then(async (resp) => {
          this.arms = resp.data.items
          this.total = resp.data.total
          this.matrix = []
          this.branchArms = {}
          for (const el of this.arms) {
            await arms
              .getAllBranchesForArm(
                this.selectedStudy.uid,
                el.arm_uid
              )
              .then((resp) => {
                this.branchArms[el.arm_uid] = resp.data
              })
          }
        })
      this.buildMatrix()
      this.loading = false
    },
    async buildMatrix() {
      const matrixPushStack = []
      for (const el of this.arms) {
        if (this.branchArms[el.arm_uid].length === 0) {
          // making a stack of what has to be pushed in this.matrix
          matrixPushStack.push({
            uid: el.arm_uid,
            arms: el.name,
            armColor: el.arm_colour,
            order: el.order,
          })
        } else {
          this.branchArms[el.arm_uid].forEach((value) => {
            // making a stack of what has to be pushed in this.matrix
            matrixPushStack.push({
              id: value.branch_arm_uid,
              uid: el.arm_uid,
              arms: el.name,
              armColor: value.arm_root.arm_colour,
              branches: value.name,
              branchColor: value.colour_code,
              order: el.order,
            })
          })
        }
      }
      // making this.matrix.push() in the right order
      this.matrixPushCalls(matrixPushStack)
    },
    async fetchStudyElements() {
      const params = {
        page_size: 0,
      }
      return arms
        .getStudyElements(this.selectedStudy.uid, params)
        .then((resp) => {
          this.elements = resp.data.items
        })
    },
    edit() {
      this.editMode = true
    },
    save() {
      this.editLoading = true
      this.saveObject = true
      setTimeout(() => {
        this.updateObject = this.updateObject.filter(
          (el) => Object.keys(el).length !== 0
        )
        arms
          .cellsBatchUpdate(this.selectedStudy.uid, this.updateObject)
          .then(() => {
            this.editLoading = false
            this.editMode = false
            arms
              .getAllStudyCells(this.selectedStudy.uid)
              .then((resp) => {
                this.cells = resp
                this.eventBusEmit('notification', {
                  msg: this.$t('DesignMatrix.matrix_updated'),
                })
                this.editLoading = false
                this.editMode = false
                this.updateObject = []
                this.saveObject = false
              })
          })
      }, 1000)
    },
    prepareUpdateObject(cell) {
      this.updateObject.push(cell)
    },
    cancel() {
      this.editMode = false
      this.buildMatrix()
    },
  },
}
</script>

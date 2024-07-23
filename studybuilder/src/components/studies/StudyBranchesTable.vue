<template>
  <div>
    <NNTable
      :headers="headers"
      item-value="branch_arm_uid"
      :items-length="total"
      :items="branchArms"
      :no-data-text="
        arms.length === 0 ? $t('StudyBranchArms.no_data') : undefined
      "
      :export-data-url="exportDataUrl"
      export-object-label="StudyBranches"
      :history-data-fetcher="fetchBranchArmsHistory"
      :history-title="$t('StudyBranchArms.global_history_title')"
      disable-filtering
      @filter="fetchStudyBranchArms"
    >
      <template #actions="">
        <v-btn
          size="small"
          color="primary"
          :title="$t('StudyBranchArms.add_branch')"
          data-cy="add-study-branch-arm"
          :disabled="
            !checkPermission($roles.STUDY_WRITE) ||
            selectedStudyVersion !== null
          "
          icon="mdi-plus"
          @click.stop="addBranchArm"
        />
      </template>
      <template #[`item.name`]="{ item }">
        <router-link
          :to="{
            name: 'StudyBranchArmOverview',
            params: { study_id: selectedStudy.uid, id: item.branch_arm_uid },
          }"
        >
          {{ item.name }}
        </router-link>
      </template>
      <template #[`item.arm_root.name`]="{ item }">
        <router-link
          :to="{
            name: 'StudyArmOverview',
            params: { study_id: selectedStudy.uid, id: item.arm_root.arm_uid },
          }"
        >
          {{ item.arm_root.name }}
        </router-link>
      </template>
      <template #[`item.colour_code`]="{ item }">
        <v-chip
          :data-cy="'color=' + item.colour_code"
          :color="item.colour_code"
          size="small"
          variant="flat"
        >
          <span>&nbsp;</span>
          <span>&nbsp;</span>
        </v-chip>
      </template>
      <template #[`item.start_date`]="{ item }">
        {{ $filters.date(item.start_date) }}
      </template>
      <template #[`item.actions`]="{ item }">
        <ActionsMenu :actions="actions" :item="item" />
      </template>
    </NNTable>
    <StudyBranchesForm
      :open="showBranchArmsForm"
      :edited-branch-arm="branchArmToEdit"
      :arms="arms"
      @close="closeForm"
    />
    <v-dialog
      v-model="showBranchHistory"
      persistent
      :fullscreen="$globals.historyDialogFullscreen"
      @keydown.esc="closeBranchHistory"
    >
      <HistoryTable
        :title="studyBranchHistoryTitle"
        :headers="headers"
        :items="branchHistoryItems"
        @close="closeBranchHistory"
      />
    </v-dialog>
    <ConfirmDialog ref="confirm" :text-cols="6" :action-cols="5" />
    <SelectionOrderUpdateForm
      v-if="selectedBranch"
      ref="orderForm"
      :initial-value="selectedBranch.order"
      :open="showOrderForm"
      @close="closeOrderForm"
      @submit="submitOrder"
    />
  </div>
</template>

<script>
import NNTable from '@/components/tools/NNTable.vue'
import arms from '@/api/arms'
import StudyBranchesForm from '@/components/studies/StudyBranchesForm.vue'
import ActionsMenu from '@/components/tools/ActionsMenu.vue'
import ConfirmDialog from '@/components/tools/ConfirmDialog.vue'
import studyEpochs from '@/api/studyEpochs'
import { useAccessGuard } from '@/composables/accessGuard'
import HistoryTable from '@/components/tools/HistoryTable.vue'
import { useStudiesGeneralStore } from '@/stores/studies-general'
import filteringParameters from '@/utils/filteringParameters'
import SelectionOrderUpdateForm from '@/components/studies/SelectionOrderUpdateForm.vue'

export default {
  components: {
    NNTable,
    StudyBranchesForm,
    ActionsMenu,
    ConfirmDialog,
    HistoryTable,
    SelectionOrderUpdateForm,
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
    return {
      ...useAccessGuard(),
      selectedStudy: studiesGeneralStore.selectedStudy,
      selectedStudyVersion: studiesGeneralStore.selectedStudyVersion,
    }
  },
  data() {
    return {
      headers: [
        { title: '', key: 'actions', width: '5%' },
        { title: '#', key: 'order', width: '5%' },
        {
          title: this.$t('StudyBranchArms.arm_name'),
          key: 'arm_root.name',
          historyHeader: 'arm_root_uid',
        },
        { title: this.$t('StudyBranchArms.name'), key: 'name' },
        { title: this.$t('StudyBranchArms.short_name'), key: 'short_name' },
        {
          title: this.$t('StudyBranchArms.randomisation_group'),
          key: 'randomization_group',
        },
        { title: this.$t('StudyBranchArms.code'), key: 'code' },
        {
          title: this.$t('StudyBranchArms.number_of_subjects'),
          key: 'number_of_subjects',
        },
        { title: this.$t('StudyBranchArms.description'), key: 'description' },
        { title: this.$t('StudyBranchArms.colour'), key: 'colour_code' },
        { title: this.$t('_global.modified'), key: 'start_date' },
        { title: this.$t('_global.modified_by'), key: 'user_initials' },
      ],
      actions: [
        {
          label: this.$t('_global.edit'),
          icon: 'mdi-pencil-outline',
          iconColor: 'primary',
          condition: () => !this.selectedStudyVersion,
          click: this.editBranchArm,
          accessRole: this.$roles.STUDY_WRITE,
        },
        {
          label: this.$t('_global.change_order'),
          icon: 'mdi-pencil-outline',
          iconColor: 'primary',
          condition: () => !this.selectedStudyVersion,
          click: this.changeOrder,
          accessRole: this.$roles.STUDY_WRITE,
        },
        {
          label: this.$t('_global.delete'),
          icon: 'mdi-delete-outline',
          iconColor: 'error',
          condition: () => !this.selectedStudyVersion,
          click: this.deleteBranchArm,
          accessRole: this.$roles.STUDY_WRITE,
        },
        {
          label: this.$t('_global.history'),
          icon: 'mdi-history',
          click: this.openBranchHistory,
        },
      ],
      total: 0,
      arms: [],
      showBranchArmsForm: false,
      branchArmToEdit: {},
      branchArms: [],
      showBranchHistory: false,
      showOrderForm: false,
      branchHistoryItems: [],
      selectedBranch: null,
      showStudyBranchesHistory: false,
    }
  },
  computed: {
    exportDataUrl() {
      return `studies/${this.selectedStudy.uid}/study-branch-arms`
    },
    studyBranchHistoryTitle() {
      if (this.selectedBranch) {
        return this.$t('StudyBranchArms.study_branch_history_title', {
          branchUid: this.selectedBranch.branch_arm_uid,
        })
      }
      return ''
    },
  },
  watch: {
    refresh() {
      this.fetchStudyArms()
    },
  },
  mounted() {
    this.fetchStudyArms()
  },
  methods: {
    async fetchBranchArmsHistory() {
      const resp = await studyEpochs.getStudyBranchesVersions(
        this.selectedStudy.uid
      )
      return resp.data
    },
    fetchStudyArms() {
      const params = {
        total_count: true,
        page_size: 0,
      }
      arms.getAllForStudy(this.selectedStudy.uid, { params }).then((resp) => {
        this.arms = resp.data.items
      })
    },
    fetchStudyBranchArms(filters, options, filtersUpdated) {
      const params = filteringParameters.prepareParameters(
        options,
        filters,
        filtersUpdated
      )
      params.study_uid = this.selectedStudy.uid
      arms.getAllBranchArms(this.selectedStudy.uid, params).then((resp) => {
        this.branchArms = resp.data
        this.total = resp.data.length
      })
    },
    closeForm() {
      this.branchArmToEdit = {}
      this.showBranchArmsForm = false
      this.fetchStudyBranchArms()
    },
    editBranchArm(item) {
      this.branchArmToEdit = item
      this.showBranchArmsForm = true
    },
    async openBranchHistory(branch) {
      this.selectedBranch = branch
      const resp = await studyEpochs.getStudyBranchVersions(
        this.selectedStudy.uid,
        branch.branch_arm_uid
      )
      this.branchHistoryItems = resp.data
      this.showBranchHistory = true
    },
    closeBranchHistory() {
      this.showBranchHistory = false
      this.selectedBranch = null
    },
    async deleteBranchArm(item) {
      let cellsInBranch = 0
      await arms
        .getAllCellsForBranch(
          this.selectedStudy.uid,
          item.branch_arm_uid
        )
        .then((resp) => {
          cellsInBranch = resp.data.length
        })
      const options = {
        type: 'warning',
        cancelLabel: this.$t('_global.cancel'),
        agreeLabel: this.$t('_global.continue'),
      }
      if (cellsInBranch === 0) {
        arms
          .deleteBranchArm(this.selectedStudy.uid, item.branch_arm_uid)
          .then(() => {
            this.fetchStudyBranchArms()
            this.eventBusEmit('notification', {
              msg: this.$t('StudyBranchArms.branch_deleted'),
            })
          })
      } else if (
        await this.$refs.confirm.open(
          this.$t('StudyBranchArms.branch_delete_notification'),
          options
        )
      ) {
        arms
          .deleteBranchArm(this.selectedStudy.uid, item.branch_arm_uid)
          .then(() => {
            this.fetchStudyBranchArms()
            this.eventBusEmit('notification', {
              msg: this.$t('StudyBranchArms.branch_deleted'),
            })
          })
      }
    },
    async addBranchArm() {
      this.fetchStudyArms()
      if (this.arms.length === 0) {
        const options = {
          type: 'warning',
          cancelLabel: this.$t('_global.cancel'),
          agreeLabel: this.$t('StudyBranchArms.add_arm'),
          redirect: 'arms',
        }
        if (
          !(await this.$refs.confirm.open(
            this.$t('StudyBranchArms.add_arm_message'),
            options
          ))
        ) {
          return
        }
      }
      this.showBranchArmsForm = true
    },
    submitOrder(value) {
      arms
        .updateBranchArmOrder(
          this.selectedBranch.study_uid,
          this.selectedBranch.branch_arm_uid,
          value
        )
        .then(() => {
          this.fetchStudyBranchArms()
          this.closeOrderForm()
          this.eventBusEmit('notification', {
            msg: this.$t('_global.order_updated'),
          })
        })
    },
    changeOrder(studyBranch) {
      this.selectedBranch = studyBranch
      this.showOrderForm = true
    },
    closeOrderForm() {
      this.showOrderForm = false
    },
  },
}
</script>

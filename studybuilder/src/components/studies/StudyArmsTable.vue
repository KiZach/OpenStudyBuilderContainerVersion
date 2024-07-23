<template>
  <div>
    <NNTable
      :headers="headers"
      item-value="arm_uid"
      :items-length="total"
      :export-data-url="exportDataUrl"
      export-object-label="StudyArms"
      :items="arms"
      :column-data-resource="`studies/${selectedStudy.uid}/study-arms`"
      :history-data-fetcher="fetchArmsHistory"
      :history-title="$t('StudyArmsTable.global_history_title')"
      disable-filtering
      @filter="fetchStudyArms"
    >
      <template #[`item.name`]="{ item }">
        <router-link
          :to="{
            name: 'StudyArmOverview',
            params: { study_id: selectedStudy.uid, id: item.arm_uid },
          }"
        >
          {{ item.name }}
        </router-link>
      </template>
      <template #[`item.start_date`]="{ item }">
        {{ $filters.date(item.start_date) }}
      </template>
      <template #[`item.arm_connected_branch_arms`]="{ item }">
        <div v-if="item.arm_connected_branch_arms">
          <router-link
            v-for="branch of item.arm_connected_branch_arms"
            :key="branch.branch_arm_uid"
            :to="{
              name: 'StudyBranchArmOverview',
              params: {
                study_id: selectedStudy.uid,
                id: branch.branch_arm_uid,
              },
            }"
          >
            {{ branch.name }}
          </router-link>
        </div>
      </template>
      <template #[`item.arm_colour`]="{ item }">
        <v-chip :color="item.arm_colour" size="small" variant="flat">
          <span>&nbsp;</span>
          <span>&nbsp;</span>
        </v-chip>
      </template>
      <template #[`item.actions`]="{ item }">
        <ActionsMenu :actions="actions" :item="item" />
      </template>
      <template #actions="">
        <v-btn
          size="small"
          color="primary"
          :title="$t('StudyArmsForm.add_arm')"
          data-cy="add-study-arm"
          :disabled="
            !checkPermission($roles.STUDY_WRITE) ||
            selectedStudyVersion !== null
          "
          icon="mdi-plus"
          @click.stop="showArmsForm = true"
        />
      </template>
    </NNTable>
    <StudyArmsForm
      :open="showArmsForm"
      :edited-arm="armToEdit"
      @close="closeForm"
    />
    <v-dialog
      v-model="showArmHistory"
      persistent
      :fullscreen="$globals.historyDialogFullscreen"
      @keydown.esc="closeArmHistory"
    >
      <HistoryTable
        :title="studyArmHistoryTitle"
        :headers="headers"
        :items="armHistoryItems"
        @close="closeArmHistory"
      />
    </v-dialog>
    <ConfirmDialog ref="confirm" :text-cols="6" :action-cols="5" />
    <SelectionOrderUpdateForm
      v-if="selectedArm"
      ref="orderForm"
      :initial-value="selectedArm.order"
      :open="showOrderForm"
      @close="closeOrderForm"
      @submit="submitOrder"
    />
  </div>
</template>

<script>
import NNTable from '@/components/tools/NNTable.vue'
import arms from '@/api/arms'
import StudyArmsForm from '@/components/studies/StudyArmsForm.vue'
import ActionsMenu from '@/components/tools/ActionsMenu.vue'
import ConfirmDialog from '@/components/tools/ConfirmDialog.vue'
import filteringParameters from '@/utils/filteringParameters'
import studyEpochs from '@/api/studyEpochs'
import HistoryTable from '@/components/tools/HistoryTable.vue'
import SelectionOrderUpdateForm from '@/components/studies/SelectionOrderUpdateForm.vue'
import { useAccessGuard } from '@/composables/accessGuard'
import { useStudiesGeneralStore } from '@/stores/studies-general'

export default {
  components: {
    NNTable,
    StudyArmsForm,
    ActionsMenu,
    HistoryTable,
    ConfirmDialog,
    SelectionOrderUpdateForm,
  },
  inject: ['eventBusEmit'],
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
          title: this.$t('StudyArmsTable.type'),
          key: 'arm_type.sponsor_preferred_name',
          width: '7%',
        },
        { title: this.$t('StudyArmsTable.name'), key: 'name' },
        { title: this.$t('StudyArmsTable.short_name'), key: 'short_name' },
        {
          title: this.$t('StudyArmsTable.randomisation_group'),
          key: 'randomization_group',
        },
        { title: this.$t('StudyArmsTable.code'), key: 'code' },
        {
          title: this.$t('StudyArmsTable.number_of_subjects'),
          key: 'number_of_subjects',
          width: '1%',
        },
        {
          title: this.$t('StudyArmsTable.connected_branches'),
          key: 'arm_connected_branch_arms',
        },
        { title: this.$t('StudyArmsTable.description'), key: 'description' },
        { title: this.$t('StudyBranchArms.colour'), key: 'arm_colour' },
        { title: this.$t('_global.modified'), key: 'start_date' },
        { title: this.$t('_global.modified_by'), key: 'user_initials' },
      ],
      actions: [
        {
          label: this.$t('_global.edit'),
          icon: 'mdi-pencil-outline',
          iconColor: 'primary',
          condition: () => !this.selectedStudyVersion,
          click: this.editArm,
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
          click: this.deleteArm,
          accessRole: this.$roles.STUDY_WRITE,
        },
        {
          label: this.$t('_global.history'),
          icon: 'mdi-history',
          click: this.openArmHistory,
        },
      ],
      total: 0,
      arms: [],
      showArmsForm: false,
      armToEdit: {},
      showArmHistory: false,
      armHistoryItems: [],
      selectedArm: null,
      showStudyArmsHistory: false,
    }
  },
  computed: {
    exportDataUrl() {
      return `studies/${this.selectedStudy.uid}/study-arms`
    },
    studyArmHistoryTitle() {
      if (this.selectedArm) {
        return this.$t('StudyArmsTable.study_arm_history_title', {
          armUid: this.selectedArm.arm_uid,
        })
      }
      return ''
    },
  },
  methods: {
    async fetchArmsHistory() {
      const resp = await studyEpochs.getStudyArmsVersions(
        this.selectedStudy.uid
      )
      return resp.data
    },
    fetchStudyArms(filters, options, filtersUpdated) {
      const params = filteringParameters.prepareParameters(
        options,
        filters,
        filtersUpdated
      )
      params.study_uid = this.selectedStudy.uid
      arms.getAllForStudy(this.selectedStudy.uid, { params }).then((resp) => {
        this.arms = resp.data.items
        this.total = resp.data.total
      })
    },
    closeForm() {
      this.armToEdit = {}
      this.showArmsForm = false
      this.fetchStudyArms()
    },
    editArm(item) {
      this.armToEdit = item
      this.showArmsForm = true
    },
    async openArmHistory(arm) {
      this.selectedArm = arm
      const resp = await studyEpochs.getStudyArmVersions(
        this.selectedStudy.uid,
        arm.arm_uid
      )
      this.armHistoryItems = resp.data
      this.showArmHistory = true
    },
    closeArmHistory() {
      this.showArmHistory = false
      this.selectedArm = null
    },
    async deleteArm(item) {
      let relatedItems = 0
      await arms
        .getAllBranchesForArm(this.selectedStudy.uid, item.arm_uid)
        .then((resp) => {
          relatedItems += resp.data.length
        })
      await arms
        .getAllCohortsForArm(this.selectedStudy.uid, item.arm_uid)
        .then((resp) => {
          relatedItems += resp.data.items.length
        })
      await arms
        .getAllCellsForArm(this.selectedStudy.uid, item.arm_uid)
        .then((resp) => {
          relatedItems += resp.data.length
        })
      const options = {
        type: 'warning',
        cancelLabel: this.$t('_global.cancel'),
        agreeLabel: this.$t('_global.continue'),
      }
      if (relatedItems === 0) {
        arms.delete(this.selectedStudy.uid, item.arm_uid).then(() => {
          this.eventBusEmit('notification', {
            msg: this.$t('StudyArmsTable.arm_deleted'),
          })
          this.fetchStudyArms()
        })
      } else if (
        await this.$refs.confirm.open(
          this.$t('StudyArmsTable.arm_delete_notification'),
          options
        )
      ) {
        arms.delete(this.selectedStudy.uid, item.arm_uid).then(() => {
          this.eventBusEmit('notification', {
            msg: this.$t('StudyArmsTable.arm_deleted'),
          })
          this.fetchStudyArms()
        })
      }
    },
    onChange(event) {
      const arm = event.moved.element
      const newOrder = {
        new_order: event.moved.newIndex + 1,
      }
      arms
        .updateArmOrder(this.selectedStudy.uid, arm.arm_uid, newOrder)
        .then(() => {
          this.fetchStudyArms()
        })
    },
    submitOrder(value) {
      arms
        .updateArmOrder(
          this.selectedArm.study_uid,
          this.selectedArm.arm_uid,
          value
        )
        .then(() => {
          this.fetchStudyArms()
          this.closeOrderForm()
          this.eventBusEmit('notification', {
            msg: this.$t('_global.order_updated'),
          })
        })
    },
    changeOrder(studyArm) {
      this.selectedArm = studyArm
      this.showOrderForm = true
    },
    closeOrderForm() {
      this.showOrderForm = false
    },
  },
}
</script>

<style scoped lang="scss">
table {
  width: max-content;
  text-align: left;
  border-spacing: 0px;
  border-collapse: collapse;
}
thead {
  background-color: #e5e5e5;
  color: rgba(26, 26, 26, 0.6);
}
tr {
  &.section {
    background-color: #e5e5e5;
  }
}
tbody tr {
  border-bottom: 1px solid #e5e5e5;
}
th {
  background-color: #e5e5e5;
  padding: 6px;
  font-size: 14px !important;
}
</style>

<template>
  <div>
    <NNTable
      :headers="headers"
      item-value="cohort_uid"
      :items-length="total"
      :items="cohorts"
      :history-data-fetcher="fetchCohortsHistory"
      :history-title="$t('StudyCohorts.global_history_title')"
      :export-data-url="exportDataUrl"
      export-object-label="StudyCohors"
      disable-filtering
      @filter="fetchStudyCohorts"
    >
      <template #actions="">
        <v-btn
          size="small"
          color="primary"
          :title="$t('StudyCohorts.add_study_cohort')"
          data-cy="add-study-cohort"
          :disabled="
            !checkPermission($roles.STUDY_WRITE) ||
            selectedStudyVersion !== null
          "
          icon="mdi-plus"
          @click.stop="showForm()"
        />
      </template>
      <template #[`item.name`]="{ item }">
        <router-link
          :to="{
            name: 'StudyCohortOverview',
            params: { study_id: selectedStudy.uid, id: item.cohort_uid },
          }"
        >
          {{ item.name }}
        </router-link>
      </template>
      <template #[`item.arm_roots`]="{ item }">
        <router-link
          v-for="arm of item.arm_roots"
          :key="arm.arm_uid"
          :to="{
            name: 'StudyArmOverview',
            params: { study_id: selectedStudy.uid, id: arm.arm_uid },
          }"
        >
          {{ arm.name }}
        </router-link>
      </template>
      <template #[`item.branch_arm_roots`]="{ item }">
        <div v-if="item.branch_arm_roots">
          <router-link
            v-for="branch of item.branch_arm_roots"
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
    <StudyCohortsForm
      :open="form"
      :edited-cohort="cohortToEdit"
      :arms="arms"
      :branches="branches"
      @close="closeForm"
    />
    <v-dialog
      v-model="showCohortHistory"
      persistent
      :fullscreen="$globals.historyDialogFullscreen"
      @keydown.esc="closeCohortHistory"
    >
      <HistoryTable
        :title="studyCohortHistoryTitle"
        :headers="headers"
        :items="cohortHistoryItems"
        @close="closeCohortHistory"
      />
    </v-dialog>
    <ConfirmDialog ref="confirm" :text-cols="6" :action-cols="5" />
    <SelectionOrderUpdateForm
      v-if="selectedCohort"
      ref="orderForm"
      :initial-value="selectedCohort.order"
      :open="showOrderForm"
      @close="closeOrderForm"
      @submit="submitOrder"
    />
  </div>
</template>

<script>
import NNTable from '@/components/tools/NNTable.vue'
import arms from '@/api/arms'
import StudyCohortsForm from '@/components/studies/StudyCohortsForm.vue'
import ActionsMenu from '@/components/tools/ActionsMenu.vue'
import ConfirmDialog from '@/components/tools/ConfirmDialog.vue'
import { useAccessGuard } from '@/composables/accessGuard'
import { useStudiesGeneralStore } from '@/stores/studies-general'
import HistoryTable from '@/components/tools/HistoryTable.vue'
import filteringParameters from '@/utils/filteringParameters'
import SelectionOrderUpdateForm from '@/components/studies/SelectionOrderUpdateForm.vue'

export default {
  components: {
    NNTable,
    StudyCohortsForm,
    ActionsMenu,
    ConfirmDialog,
    HistoryTable,
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
          title: this.$t('StudyCohorts.arm_name'),
          key: 'arm_roots',
          historyHeader: 'arm_roots_uids',
        },
        {
          title: this.$t('StudyCohorts.branch_arm_name'),
          key: 'branch_arm_roots',
          historyHeader: 'branch_arm_roots_uids',
        },
        { title: this.$t('StudyCohorts.cohort_name'), key: 'name' },
        { title: this.$t('StudyCohorts.cohort_short_name'), key: 'short_name' },
        { title: this.$t('StudyCohorts.cohort_code'), key: 'code' },
        {
          title: this.$t('StudyCohorts.number_of_subjects'),
          key: 'number_of_subjects',
        },
        { title: this.$t('_global.description'), key: 'description' },
        { title: this.$t('StudyCohorts.colour'), key: 'colour_code' },
        { title: this.$t('_global.modified'), key: 'start_date' },
        { title: this.$t('_global.modified_by'), key: 'user_initials' },
      ],
      actions: [
        {
          label: this.$t('_global.edit'),
          icon: 'mdi-pencil-outline',
          iconColor: 'primary',
          condition: () => !this.selectedStudyVersion,
          click: this.editCohort,
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
          click: this.deleteCohort,
          accessRole: this.$roles.STUDY_WRITE,
        },
        {
          label: this.$t('_global.history'),
          icon: 'mdi-history',
          click: this.openCohortHistory,
        },
      ],
      total: 0,
      cohorts: [],
      form: false,
      arms: [],
      branches: [],
      cohortToEdit: {},
      showCohortHistory: false,
      showOrderForm: false,
      cohortHistoryItems: [],
      selectedCohort: null,
      showStudyCohortsHistory: false,
    }
  },
  computed: {
    studyCohortHistoryTitle() {
      if (this.selectedCohort) {
        return this.$t('StudyCohorts.study_arm_history_title', {
          cohortUid: this.selectedCohort.cohort_uid,
        })
      }
      return ''
    },
    exportDataUrl() {
      return `studies/${this.selectedStudy.uid}/study-cohorts`
    },
  },
  mounted() {
    this.fetchStudyArmsAndBranches()
  },
  methods: {
    async fetchCohortsHistory() {
      const resp = await arms.getStudyCohortsVersions(this.selectedStudy.uid)
      return resp.data
    },
    fetchStudyArmsAndBranches() {
      const params = {
        total_count: true,
        page_size: 0,
      }
      arms.getAllForStudy(this.selectedStudy.uid, { params }).then((resp) => {
        this.arms = resp.data.items
      })
      arms.getAllBranchArms(this.selectedStudy.uid, params).then((resp) => {
        this.branches = resp.data
      })
    },
    fetchStudyCohorts(filters, options, filtersUpdated) {
      const params = filteringParameters.prepareParameters(
        options,
        filters,
        filtersUpdated
      )
      params.study_uid = this.selectedStudy.uid
      arms.getAllCohorts(this.selectedStudy.uid, params).then((resp) => {
        this.cohorts = resp.data.items
        this.total = resp.data.total
      })
    },
    showForm() {
      this.form = true
    },
    closeForm() {
      this.form = false
      this.cohortToEdit = {}
      this.fetchStudyCohorts()
    },
    editCohort(item) {
      this.cohortToEdit = item
      this.form = true
    },
    async openCohortHistory(cohort) {
      this.selectedCohort = cohort
      const resp = await arms.getStudyCohortVersions(
        this.selectedStudy.uid,
        cohort.cohort_uid
      )
      this.cohortHistoryItems = resp.data
      this.showCohortHistory = true
    },
    closeCohortHistory() {
      this.showCohortHistory = false
      this.selectedCohort = null
    },
    deleteCohort(item) {
      arms.deleteCohort(this.selectedStudy.uid, item.cohort_uid).then(() => {
        this.fetchStudyCohorts()
        this.eventBusEmit('notification', {
          msg: this.$t('StudyCohorts.cohort_deleted'),
        })
      })
    },
    submitOrder(value) {
      arms
        .updateCohortOrder(
          this.selectedCohort.study_uid,
          this.selectedCohort.cohort_uid,
          value
        )
        .then(() => {
          this.fetchStudyCohorts()
          this.closeOrderForm()
          this.eventBusEmit('notification', {
            msg: this.$t('_global.order_updated'),
          })
        })
    },
    changeOrder(studyCohort) {
      this.selectedCohort = studyCohort
      this.showOrderForm = true
    },
    closeOrderForm() {
      this.showOrderForm = false
    },
  },
}
</script>

<template>
  <div class="px-4">
    <div class="page-title d-flex align-center">
      {{ $t('Sidebar.study.study_structure') }} ({{ studyId }})
      <HelpButtonWithPanels
        :help-text="$t('_help.StudyStructure.general')"
        :items="helpItems"
      />
    </div>
    <v-tabs v-model="tab" bg-color="white">
      <v-tab v-for="item of tabs" :key="item.tab" :value="item.tab">
        {{ item.name }}
      </v-tab>
    </v-tabs>
    <v-window v-model="tab" class="bg-white">
      <v-window-item value="overview">
        <StudyStructureOverview :key="key" />
      </v-window-item>
      <v-window-item value="arms">
        <StudyArmsTable />
      </v-window-item>
      <v-window-item value="branches">
        <StudyBranchesTable :refresh="key" />
      </v-window-item>
      <v-window-item value="cohorts">
        <StudyCohortsTable />
      </v-window-item>
      <v-window-item value="epochs">
        <StudyEpochTable />
      </v-window-item>
      <v-window-item value="elements">
        <StudyElementsTable />
      </v-window-item>
      <v-window-item value="visits">
        <StudyVisitTable />
      </v-window-item>
      <v-window-item value="design_matrix">
        <DesignMatrixTable :refresh="key" />
      </v-window-item>
      <v-window-item value="disease_milestones">
        <DiseaseMilestoneTable />
      </v-window-item>
    </v-window>
    <!-- <comment-thread-list :topicPath="topicPath" :isTransparent="true"></comment-thread-list> -->
  </div>
</template>

<script>
import { useRoute } from 'vue-router'
import DesignMatrixTable from '@/components/studies/DesignMatrixTable.vue'
import DiseaseMilestoneTable from '@/components/studies/DiseaseMilestoneTable.vue'
import HelpButtonWithPanels from '@/components/tools/HelpButtonWithPanels.vue'
import StudyEpochTable from '@/components/studies/StudyEpochTable.vue'
import StudyArmsTable from '@/components/studies/StudyArmsTable.vue'
import StudyBranchesTable from '@/components/studies/StudyBranchesTable.vue'
import StudyVisitTable from '@/components/studies/StudyVisitTable.vue'
import StudyElementsTable from '@/components/studies/StudyElementsTable.vue'
import StudyCohortsTable from '@/components/studies/StudyCohortsTable.vue'
import StudyStructureOverview from '@/components/studies/StudyStructureOverview.vue'
// import CommentThreadList from '@/components/tools/CommentThreadList.vue'
import { useStudiesGeneralStore } from '@/stores/studies-general'
import { useAppStore } from '@/stores/app'
import { computed } from 'vue'

export default {
  components: {
    DiseaseMilestoneTable,
    HelpButtonWithPanels,
    StudyVisitTable,
    StudyEpochTable,
    StudyArmsTable,
    DesignMatrixTable,
    StudyElementsTable,
    StudyBranchesTable,
    StudyCohortsTable,
    // CommentThreadList,
    StudyStructureOverview,
  },
  setup() {
    const appStore = useAppStore()
    const studiesGeneralStore = useStudiesGeneralStore()
    const route = useRoute()
    return {
      selectedStudy: computed(() => studiesGeneralStore.selectedStudy),
      studyId: computed(() => studiesGeneralStore.studyId),
      addBreadcrumbsLevel: appStore.addBreadcrumbsLevel,
      route,
    }
  },
  data() {
    return {
      helpItems: [
        'StudyStructure.study_arms',
        'StudyStructure.study_branches',
        'StudyStructure.study_cohorts',
        'StudyStructure.study_epochs',
        'StudyStructure.study_elements',
        'StudyStructure.study_visits',
        'StudyStructure.design_matrix',
        'StudyStructure.edit_visit_tableview',
      ],
      key: 0,
      topicPath: '',
      tab: null,
      tabs: [
        { tab: 'overview', name: this.$t('_global.overview') },
        { tab: 'arms', name: this.$t('Sidebar.study.study_arms') },
        { tab: 'branches', name: this.$t('Sidebar.study.study_branches') },
        { tab: 'cohorts', name: this.$t('Sidebar.study.study_cohorts') },
        { tab: 'epochs', name: this.$t('Sidebar.study.study_epochs') },
        { tab: 'elements', name: this.$t('Sidebar.study.study_elements') },
        { tab: 'visits', name: this.$t('Sidebar.study.study_visits') },
        { tab: 'design_matrix', name: this.$t('Sidebar.study.design_matrix') },
        {
          tab: 'disease_milestones',
          name: this.$t('Sidebar.study.disease_milestones'),
        },
      ],
    }
  },
  watch: {
    tab(newValue) {
      if (newValue !== undefined) {
        this.topicPath =
          '/studies/' + this.selectedStudy.uid + '/study_structure/' + newValue
      }
      if (['overview', 'design_matrix', 'branches'].indexOf(newValue) >= 0)
        this.refresh()
      const tabName = newValue
        ? this.tabs.find((el) => el.tab === newValue).name
        : this.tabs[0].name
      this.$router.push({
        name: 'StudyStructure',
        params: { tab: newValue },
      })
      this.addBreadcrumbsLevel(
        tabName,
        {
          name: 'StudyStructure',
          params: { study_id: this.selectedStudy.uid, tab: tabName },
        },
        3,
        true
      )
    },
    '$route.params.tab'(newValue) {
      this.tab = newValue
    },
  },
  mounted() {
    if (this.route.params.tab) {
      this.tab = this.route.params.tab
    }
    const tabName = this.tab
      ? this.tabs.find((el) => el.tab === this.tab).name
      : this.tabs[0].name
    setTimeout(() => {
      this.addBreadcrumbsLevel(
        tabName,
        {
          name: 'StudyStructure',
          params: { study_id: this.selectedStudy.uid, tab: tabName },
        },
        3,
        true
      )
    }, 100)
  },
  methods: {
    refresh() {
      this.key += 1
    },
  },
}
</script>

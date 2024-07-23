<template>
  <div>
    <NNTable
      :headers="headers"
      item-value="uid"
      export-object-label="Studies"
      :export-data-url="exportDataUrl"
      column-data-resource="studies"
      v-bind="$attrs"
    >
      <template #actions="">
        <v-btn
          v-if="!readOnly"
          data-cy="add-study"
          size="small"
          color="primary"
          :title="$t('StudyForm.add_title')"
          :disabled="!checkPermission($roles.STUDY_WRITE)"
          icon="mdi-plus"
          @click.stop="showForm = true"
        />
      </template>
      <template #[`item.brand_name`]="{ item }">
        {{ getBrandName(item) }}
      </template>
      <template
        #[`item.current_metadata.identification_metadata.study_number`]="{
          item,
        }"
      >
        {{ item.current_metadata.identification_metadata.study_number }}
      </template>
      <template
        #[`item.current_metadata.identification_metadata.study_id`]="{ item }"
      >
        <template v-if="!item.study_parent_part">
          {{ item.current_metadata.identification_metadata.study_id }}
        </template>
        <template v-else>
          {{ item.study_parent_part.study_id }}
        </template>
      </template>
      <template #[`item.sub_study_id`]="{ item }">
        <template v-if="item.study_parent_part">
          {{ item.current_metadata.identification_metadata.study_id }}
        </template>
      </template>
      <template
        #[`item.current_metadata.study_description.study_title`]="{ item }"
      >
        {{
          item.study_parent_part
            ? item.study_parent_part.study_title
            : item.current_metadata.study_description.study_title
        }}
      </template>
      <template
        #[`item.current_metadata.version_metadata.version_timestamp`]="{ item }"
      >
        {{
          $filters.date(
            item.current_metadata.version_metadata.version_timestamp
          )
        }}
      </template>
      <template
        #[`item.current_metadata.version_metadata.locked_version_author`]="{
          item,
        }"
      >
        {{ item.current_metadata.version_metadata.version_author }}
      </template>
      <template #[`item.actions`]="{ item }">
        <v-row>
          <ActionsMenu
            v-if="!readOnly"
            :actions="actions"
            :item="item"
            :badge="actionsMenuBadge(item)"
          />
        </v-row>
      </template>
    </NNTable>
    <StudyForm
      :open="showForm"
      :edited-study="activeStudy"
      @close="closeForm"
    />
  </div>
</template>

<script>
import ActionsMenu from '@/components/tools/ActionsMenu.vue'
import NNTable from '@/components/tools/NNTable.vue'
import StudyForm from '@/components/studies/StudyForm.vue'
import { useAccessGuard } from '@/composables/accessGuard'
import { useStudiesGeneralStore } from '@/stores/studies-general'
import { useStudiesManageStore } from '@/stores/studies-manage'
export default {
  components: {
    ActionsMenu,
    NNTable,
    StudyForm,
  },
  props: {
    readOnly: {
      type: Boolean,
      default: false,
    },
  },
  emits: ['refreshStudies'],
  setup() {
    const accessGuard = useAccessGuard()
    const studiesGeneralStore = useStudiesGeneralStore()
    const studiesManageStore = useStudiesManageStore()

    return {
      studiesGeneralStore,
      studiesManageStore,
      ...accessGuard,
    }
  },
  data() {
    return {
      actions: [
        {
          label: this.$t('StudyTable.select'),
          icon: 'mdi-check-circle-outline',
          iconColor: 'primary',
          condition: (item) =>
            !this.studiesGeneralStore.selectedStudy ||
            this.studiesGeneralStore.selectedStudy.uid !== item.uid,
          click: this.selectStudy,
        },
        {
          label: this.$t('StudyTable.unselect'),
          icon: 'mdi-check-circle',
          iconColor: 'green',
          condition: (item) =>
            this.studiesGeneralStore.selectedStudy &&
            this.studiesGeneralStore.selectedStudy.uid === item.uid,
          click: this.unSelectStudy,
        },
        {
          label: this.$t('_global.edit'),
          icon: 'mdi-pencil-outline',
          iconColor: 'primary',
          condition: (item) =>
            item.current_metadata.version_metadata.study_status === 'DRAFT',
          click: this.editStudy,
          accessRole: this.$roles.STUDY_WRITE,
        },
      ],
      headers: [
        { title: '', key: 'actions' },
        {
          title: this.$t('StudyTable.clinical_programme'),
          key: 'current_metadata.identification_metadata.clinical_programme_name',
        },
        {
          title: this.$t('StudyTable.project_id'),
          key: 'current_metadata.identification_metadata.project_number',
        },
        {
          title: this.$t('StudyTable.project_name'),
          key: 'current_metadata.identification_metadata.project_name',
        },
        { title: this.$t('StudyTable.brand_name'), key: 'brand_name' },
        {
          title: this.$t('StudyTable.number'),
          key: 'current_metadata.identification_metadata.study_number',
        },
        {
          title: this.$t('StudyTable.id'),
          key: 'current_metadata.identification_metadata.study_id',
        },
        {
          title: this.$t('StudyTable.subpart_id'),
          key: 'current_metadata.identification_metadata.subpart_id',
        },
        {
          title: this.$t('StudyTable.sub_study_id'),
          key: 'sub_study_id',
          filteringName: 'current_metadata.identification_metadata.study_id',
        },
        {
          title: this.$t('StudyTable.acronym'),
          key: 'current_metadata.identification_metadata.study_acronym',
        },
        {
          title: this.$t('StudyTable.subpart_acronym'),
          key: 'current_metadata.identification_metadata.study_subpart_acronym',
        },
        {
          title: this.$t('StudyTable.title'),
          key: 'current_metadata.study_description.study_title',
        },
        {
          title: this.$t('_global.status'),
          key: 'current_metadata.version_metadata.study_status',
        },
        {
          title: this.$t('_global.modified'),
          key: 'current_metadata.version_metadata.version_timestamp',
        },
        {
          title: this.$t('_global.modified_by'),
          key: 'current_metadata.version_metadata.locked_version_author',
        },
      ],
      showForm: false,
      activeStudy: null,
    }
  },
  computed: {
    exportDataUrl() {
      let result = '/studies'
      if (this.readOnly) {
        result += '?deleted=true'
      }
      return result
    },
  },
  methods: {
    actionsMenuBadge(item) {
      if (
        this.studiesGeneralStore.selectedStudy &&
        this.studiesGeneralStore.selectedStudy.uid === item.uid
      ) {
        return {
          color: 'green',
          icon: 'mdi-check-circle',
        }
      }
      return undefined
    },
    closeForm() {
      this.showForm = false
      this.activeStudy = null
      this.$emit('refreshStudies')
    },
    selectStudy(study) {
      this.studiesGeneralStore.selectStudy(study, true)
    },
    unSelectStudy() {
      this.studiesGeneralStore.unselectStudy()
      window.location.reload()
    },
    editStudy(study) {
      this.activeStudy = study
      this.showForm = true
    },
    getBrandName(study) {
      const project = this.studiesManageStore.getProjectByNumber(
        study.current_metadata.identification_metadata.project_number
      )
      return project !== undefined ? project.brand_name : ''
    },
  },
}
</script>

<template>
  <div class="px-4">
    <div class="page-title d-flex align-center">
      {{ $t('StudyTitleView.title') }} ({{ studyId }})
      <HelpButtonWithPanels
        :help-text="$t('_help.StudyTitleView.general')"
        :items="helpItems"
      />
    </div>
    <div class="d-flex">
      <v-spacer />
      <v-btn
        class="mb-2"
        size="small"
        color="primary"
        :title="$t('StudyTitleView.edit_title')"
        :data-cy="$t('StudyTitleView.edit_title')"
        :disabled="
          selectedStudyVersion !== null ||
          Boolean(selectedStudy.study_parent_part)
        "
        icon="mdi-pencil-outline"
        @click.stop="showForm = true"
      />
    </div>
    <v-sheet elevation="0" class="pa-4 title" rounded>
      {{ $t('StudyTitleView.title') }}<br />
      <span data-cy="study-title-field" class="text-body-1 mb-3">{{
        description.study_title
      }}</span
      ><br /><br />
      {{ $t('StudyTitleView.short_title') }}<br />
      <span data-cy="study-title-field" class="text-body-1">{{
        description.study_short_title
      }}</span>
    </v-sheet>
    <v-dialog
      v-model="showForm"
      persistent
      fullscreen
      hide-overlay
      @keydown.esc="showForm = false"
    >
      <StudyTitleForm
        :description="description"
        @updated="fetchStudyDescription"
        @close="showForm = false"
      />
    </v-dialog>
    <CommentThreadList
      :topic-path="'/studies/' + selectedStudy.uid + '/study_title'"
      :is-transparent="true"
    />
  </div>
</template>

<script>
import { computed } from 'vue'
import study from '@/api/study'
import StudyTitleForm from '@/components/studies/StudyTitleForm.vue'
import HelpButtonWithPanels from '@/components/tools/HelpButtonWithPanels.vue'
import CommentThreadList from '@/components/tools/CommentThreadList.vue'
import { useStudiesGeneralStore } from '@/stores/studies-general'

export default {
  components: {
    StudyTitleForm,
    HelpButtonWithPanels,
    CommentThreadList,
  },
  setup() {
    const studiesGeneralStore = useStudiesGeneralStore()
    return {
      selectedStudy: computed(() => studiesGeneralStore.selectedStudy),
      selectedStudyVersion: computed(
        () => studiesGeneralStore.selectedStudyVersion
      ),
      studyId: studiesGeneralStore.studyId,
    }
  },
  data() {
    return {
      description: {},
      showForm: false,
      helpItems: ['StudyTitleView.title'],
    }
  },
  mounted() {
    this.fetchStudyDescription()
  },
  methods: {
    fetchStudyDescription() {
      let studyUid = ''
      if (this.selectedStudy.study_parent_part) {
        studyUid = this.selectedStudy.study_parent_part.uid
      } else {
        studyUid = this.selectedStudy.uid
      }
      study
        .getStudyDescriptionMetadata(studyUid)
        .then((resp) => {
          this.description = resp.data.current_metadata.study_description
        })
    },
  },
}
</script>

<style scoped>
.title {
  min-height: 200px !important;
}
</style>

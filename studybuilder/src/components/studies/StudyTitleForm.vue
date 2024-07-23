<template>
  <v-card elevation="0" class="nn-grey">
    <v-card-title class="d-flex align-center">
      <span class="page-title"
        >{{ $t('StudyTitleForm.title') }} ({{ studyId }})</span
      >
      <v-spacer />
      <v-btn class="secondary-btn" color="white" @click="close">
        {{ $t('_global.cancel') }}
      </v-btn>
      <v-btn
        data-cy="save-button"
        color="secondary"
        :loading="working"
        class="ml-3"
        @click="submit"
      >
        {{ $t('_global.save') }}
      </v-btn>
    </v-card-title>
    <v-card-text ref="container" class="mt-4">
      <div class="bg-white pa-4 mb-6">
        <v-form ref="observer">
          <div class="d-flex">
            <label class="v-label">{{
              $t('StudyTitleForm.title_label')
            }}</label>
            <v-spacer />
            <span>{{ currentTitleLength }} / {{ maxTitleLength }}</span>
          </div>
          <v-textarea
            ref="titlearea"
            v-model="form.study_title"
            data-cy="study-title"
            :maxlength="maxTitleLength"
            :hint="$t('StudyTitleForm.title_hint')"
            persistent-hint
            rows="1"
            auto-grow
            :rules="[formRules.required]"
          />
          <div class="d-flex mt-6">
            <label class="v-label">{{
              $t('StudyTitleForm.short_title')
            }}</label>
            <v-spacer />
            <span
              >{{ currentShortTitleLength }} / {{ maxTitleLength / 2 }}</span
            >
          </div>
          <v-textarea
            ref="shorttitlearea"
            v-model="form.study_short_title"
            data-cy="short-study-title"
            :maxlength="maxTitleLength / 2"
            :hint="$t('StudyTitleForm.short_title_hint')"
            persistent-hint
            rows="1"
            auto-grow
            :rules="[formRules.required]"
          />
        </v-form>
      </div>
      <div class="text-grey font-italic mx-4 mb-0">
        {{ $t('StudyTitleForm.global_help') }}
      </div>
      <v-data-table :headers="headers" :items="studies" height="30vh">
        <template #[`item.actions`]="{ item }">
          <v-btn
            data-cy="copy-title"
            icon="mdi-content-copy"
            color="primary"
            :title="$t('StudyTitleForm.copy_title')"
            variant="text"
            @click="copyTitle(item)"
          />
        </template>
      </v-data-table>
    </v-card-text>
    <ConfirmDialog ref="confirm" :text-cols="6" :action-cols="5" />
  </v-card>
</template>

<script>
import { computed } from 'vue'
import study from '@/api/study'
import _isEqual from 'lodash/isEqual'
import ConfirmDialog from '@/components/tools/ConfirmDialog.vue'
import { useStudiesGeneralStore } from '@/stores/studies-general'

export default {
  components: {
    ConfirmDialog,
  },
  inject: ['eventBusEmit', 'formRules'],
  props: {
    description: {
      type: Object,
      default: undefined,
    },
  },
  emits: ['close', 'updated'],
  setup() {
    const studiesGeneralStore = useStudiesGeneralStore()
    return {
      selectedStudy: computed(() => studiesGeneralStore.selectedStudy),
      studyId: studiesGeneralStore.studyId,
    }
  },
  data() {
    return {
      form: {},
      headers: [
        { title: '', key: 'actions', width: '5%' },
        {
          title: this.$t('StudyTitleForm.project_id'),
          key: 'current_metadata.identification_metadata.project_number',
        },
        {
          title: this.$t('StudyTitleForm.project_name'),
          key: 'current_metadata.identification_metadata.project_name',
        },
        {
          title: this.$t('StudyTitleForm.study_id'),
          key: 'current_metadata.identification_metadata.study_id',
        },
        {
          title: this.$t('StudyTitleForm.study_title'),
          key: 'current_metadata.study_description.study_title',
        },
        {
          title: this.$t('StudyTitleForm.short_title'),
          key: 'current_metadata.study_description.study_short_title',
        },
      ],
      maxTitleLength: 600,
      studies: [],
      working: false,
    }
  },
  computed: {
    currentTitleLength() {
      if (this.form.study_title) {
        return this.form.study_title.length
      }
      return 0
    },
    currentShortTitleLength() {
      if (this.form.study_short_title) {
        return this.form.study_short_title.length
      }
      return 0
    },
  },
  watch: {
    description: {
      handler(value) {
        if (value) {
          this.form = JSON.parse(JSON.stringify(value))
        }
      },
      immediate: true,
    },
  },
  mounted() {
    study.getAll().then((resp) => {
      this.studies = resp.data.items
    })
  },
  methods: {
    async close() {
      if (_isEqual(this.form, this.description)) {
        this.$emit('close')
        return
      }
      const options = {
        type: 'warning',
        cancelLabel: this.$t('_global.cancel'),
        agreeLabel: this.$t('_global.continue'),
      }
      if (
        await this.$refs.confirm.open(
          this.$t('_global.cancel_changes'),
          options
        )
      ) {
        this.form = this.description
        this.$emit('close')
      }
    },
    copyTitle(study) {
      this.form.study_title =
        study.current_metadata.study_description.study_title
      this.form.study_short_title =
        study.current_metadata.study_description.study_short_title
    },
    async submit() {
      const { valid } = await this.$refs.observer.validate()
      if (!valid) return
      if (_isEqual(this.form, this.description)) {
        this.eventBusEmit('notification', {
          msg: this.$t('_global.no_changes'),
          type: 'info',
        })
        this.close()
        return
      }
      this.working = true
      try {
        await study.updateStudyDescription(this.selectedStudy.uid, this.form)
        this.$emit('updated')
        this.eventBusEmit('notification', {
          msg: this.$t('StudyTitleForm.update_success'),
        })
        this.$emit('close')
      } finally {
        this.working = false
      }
    },
  },
}
</script>

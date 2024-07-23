<template>
  <v-card bg-color="dfltBackground">
    <v-card-title class="d-flex align-center">
      <span class="dialog-title">{{ $t('StudyActivityEditForm.title') }}</span>
      <HelpButtonWithPanels :title="$t('_global.help')" :items="helpItems" />
    </v-card-title>
    <v-card-text class="mt-4">
      <div class="bg-white pa-4">
        <div class="d-flex">
          <v-text-field
            :label="$t('_global.library')"
            :model-value="library"
            disabled
            variant="filled"
            class="mr-2"
          />
          <v-text-field
            :label="$t('StudyActivity.activity_group')"
            :model-value="activity_group"
            disabled
            variant="filled"
            class="mr-2"
          />
          <v-text-field
            :label="$t('StudyActivity.activity_sub_group')"
            :model-value="activity_subgroup"
            disabled
            variant="filled"
            class="mr-2"
          />
          <v-text-field
            :label="$t('StudyActivity.activity')"
            :model-value="activity"
            disabled
            variant="filled"
          />
        </div>
        <v-form ref="observer">
          <v-autocomplete
            v-model="form.study_soa_group"
            :label="$t('StudyActivityForm.flowchart_group')"
            data-cy="flowchart-group"
            :items="flowchartGroups"
            item-title="name.sponsor_preferred_name"
            return-object
            :rules="[formRules.required]"
            clearable
          />
        </v-form>
      </div>
    </v-card-text>
    <v-card-actions class="pr-6 pb-6">
      <v-spacer />
      <v-btn
        class="secondary-btn"
        variant="outlined"
        elevation="2"
        width="120px"
        @click="close"
      >
        {{ $t('_global.cancel') }}
      </v-btn>
      <v-btn
        color="secondary"
        variant="flat"
        elevation="2"
        width="120px"
        :loading="working"
        @click="submit"
      >
        {{ $t('_global.save') }}
      </v-btn>
    </v-card-actions>
  </v-card>
</template>

<script>
import study from '@/api/study'
import terms from '@/api/controlledTerminology/terms'
import HelpButtonWithPanels from '@/components/tools/HelpButtonWithPanels.vue'

export default {
  components: {
    HelpButtonWithPanels,
  },
  inject: ['eventBusEmit', 'formRules'],
  props: {
    studyActivity: {
      type: Object,
      default: undefined,
    },
  },
  emits: ['close', 'updated'],
  data() {
    return {
      flowchartGroups: [],
      form: {},
      helpItems: [],
      working: false,
    }
  },
  computed: {
    library() {
      return this.studyActivity && this.studyActivity.activity
        ? this.studyActivity.activity.library_name
        : ''
    },
    activity_group() {
      return this.studyActivity &&
        this.studyActivity.study_activity_group &&
        this.studyActivity.study_activity_group.activity_group_name
        ? this.studyActivity.study_activity_group.activity_group_name
        : ''
    },
    activity_subgroup() {
      return this.studyActivity &&
        this.studyActivity.study_activity_subgroup &&
        this.studyActivity.study_activity_subgroup.activity_subgroup_name
        ? this.studyActivity.study_activity_subgroup.activity_subgroup_name
        : ''
    },
    activity() {
      return this.studyActivity ? this.studyActivity.activity.name : ''
    },
  },
  watch: {
    studyActivity: {
      handler(value) {
        if (value) {
          this.form = { ...value }
          this.form.study_soa_group.name = {
            sponsor_preferred_name: this.form.study_soa_group.soa_group_name,
          }
        } else {
          this.form = {}
        }
      },
      immediate: true,
    },
  },
  mounted() {
    terms.getByCodelist('flowchartGroups').then((resp) => {
      this.flowchartGroups = resp.data.items
    })
  },
  methods: {
    close() {
      this.working = false
      this.form = {}
      this.$refs.observer.reset()
      this.$emit('close')
    },
    cancel() {
      this.close()
    },
    async submit() {
      const { valid } = await this.$refs.observer.validate()
      if (!valid) {
        return
      }
      this.working = true
      const data = {
        soa_group_term_uid: this.form.study_soa_group.term_uid,
      }
      study
        .updateStudyActivity(
          this.studyActivity.study_uid,
          this.studyActivity.study_activity_uid,
          data
        )
        .then(
          () => {
            this.eventBusEmit('notification', {
              type: 'success',
              msg: this.$t('StudyActivityEditForm.update_success'),
            })
            this.$emit('updated')
            this.close()
          },
          () => {
            this.working = false
          }
        )
    },
  },
}
</script>

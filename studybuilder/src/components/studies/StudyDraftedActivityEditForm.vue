<template>
  <v-card bg-color="dfltBackground">
    <v-card-title class="d-flex align-center">
      <span class="dialog-title">{{ $t('StudyActivityEditForm.title') }}</span>
      <HelpButtonWithPanels :title="$t('_global.help')" :items="helpItems" />
    </v-card-title>
    <v-card-text class="mt-4">
      <div class="bg-white pa-4">
        <v-form ref="observer">
          <v-row>
            <v-col>
              <v-autocomplete
                v-model="form.soa_group_term_uid"
                :label="$t('StudyActivityForm.flowchart_group')"
                data-cy="flowchart-group"
                :items="flowchartGroups"
                item-title="name.sponsor_preferred_name"
                item-value="term_uid"
                :rules="[formRules.required]"
                :hint="$t('_help.StudyActivityForm.flowchart_group')"
                persistent-hint
                clearable
              />
              <v-autocomplete
                v-model="form.activity_group_uid"
                :label="$t('ActivityForms.activity_group')"
                :items="groups"
                item-title="name"
                item-value="uid"
                density="compact"
                clearable
                @update:model-value="form.activity_subgroup_uid = null"
              />
              <v-autocomplete
                v-model="form.activity_subgroup_uid"
                :label="$t('ActivityForms.activity_subgroup')"
                data-cy="activity-subgroup"
                :items="filteredSubGroups"
                item-title="name"
                item-value="uid"
                density="compact"
                clearable
                :disabled="form.activity_group_uid ? false : true"
              />
              <v-text-field
                v-model="form.activity_name"
                :label="$t('ActivityFormsRequested.name')"
                data-cy="instance-name"
                density="compact"
                clearable
                :rules="[formRules.required]"
              />
              <v-textarea
                v-model="form.request_rationale"
                :label="$t('ActivityFormsRequested.rationale_for_request')"
                data-cy="activity-rationale"
                density="compact"
                clearable
                auto-grow
                rows="1"
                :rules="[formRules.required]"
              />
              <v-row>
                <v-checkbox
                  v-model="form.is_data_collected"
                  class="mt-2 mr-2"
                  :label="$t('ActivityForms.is_data_collected')"
                />
                <v-switch
                  v-model="form.is_request_final"
                  :label="$t('ActivityForms.submit_request')"
                  hide-details
                  color="primary"
                />
              </v-row>
            </v-col>
          </v-row>
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
import activities from '@/api/activities'
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
      form: {},
      groups: [],
      subGroups: [],
      flowchartGroups: [],
    }
  },
  computed: {
    filteredSubGroups() {
      if (!this.form.activity_group_uid) {
        return []
      }
      return this.subGroups.filter(
        (el) =>
          el.activity_groups.find(
            (o) => o.uid === this.form.activity_group_uid
          ) !== undefined
      )
    },
  },
  watch: {
    studyActivity: {
      handler(value) {
        if (value) {
          this.initForm(value)
        } else {
          this.form = {}
        }
      },
      immediate: true,
    },
    filteredSubGroups(value) {
      if (value.length === 1) {
        this.form.activity_subgroup_uid = value[0].uid
      }
    },
  },
  mounted() {
    terms.getByCodelist('flowchartGroups').then((resp) => {
      this.flowchartGroups = resp.data.items
    })
    this.getGroups()
  },
  methods: {
    initForm(activity) {
      this.form = {
        show_activity_in_protocol_flowchart:
          activity.show_activity_in_protocol_flowchart,
        show_activity_subgroup_in_protocol_flowchart:
          activity.show_activity_subgroup_in_protocol_flowchart,
        show_activity_group_in_protocol_flowchart:
          activity.show_activity_group_in_protocol_flowchart,
        show_soa_group_in_protocol_flowchart:
          activity.show_soa_group_in_protocol_flowchart,
        soa_group_term_uid: activity.study_soa_group.soa_group_term_uid,
        activity_group_uid: activity.study_activity_group.activity_group_uid,
        activity_subgroup_uid:
          activity.study_activity_subgroup.activity_subgroup_uid,
        activity_uid: activity.activity.uid,
        activity_name: activity.activity.name,
        request_rationale: activity.activity.request_rationale,
        is_data_collected: activity.activity.is_data_collected,
        is_request_final: activity.activity.is_request_final,
      }
    },
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
      study
        .updateStudyActivityRequest(
          this.studyActivity.study_uid,
          this.studyActivity.study_activity_uid,
          this.form
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
    getGroups() {
      const params = {
        page_size: 0,
        filters: { status: { v: ['Final'], op: 'co' } },
        sort_by: JSON.stringify({ name: true }),
      }
      activities.get(params, 'activity-groups').then((resp) => {
        this.groups = resp.data.items
      })
      activities.get(params, 'activity-sub-groups').then((resp) => {
        this.subGroups = resp.data.items
      })
    },
  },
}
</script>

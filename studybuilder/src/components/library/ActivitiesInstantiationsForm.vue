<template>
  <HorizontalStepperForm
    ref="stepper"
    :title="title"
    :steps="steps"
    :form-observer-getter="getObserver"
    :help-items="helpItems"
    :extra-step-validation="extraValidation"
    @close="cancel"
    @save="submit"
  >
    <template #[`step.activities`]="{ step }">
      <v-form :ref="`observer_${step}`">
        <v-row data-cy="instanceform-activity-class">
          <v-col cols="4">
            <v-autocomplete
              v-model="selectedActivity"
              :rules="[formRules.required]"
              :items="activities"
              :label="$t('ActivityForms.activity')"
              data-cy="instanceform-activity-dropdown"
              item-title="name"
              density="compact"
              clearable
              class="mt-4"
              return-object
              @update:model-value="selectedGroupings = []"
            />
          </v-col>
        </v-row>
        <v-row>
          <v-col>
            <v-data-table
              v-if="selectedActivity"
              v-model="selectedGroupings"
              class="mb-3 pb-3"
              show-select
              :headers="headers"
              item-value="activity_subgroup_uid"
              data-cy="instanceform-activitygroup-table"
              :items="selectedActivity.activity_groupings"
              return-object
            >
              <template #bottom />
            </v-data-table>
          </v-col>
        </v-row>
      </v-form>
      <v-spacer />
    </template>
    <template #[`step.type`]="{ step }">
      <v-form :ref="`observer_${step}`">
        <v-row data-cy="instanceform-instanceclass-class">
          <v-col cols="4">
            <v-select
              v-model="form.activity_instance_class_uid"
              :items="activityInstanceClasses"
              :label="$t('ActivityForms.instance_class')"
              data-cy="instanceform-instanceclass-dropdown"
              item-title="name"
              item-value="uid"
              density="compact"
              clearable
              class="mt-4"
              :rules="[formRules.required]"
            />
          </v-col>
        </v-row>
      </v-form>
    </template>
    <template #[`step.basicData`]="{ step }">
      <v-form :ref="`observer_${step}`">
        <v-row>
          <v-col cols="8">
            <v-text-field
              v-model="form.name"
              :label="$t('ActivityForms.activity_ins_name')"
              data-cy="instanceform-instancename-field"
              :rules="[formRules.required]"
            />
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="8">
            <SentenceCaseNameField
              v-model="form.name_sentence_case"
              :name="form.name"
            />
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="8">
            <v-textarea
              v-model="form.definition"
              :label="$t('ActivityForms.definition')"
              data-cy="instanceform-definition-field"
              auto-grow
              rows="2"
              :rules="[formRules.required]"
            />
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="8">
            <v-text-field
              v-model="form.nci_concept_id"
              :label="$t('ActivityTable.nci_concept_id')"
              data-cy="instanceform-nciconceptid-field"
              density="compact"
              clearable
            />
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="8">
            <v-text-field
              v-model="form.topic_code"
              :label="$t('ActivityForms.topicCode')"
              data-cy="instanceform-topiccode-field"
              :rules="[formRules.required]"
            />
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="8">
            <v-text-field
              v-model="form.adam_param_code"
              :label="$t('ActivityForms.adamCode')"
              data-cy="instanceform-adamcode-field"
              hide-details
            />
          </v-col>
        </v-row>
        <v-row>
          <v-col>
            <v-checkbox
              v-model="form.is_required_for_activity"
              :label="$t('ActivityForms.is_required_for_activity')"
              data-cy="instanceform-requiredforactivity-checkbox"
            />
            <v-checkbox
              v-model="form.is_default_selected_for_activity"
              :label="$t('ActivityForms.is_default_selected_for_activity')"
            />
          </v-col>
          <v-col>
            <v-checkbox
              v-model="form.is_data_sharing"
              :label="$t('ActivityForms.is_data_sharing')"
            />
            <v-checkbox
              v-model="form.is_legacy_usage"
              :label="$t('ActivityForms.is_legacy_usage')"
            />
          </v-col>
        </v-row>
      </v-form>
    </template>
  </HorizontalStepperForm>
  <ConfirmDialog ref="confirm" :text-cols="6" :action-cols="5" />
</template>

<script>
import activityInstanceClasses from '@/api/activityInstanceClasses'
import activities from '@/api/activities'
import ConfirmDialog from '@/components/tools/ConfirmDialog.vue'
import libraries from '@/constants/libraries'
import HorizontalStepperForm from '@/components/tools/HorizontalStepperForm.vue'
import SentenceCaseNameField from '@/components/tools/SentenceCaseNameField.vue'
import { useFormStore } from '@/stores/form'
import statuses from '@/constants/statuses'

const source = 'activity-instances'

export default {
  components: {
    ConfirmDialog,
    HorizontalStepperForm,
    SentenceCaseNameField,
  },
  inject: ['eventBusEmit', 'formRules'],
  props: {
    editedActivity: {
      type: Object,
      default: null,
    },
  },
  emits: ['close'],
  setup() {
    const formStore = useFormStore()
    return {
      formStore,
    }
  },
  data() {
    return {
      form: { activity_groupings: [] },
      type: '',
      activities: [],
      activityInstanceClasses: [],
      steps: this.getInitialSteps(),
      helpItems: [
        'ActivityFormsInstantiations.activities',
        'ActivityFormsInstantiations.activity_group',
        'ActivityFormsInstantiations.select_type',
        'ActivityFormsInstantiations.name',
        'ActivityFormsInstantiations.definition',
        'ActivityFormsInstantiations.nci_concept_id',
        'ActivityFormsInstantiations.topicCode',
        'ActivityFormsInstantiations.adamCode',
        'ActivityFormsInstantiations.is_required_for_activity',
        'ActivityFormsInstantiations.is_default_selected_for_activity',
        'ActivityFormsInstantiations.is_data_sharing',
        'ActivityFormsInstantiations.is_legacy_usage',
      ],
      headers: [
        {
          title: this.$t('ActivityFormsInstantiations.activity_group'),
          key: 'activity_group_name',
        },
        {
          title: this.$t('ActivityFormsInstantiations.activity_subgroup'),
          key: 'activity_subgroup_name',
        },
      ],
      selectedActivity: null,
      selectedGroupings: [],
    }
  },
  computed: {
    title() {
      return this.editedActivity
        ? this.$t('ActivityForms.editInstance')
        : this.$t('ActivityForms.addInstance')
    },
    filteredGroups() {
      if (
        !this.form.activity_groupings ||
        !this.form.activity_groupings[0].activity_uid
      ) {
        return []
      }
      const uid = this.form.activity_groupings[0].activity_uid
      const activity = this.activities.find((o) => o.uid === uid)
      if (!activity) {
        return []
      }
      return activity.activity_groupings.map((o) => ({
        name: o.activity_group_name,
        uid: o.activity_group_uid,
      }))
    },
    filteredSubGroups() {
      if (
        !this.form.activity_groupings ||
        !this.form.activity_groupings[0].activity_group_uid
      ) {
        return []
      }
      const activityUid = this.form.activity_groupings[0].activity_uid
      const groupUid = this.form.activity_groupings[0].activity_group_uid
      const activity = this.activities.find((o) => o.uid === activityUid)
      if (!activity) {
        return []
      }
      return activity.activity_groupings
        .filter((o) => o.activity_group_uid === groupUid)
        .map((o) => ({
          name: o.activity_subgroup_name,
          uid: o.activity_subgroup_uid,
        }))
    },
  },
  watch: {
    activities() {
      if (this.editedActivity) {
        this.setActivityGroupings()
      }
    },
    editedActivity: {
      handler(value) {
        if (value) {
          this.initForm(value)
        }
        if (this.editedActivity && this.activities.length > 0) {
          this.setActivityGroupings()
        }
      },
      immediate: true,
    },
  },
  mounted() {
    if (this.editedActivity) {
      this.initForm(this.editedActivity)
    }
    this.getActivities()
    activityInstanceClasses.getAll({ page_size: 0 }).then((resp) => {
      this.activityInstanceClasses = resp.data.items
    })
  },
  methods: {
    initForm(value) {
      this.form = {
        name: value.name,
        activity_instance_class_uid: value.activity_instance_class.uid,
        name_sentence_case: value.name_sentence_case,
        nci_concept_id: value.nci_concept_id,
        definition: value.definition,
        change_description: value.change_description,
        activity_sub_groups: value.activity_sub_groups,
        topic_code: value.topic_code,
        adam_param_code: value.adam_param_code,
        is_required_for_activity: value.is_required_for_activity,
        is_default_selected_for_activity:
          value.is_default_selected_for_activity,
        is_data_sharing: value.is_data_sharing,
        is_legacy_usage: value.is_legacy_usage,
        activity_groupings: [],
      }
      this.formStore.save(this.form)
    },
    getInitialSteps() {
      return [
        {
          name: 'activities',
          title: this.$t('ActivityForms.select_activities'),
        },
        { name: 'type', title: this.$t('ActivityForms.select_class') },
        { name: 'basicData', title: this.$t('ActivityForms.addBasicData') },
      ]
    },
    async extraValidation(step) {
      if (step !== 1) {
        return true
      }
      if (this.selectedGroupings.length === 0) {
        this.eventBusEmit('notification', {
          msg: this.$t('ActivityForms.grouping_selection_info'),
          type: 'info',
        })
        return false
      }
      return true
    },
    async cancel() {
      if (this.formStore.isEmpty || this.formStore.isEqual(this.form)) {
        this.close()
      } else {
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
          this.close()
        }
      }
    },
    close() {
      this.$emit('close')
      this.form = { activity_groupings: [] }
      this.selectedActivity = null
      this.selectedGroupings = []
      this.formStore.reset()
      this.$refs.stepper.reset()
      this.$refs.stepper.loading = false
    },
    async submit() {
      this.form.library_name = libraries.LIBRARY_SPONSOR
      this.form.activities = [this.form.activities]
      this.selectedGroupings = this.selectedGroupings.filter(function (val) {
        return val !== undefined
      })
      this.selectedGroupings.forEach((grouping) => {
        this.form.activity_groupings.push({
          activity_uid: this.selectedActivity.uid,
          activity_group_uid: grouping.activity_group_uid,
          activity_subgroup_uid: grouping.activity_subgroup_uid,
        })
      })
      if (!this.editedActivity) {
        activities.create(this.form, source).then(
          () => {
            this.eventBusEmit('notification', {
              msg: this.$t('ActivityForms.activity_created'),
            })
            this.close()
          },
          () => {
            this.$refs.stepper.loading = false
          }
        )
      } else {
        activities.update(this.editedActivity.uid, this.form, source).then(
          () => {
            this.eventBusEmit('notification', {
              msg: this.$t('ActivityForms.activity_updated'),
            })
            this.close()
          },
          () => {
            this.$refs.stepper.loading = false
          }
        )
      }
    },
    getObserver(step) {
      return this.$refs[`observer_${step}`]
    },
    getActivities() {
      const params = {
        page_size: 0,
        filters: {
          status: { v: [statuses.FINAL] },
          library_name: { v: [libraries.LIBRARY_SPONSOR] },
        },
      }
      activities.get(params, 'activities').then((resp) => {
        this.activities = resp.data.items
      })
    },
    setActivityGroupings() {
      this.selectedActivity = this.activities.find(
        (act) => act.uid === this.editedActivity.activities[0].uid
      )
      if (this.editedActivity.activity_groupings.length > 0) {
        this.selectedGroupings = []
        this.editedActivity.activity_groupings.forEach((grouping) => {
          this.selectedGroupings.push(
            this.selectedActivity.activity_groupings.find(
              (group) =>
                group.activity_group_uid === grouping.activity_group.uid &&
                group.activity_subgroup_uid === grouping.activity_subgroup.uid
            )
          )
        })
      }
    },
  },
}
</script>

<template>
  <SimpleFormDialog
    ref="form"
    max-width="1000px"
    :title="$t('StudyActivityInstances.edit_add_instance')"
    :open="open"
    @close="close"
    @submit="submit"
  >
    <template #body>
      <v-card elevation="0">
        <v-card-title>
          {{ $t('StudyActivityInstances.activity_selected') }}
        </v-card-title>
        <v-text-field
          :model-value="getActivityPath"
          density="compact"
          readonly
          disabled
        />
        <v-data-table
          v-model="selected"
          :headers="headers"
          :items="instances"
          item-value="uid"
          show-select
          select-strategy="single"
          @filter="getAvailableInstances()"
        >
          <template #bottom />
          <template #[`item.details`]="{ item }">
            <div v-html="item.details" />
          </template>
          <template #[`item.state`]="{ item }">
            <div :class="'px-1 ' + getActivityStateBackground(item)">
              {{ getActivityState(item) }}
            </div>
          </template>
        </v-data-table>
      </v-card>
    </template>
  </SimpleFormDialog>
</template>
<script>
import { computed } from 'vue'
import { useStudiesGeneralStore } from '@/stores/studies-general'
import { useStudyActivitiesStore } from '@/stores/studies-activities'
import SimpleFormDialog from '@/components/tools/SimpleFormDialog.vue'
import activities from '@/api/activities'
import _isEmpty from 'lodash/isEmpty'

export default {
  components: {
    SimpleFormDialog,
  },
  inject: ['eventBusEmit'],
  props: {
    open: Boolean,
    editedActivity: {
      type: Object,
      default: null,
    },
  },
  emits: ['close'],
  setup() {
    const studiesGeneralStore = useStudiesGeneralStore()
    const activitiesStore = useStudyActivitiesStore()

    return {
      selectedStudy: computed(() => studiesGeneralStore.selectedStudy),
      activitiesStore,
    }
  },
  data() {
    return {
      headers: [
        { title: this.$t('StudyActivityInstances.instance'), key: 'name' },
        { title: this.$t('StudyActivityInstances.details'), key: 'details' },
        { title: this.$t('StudyActivityInstances.state'), key: 'state' },
      ],
      instances: [],
      selected: [],
    }
  },
  computed: {
    getActivityPath() {
      if (!_isEmpty(this.editedActivity)) {
        return `${this.editedActivity.study_activity_group.activity_group_name}/${this.editedActivity.study_activity_subgroup.activity_subgroup_name}/${this.editedActivity.activity.name}`
      }
      return ''
    },
  },
  watch: {
    editedActivity() {
      this.getAvailableInstances()
    },
  },
  mounted() {
    this.getAvailableInstances()
  },
  methods: {
    getAvailableInstances() {
      if (!_isEmpty(this.editedActivity)) {
        const params = {
          activity_names: [this.editedActivity.activity.name],
          activity_subgroup_names: [
            this.editedActivity.study_activity_subgroup.activity_subgroup_name,
          ],
          activity_group_names: [
            this.editedActivity.study_activity_group.activity_group_name,
          ],
        }
        activities.get(params, 'activity-instances').then((resp) => {
          this.instances = this.transformInstances(resp.data.items)
          if (this.editedActivity.activity_instance) {
            this.selected.push(
              this.instances.find(
                (instance) =>
                  instance.uid === this.editedActivity.activity_instance.uid
              ).uid
            )
          }
        })
      }
    },
    transformInstances(instances) {
      for (let instance of instances) {
        instance.details = `Class: ${instance.activity_instance_class.name} <br> Topic code: ${instance.topic_code} <br> ADaM param: ${instance.adam_param_code}`
        for (let item of instance.activity_items) {
          if (item.ct_terms.length > 0) {
            instance.details += `<br> ${item.activity_item_class.name}: ${item.ct_terms.map((term) => term.name)}`
          } else {
            instance.details += `<br> ${item.activity_item_class.name}: ${item.unit_definitions.map((unit) => unit.name)}`
          }
        }
      }
      return instances
    },
    getActivityStateBackground(activity) {
      if (activity.is_required_for_activity) {
        return 'mandatory'
      } else if (activity.is_default_selected_for_activity) {
        return 'defaulted'
      }
      if (this.instances.length === 1) {
        return 'suggestion'
      }
    },
    getActivityState(activity) {
      if (activity.is_required_for_activity) {
        return this.$t('StudyActivityInstances.mandatory')
      } else if (activity.is_default_selected_for_activity) {
        return this.$t('StudyActivityInstances.defaulted')
      }
      if (this.instances.length === 1) {
        return this.$t('StudyActivityInstances.suggestion')
      }
    },
    submit() {
      const data = {
        activity_instance_uid: this.selected[0],
        study_activity_uid: this.editedActivity.study_activity_uid,
        show_activity_instance_in_protocol_flowchart:
          this.editedActivity.show_activity_instance_in_protocol_flowchart,
      }
      this.activitiesStore
        .updateStudyActivityInstance(
          this.selectedStudy.uid,
          this.editedActivity.study_activity_instance_uid,
          data
        )
        .then(
          () => {
            this.eventBusEmit('notification', {
              msg: this.$t('StudyActivityInstances.instance_updated'),
              type: 'success',
            })
            this.close()
          },
          () => {
            this.$refs.form.working = false
          }
        )
    },
    close() {
      this.instances = []
      this.selected = []
      this.$emit('close')
    },
  },
}
</script>

<style scoped>
.defaulted {
  background-color: darkseagreen;
  border-radius: 5px;
}
.mandatory {
  background-color: rgb(202, 124, 124);
  border-radius: 5px;
}
.suggestion {
  background-color: rgb(217, 201, 106);
  border-radius: 5px;
}
</style>

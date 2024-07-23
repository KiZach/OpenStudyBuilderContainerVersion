<template>
  <div>
    <SimpleFormDialog
      ref="form"
      :title="title"
      :help-items="helpItems"
      :open="open"
      @close="close"
      @submit="submit"
    >
      <template #body>
        <v-form ref="observer">
          <v-row v-if="subgroup" data-cy="groupform-subgroup-class">
            <v-col>
              <v-autocomplete
                v-model="form.activity_groups"
                :items="groups"
                :label="$t('ActivityForms.groups')"
                data-cy="groupform-activity-group-dropdown"
                item-title="name"
                item-value="uid"
                density="compact"
                clearable
                multiple
                :rules="[formRules.required]"
              />
            </v-col>
          </v-row>
          <v-row data-cy="groupform-activity-group-class">
            <v-col>
              <v-text-field
                v-model="form.name"
                :label="
                  subgroup
                    ? $t('ActivityForms.subgroup_name')
                    : $t('ActivityForms.group_name')
                "
                data-cy="groupform-activity-group-field"
                :rules="[formRules.required]"
              />
            </v-col>
          </v-row>
          <SentenceCaseNameField
            v-model="form.name_sentence_case"
            :name="form.name"
          />
          <v-row>
            <v-col>
              <v-text-field
                v-model="form.abbreviation"
                :label="$t('ActivityForms.abbreviation')"
                data-cy="groupform-abbreviation-field"
              />
            </v-col>
          </v-row>
          <v-row data-cy="groupform-definition-class">
            <v-col>
              <v-textarea
                v-model="form.definition"
                :label="$t('ActivityForms.definition')"
                data-cy="groupform-definition-field"
                auto-grow
                rows="1"
                :rules="[formRules.required]"
              />
            </v-col>
          </v-row>
          <v-row v-if="editing">
            <v-col>
              <v-textarea
                v-model="form.change_description"
                :label="$t('ActivityForms.change_description')"
                data-cy="groupform-change-description-field"
                auto-grow
                rows="1"
                :rules="[formRules.required]"
              />
            </v-col>
          </v-row>
        </v-form>
      </template>
    </SimpleFormDialog>
    <ConfirmDialog ref="confirm" :text-cols="6" :action-cols="5" />
  </div>
</template>

<script>
import ConfirmDialog from '@/components/tools/ConfirmDialog.vue'
import _isEmpty from 'lodash/isEmpty'
import _isEqual from 'lodash/isEqual'
import activities from '@/api/activities'
import SimpleFormDialog from '@/components/tools/SimpleFormDialog.vue'
import SentenceCaseNameField from '@/components/tools/SentenceCaseNameField.vue'
import { useFormStore } from '@/stores/form'

export default {
  components: {
    ConfirmDialog,
    SimpleFormDialog,
    SentenceCaseNameField,
  },
  inject: ['eventBusEmit', 'formRules'],
  props: {
    open: Boolean,
    editedGroupOrSubgroup: {
      type: Object,
      default: null,
    },
    subgroup: Boolean,
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
      form: {},
      steps: [
        { name: 'select', title: this.$t('ActivityForms.select_type') },
        {
          name: 'details',
          title: this.$t('ActivityForms.add_additional_data'),
        },
      ],
      groups: [],
      loading: false,
      editing: false,
      libraries: [],
      helpItems: [
        'ActivityFormsGrouping.name',
        'ActivityFormsGrouping.definition',
      ],
    }
  },
  computed: {
    title() {
      if (!this.subgroup) {
        return !_isEmpty(this.editedGroupOrSubgroup)
          ? this.$t('ActivityForms.edit_group')
          : this.$t('ActivityForms.add_group')
      } else {
        return !_isEmpty(this.editedGroupOrSubgroup)
          ? this.$t('ActivityForms.edit_subgroup')
          : this.$t('ActivityForms.add_subgroup')
      }
    },
  },
  watch: {
    editedGroupOrSubgroup: {
      handler(value) {
        if (!_isEmpty(value)) {
          this.initForm(value)
        }
      },
      immediate: true,
    },
  },
  mounted() {
    if (!_isEmpty(this.editedGroupOrSubgroup)) {
      this.initForm(this.editedGroupOrSubgroup)
    }
    this.getGroups()
  },
  methods: {
    initForm(value) {
      this.editing = true
      this.form = {
        name: value.name,
        name_sentence_case: value.name_sentence_case,
        definition: value.definition,
        change_description: '',
        abbreviation: value.abbreviation,
      }
      if (!_isEmpty(value)) {
        if (value.activity_groups) {
          const uids = []
          for (const item of value.activity_groups) {
            uids.push(item.uid)
          }
          this.form.activity_groups = uids
        }
      }
      this.formStore.save(this.form)
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
      this.form = {}
      this.editing = false
      this.$refs.form.working = false
      this.formStore.reset()
      this.$refs.observer.reset()
    },
    async submit() {
      this.form.library_name = 'Sponsor' // Hardcoded for now at the Sinna and Mikkel request
      if (!this.editedGroupOrSubgroup) {
        if (!this.subgroup) {
          activities.create(this.form, 'activity-groups').then(
            () => {
              this.eventBusEmit('notification', {
                msg: this.$t('ActivityForms.group_created'),
              })
              this.close()
            },
            () => {
              this.$refs.form.working = false
            }
          )
        } else {
          activities.create(this.form, 'activity-sub-groups').then(
            () => {
              this.eventBusEmit('notification', {
                msg: this.$t('ActivityForms.subgroup_created'),
              })
              this.close()
            },
            () => {
              this.$refs.form.working = false
            }
          )
        }
      } else {
        if (!this.subgroup) {
          activities
            .update(
              this.editedGroupOrSubgroup.uid,
              this.form,
              'activity-groups'
            )
            .then(
              () => {
                this.eventBusEmit('notification', {
                  msg: this.$t('ActivityForms.group_updated'),
                })
                this.close()
              },
              () => {
                this.$refs.form.working = false
              }
            )
        } else {
          activities
            .update(
              this.editedGroupOrSubgroup.uid,
              this.form,
              'activity-sub-groups'
            )
            .then(
              () => {
                this.eventBusEmit('notification', {
                  msg: this.$t('ActivityForms.subgroup_updated'),
                })
                this.close()
              },
              () => {
                this.$refs.form.working = false
              }
            )
        }
      }
    },
    checkIfEqual() {
      if (
        _isEqual(
          this.form.change_description,
          this.editedGroupOrSubgroup.change_description
        ) &&
        _isEqual(this.form.definition, this.editedGroupOrSubgroup.definition) &&
        _isEqual(this.form.name, this.editedGroupOrSubgroup.name)
      ) {
        return true
      } else {
        return false
      }
    },
    getGroups() {
      activities
        .get(
          { page_size: 0, filters: { status: { v: ['Final'] } } },
          'activity-groups'
        )
        .then((resp) => {
          this.groups = resp.data.items
        })
    },
  },
}
</script>

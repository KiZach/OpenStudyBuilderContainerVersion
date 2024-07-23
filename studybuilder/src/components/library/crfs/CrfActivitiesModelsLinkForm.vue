<template>
  <SimpleFormDialog
    ref="form"
    :title="title"
    :help-items="helpItems"
    :open="open"
    @close="close"
    @submit="submit"
  >
    <template #body>
      <v-data-table :headers="choosenItemsheaders" :items="choosenItems">
        <template #bottom />
        <template #[`item.delete`]="{ item }">
          <v-btn
            icon="mdi-delete-outline"
            class="mt-1 rightButtons"
            data-cy="remove-item-link"
            size="small"
            variant="text"
            @click="removeItem(item)"
          />
        </template>
      </v-data-table>
      <v-col class="pt-0 mt-0">
        <NNTable
          :headers="availableItemsHeaders"
          item-value="uid"
          :items="items"
          :items-length="total"
          hide-export-button
          hide-default-switches
          additional-margin
          data-cy="test"
          @filter="fetchActivities"
        >
          <template #[`item.add`]="{ item }">
            <v-btn
              icon="mdi-plus"
              class="mt-1 rightButtons"
              data-cy="add-item-link"
              size="small"
              variant="text"
              @click="addItem(item)"
            />
          </template>
        </NNTable>
      </v-col>
    </template>
  </SimpleFormDialog>
</template>

<script>
import SimpleFormDialog from '@/components/tools/SimpleFormDialog.vue'
import crfs from '@/api/crfs'
import NNTable from '@/components/tools/NNTable.vue'
import activities from '@/api/activities'
import filteringParameters from '@/utils/filteringParameters'

export default {
  components: {
    SimpleFormDialog,
    NNTable,
  },
  props: {
    itemToLink: {
      type: Object,
      default: null,
    },
    itemType: {
      type: String,
      default: null,
    },
    open: Boolean,
  },
  emits: ['close'],
  data() {
    return {
      helpItems: [],
      items: [],
      choosenItems: [],
      choosenItemsheaders: [
        { title: this.$t('_global.name'), key: 'name' },
        { title: '', key: 'delete' },
      ],
      availableItemsHeaders: [
        { title: this.$t('_global.name'), key: 'name' },
        { title: '', key: 'add' },
      ],
      total: 0,
      options: {},
    }
  },
  computed: {
    title() {
      if (this.itemType === 'form') {
        return this.$t('CrfLinikingForm.link_activity_groups')
      }
      if (this.itemType === 'itemGroup') {
        return this.$t('CrfLinikingForm.link_activity_sub_groups')
      }
      return this.$t('CrfLinikingForm.link_activities')
    },
  },
  watch: {
    itemToLink(value) {
      if (value) {
        this.fetchActivities()
        this.choosenItems =
          this.itemToLink.activity_groups ||
          this.itemToLink.activity_subgroups ||
          (this.itemToLink.activity ? [this.itemToLink.activity] : [])
      }
    },
    options() {
      this.fetchActivities()
    },
  },
  mounted() {
    this.fetchActivities()
  },
  methods: {
    submit() {
      const data = []
      this.choosenItems.forEach((el) => {
        data.push({ uid: el.uid })
      })
      if (this.itemType === 'form') {
        crfs.addActivityGroupsToForm(data, this.itemToLink.uid).then(() => {
          this.close()
        })
      } else if (this.itemType === 'itemGroup') {
        crfs
          .addActivitySubGroupsToItemGroup(data, this.itemToLink.uid)
          .then(() => {
            this.close()
          })
      } else {
        crfs.addActivitiesToItem(data[0], this.itemToLink.uid).then(() => {
          this.close()
        })
      }
    },
    addItem(item) {
      if (
        !this.choosenItems.some((el) => el.uid === item.uid) &&
        this.choosenItems.length < 1
      ) {
        this.choosenItems.push(item)
      }
    },
    removeItem(item) {
      this.choosenItems = this.choosenItems.filter((el) => el.uid !== item.uid)
    },
    close() {
      this.choosenItems = []
      this.items = []
      this.$emit('close')
    },
    fetchActivities(filters, options, filtersUpdated) {
      const params = filteringParameters.prepareParameters(
        options,
        filters,
        filtersUpdated
      )
      if (this.itemType === 'form') {
        activities.getAllGroups(params).then((resp) => {
          this.items = resp.data.items
          this.total = resp.data.total
        })
      } else if (this.itemType === 'itemGroup') {
        activities.getAllSubGroups(params).then((resp) => {
          this.items = resp.data.items
          this.total = resp.data.total
        })
      } else {
        activities.get(params, 'activities').then((resp) => {
          this.items = resp.data.items
          this.total = resp.data.total
        })
      }
    },
  },
}
</script>
<style scoped>
.rightButtons {
  float: right;
}
</style>

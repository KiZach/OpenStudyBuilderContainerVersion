<template>
  <SimpleFormDialog
    ref="form"
    :title="$t('StudyActivityBatchEditForm.title')"
    :help-items="helpItems"
    :open="open"
    @close="close"
    @submit="$emit('submit')"
  >
    <template #body>
      <p>{{ $t('StudyActivityBatchEditForm.note') }}</p>
      <div class="d-flex align-center">
        <div>
          {{ $t('StudyActivityBatchEditForm.items_selected') }}
          <span class="font-weight-bold">{{ selection.length }}</span>
        </div>
        <div class="ml-10 d-flex align-center">
          {{ $t('StudyActivityBatchEditForm.show_items') }}
          <v-checkbox
            v-model="showItems"
            on-icon="mdi-close-circle-outline"
            off-icon="mdi-dots-horizontal-circle-outline"
            hide-details
            class="ml-2"
          />
        </div>
      </div>
      <v-table v-if="showItems" density="compact" class="mt-4 preview">
        <tbody>
          <tr v-for="item in selection" :key="item.name">
            <td>{{ item.activity.name }}</td>
            <td v-if="withDeleteAction" class="text-right">
              <v-btn
                color="error"
                icon="mdi-close"
                variant="text"
                @click="removeItem(item)"
              />
            </td>
          </tr>
        </tbody>
      </v-table>
      <slot name="body" />
    </template>
  </SimpleFormDialog>
</template>

<script>
import SimpleFormDialog from '@/components/tools/SimpleFormDialog.vue'

export default {
  components: {
    SimpleFormDialog,
  },
  props: {
    helpItems: {
      type: Array,
      default: () => [],
    },
    selection: {
      type: Array,
      default: () => [],
    },
    withDeleteAction: {
      type: Boolean,
      default: false,
    },
    open: Boolean,
  },
  emits: ['close', 'remove', 'submit'],
  data() {
    return {
      showItems: false,
    }
  },
  methods: {
    close() {
      this.showItems = false
      this.$emit('close')
    },
    removeItem(item) {
      this.$emit('remove', item)
    },
  },
}
</script>

<style scoped lang="scss">
.preview {
  max-height: 150px;
  overflow: auto;
}
</style>

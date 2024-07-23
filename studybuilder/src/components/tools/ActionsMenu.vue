<template>
  <v-menu v-if="item && checkActionsPermissions" position="bottom">
    <template #activator="{ props }">
      <div>
        <v-btn
          v-if="!badge"
          data-cy="table-item-action-button"
          icon="mdi-dots-vertical"
          variant="plain"
          v-bind="props"
          class="pb-3"
        />
        <v-badge v-else :color="badge.color" :icon="badge.icon" bordered inline>
          <v-btn
            icon="mdi-dots-vertical"
            v-bind="props"
            class="pb-3"
            variant="text"
          />
        </v-badge>
      </div>
    </template>
    <v-list>
      <template v-for="(action, index) in actions">
        <v-list-item
          v-if="action.condition === undefined || action.condition(item)"
          :key="index"
          :disabled="
            action.accessRole && !accessGuard.checkPermission(action.accessRole)
          "
          @click="action.click(item, source)"
        >
          <template #prepend>
            <v-icon
              v-if="action.iconColor"
              :color="action.iconColor"
              :icon="action.icon"
            />
            <v-icon
              v-else-if="action.iconColorFunc"
              :color="action.iconColorFunc(item)"
              :icon="action.icon"
            />
            <v-icon v-else :icon="action.icon" />
          </template>
          <v-list-item-title :data-cy="action.label">
            {{ action.label }}
          </v-list-item-title>
        </v-list-item>
      </template>
    </v-list>
  </v-menu>
</template>

<script setup>
import { computed } from 'vue'
import { useAccessGuard } from '@/composables/accessGuard'

const accessGuard = useAccessGuard()
const props = defineProps({
  actions: {
    type: Array,
    default: () => [],
  },
  item: {
    type: Object,
    default: undefined,
  },
  source: {
    type: String,
    default: '',
  },
  badge: {
    type: Object,
    required: false,
    default: undefined,
  },
  accessRole: {
    type: String,
    default: '',
  },
})

const checkActionsPermissions = computed(() => {
  return props.accessRole ? accessGuard.checkPermission(props.accessRole) : true
})
</script>

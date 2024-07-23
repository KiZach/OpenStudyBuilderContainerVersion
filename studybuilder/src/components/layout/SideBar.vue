<!-- eslint-disable vue/v-bind-style -->
<template>
  <v-navigation-drawer
    :key="drawerRefreshKey"
    v-model="appStore.drawer"
    :rail="mini"
    :expand-on-hover="mini"
    color="primary"
    width="290"
    @transitionend="transitionEnd"
  >
    <template #prepend="">
      <v-btn
        class="mt-1 ml-2"
        :icon="menuExpandedIcon"
        data-cy="toggle-sidebar"
        color="primary"
        size="small"
        @click="toggleMenu"
      />
    </template>
    <v-list
      v-if="appStore.menuItems"
      v-model:opened="open"
      density="compact"
      color="primary"
    >
      <template v-for="(item, pos) in selectedItems" :key="pos">
        <v-list-item
          v-if="!item.children"
          v-bind:key="item.title"
          :data-cy="item.title"
          color="white"
          link
          :disabled="item.disabled && item.disabled()"
          :value="item.url.name"
          :to="item.url"
          @click="(event) => onMenuItemClick(event, item)"
        >
          <template v-if="item.icon" #prepend>
            <v-icon :icon="item.icon" />
          </template>

          <v-list-item-title>{{ item.title }}</v-list-item-title>
        </v-list-item>
        <v-list-group
          v-else
          v-bind:key="item"
          color="white"
          :data-cy="item.title"
          :prepend-icon="item.icon"
          :value="item.id"
        >
          <template #activator="{ props }">
            <v-list-item v-bind="props" :title="item.title" />
          </template>

          <v-list-item
            v-for="subitem in item.children"
            :key="subitem.title"
            class="submenu-item"
            color="white"
            :data-cy="subitem.title"
            :disabled="subitem.disabled && subitem.disabled()"
            link
            :value="subitem.url.name"
            :to="subitem.url"
            @click="(event) => onMenuItemClick(event, item, subitem)"
          >
            <template v-if="subitem.icon" #preprend>
              <v-icon :icon="subitem.icon" />
            </template>
            <v-list-item-title>{{ subitem.title }}</v-list-item-title>
          </v-list-item>
        </v-list-group>
      </template>
    </v-list>
    <RedirectHandler :target="target" />
  </v-navigation-drawer>
</template>

<script>
import { useAppStore } from '@/stores/app'
import { useStudiesGeneralStore } from '@/stores/studies-general'
import RedirectHandler from '@/components/tools/RedirectHandler.vue'

export default {
  components: {
    RedirectHandler,
  },
  setup() {
    const appStore = useAppStore()
    const studiesGeneralStore = useStudiesGeneralStore()

    return {
      selectedStudy: studiesGeneralStore.selectedStudy,
      appStore,
    }
  },
  data() {
    return {
      drawerRefreshKey: 1,
      nextUrl: null,
      refreshNeeded: false,
      mini: false,
      showSelectForm: false,
      studyId: '',
      target: {},
      open: [],
    }
  },
  computed: {
    menuExpandedIcon() {
      return this.mini ? 'mdi-chevron-double-right' : 'mdi-chevron-double-left'
    },
    selectedItems() {
      if (
        this.appStore.section &&
        Object.prototype.hasOwnProperty.call(
          this.appStore.menuItems,
          this.appStore.section
        )
      ) {
        return this.appStore.menuItems[this.appStore.section].items
      }
      return []
    },
    secondBreadcrumbsLevel() {
      return this.appStore.getBreadcrumbsLevel(1)
    },
  },
  watch: {
    selected: function (val) {
      if (val) {
        this.studyId = val.uid
      } else {
        this.studyId = null
      }
    },
  },
  mounted() {
    this.studyId = this.appStore.studyUid
    if (JSON.parse(localStorage.getItem('narrowMenu')) === true) {
      this.mini = true
    }
    this.selected = this.selectedStudy
  },
  methods: {
    onMenuItemClick(event, item, subitem) {
      // Here we only update target, the actual redirection will be
      // done by the RedirectHandler component
      event.preventDefault()
      this.target = { subitem, item }
    },
    toggleMenu() {
      this.mini = !this.mini
      this.refreshNeeded = true
      localStorage.setItem('narrowMenu', JSON.stringify(this.mini))
    },
    transitionEnd() {
      if (this.refreshNeeded) {
        this.drawerRefreshKey += 1
        this.refreshNeeded = false
      }
    },
  },
}
</script>

<style scoped lang="scss">
.top-logo {
  height: 64px;
  cursor: pointer;
}
.submenu-item {
  background-color: rgb(var(--v-theme-nnLightBlue1));
}
.v-list-item {
  &--active {
    background-color: rgb(var(--v-theme-nnLightBlue2)) !important;
    &::before {
      opacity: 0 !important;
    }
    .v-list-item-title {
      font-weight: 700 !important;
    }
  }
}
</style>

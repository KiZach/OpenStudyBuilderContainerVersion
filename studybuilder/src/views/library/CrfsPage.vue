<template>
  <div class="px-4">
    <div class="d-flex page-title">
      {{ $t('CrfsView.title') }}
      <HelpButton
        :title="$t('_global.definition')"
        :help-text="$t('HelpMessages.crfs')"
      />
    </div>
    <v-tabs v-model="tab" bg-color="white">
      <v-tab v-for="item of tabs" :key="item.tab" :value="item.tab">
        <v-icon
          v-if="item.icon"
          :color="item.iconColor"
          class="mr-1"
          :icon="item.icon"
        />{{ item.name }}
      </v-tab>
    </v-tabs>
    <v-window v-model="tab" class="bg-white">
      <v-window-item value="templates">
        <CrfTemplateTable
          :element-prop="{ uid: uid, type: type, tab: tab }"
          @clear-uid="clearUid"
        />
      </v-window-item>
      <v-window-item value="forms">
        <CrfFormTable
          :element-prop="{ uid: uid, type: type, tab: tab }"
          @clear-uid="clearUid"
          @update-form="updateElement"
        />
      </v-window-item>
      <v-window-item value="item-groups">
        <CrfItemGroupTable
          :element-prop="{ uid: uid, type: type, tab: tab }"
          @clear-uid="clearUid"
          @update-item-group="updateElement"
        />
      </v-window-item>
      <v-window-item value="items">
        <CrfItemTable
          :element-prop="{ uid: uid, type: type, tab: tab }"
          @clear-uid="clearUid"
          @update-item="updateElement"
        />
      </v-window-item>
      <v-window-item value="crf-tree">
        <CrfTreeMain @redirect-to-page="redirectToPage" />
      </v-window-item>
      <v-window-item value="odm-viewer">
        <OdmViewer :element-prop="uid" :refresh="tab" @clear-uid="clearUid" />
      </v-window-item>
      <v-window-item value="alias">
        <CrfAliasTable />
      </v-window-item>
      <v-window-item value="extensions">
        <CrfExtensionsTable />
      </v-window-item>
    </v-window>
  </div>
</template>

<script>
import { useRoute } from 'vue-router'
import { useAppStore } from '@/stores/app'
import HelpButton from '@/components/tools/HelpButton.vue'
import CrfTemplateTable from '@/components/library/crfs/CrfTemplateTable.vue'
import CrfFormTable from '@/components/library/crfs/CrfFormTable.vue'
import CrfItemGroupTable from '@/components/library/crfs/CrfItemGroupTable.vue'
import CrfItemTable from '@/components/library/crfs/CrfItemTable.vue'
import CrfTreeMain from '@/components/library/crfs/crfTreeComponents/CrfTreeMain.vue'
import OdmViewer from '@/components/library/crfs/OdmViewer.vue'
import CrfAliasTable from '@/components/library/crfs/CrfAliasTable.vue'
import CrfExtensionsTable from '@/components/library/crfs/CrfExtensionsTable.vue'

export default {
  components: {
    HelpButton,
    CrfTemplateTable,
    CrfFormTable,
    CrfItemGroupTable,
    CrfItemTable,
    CrfTreeMain,
    OdmViewer,
    CrfAliasTable,
    CrfExtensionsTable,
  },
  setup() {
    const appStore = useAppStore()
    const route = useRoute()
    return {
      addBreadcrumbsLevel: appStore.addBreadcrumbsLevel,
      route,
    }
  },
  data() {
    return {
      tab: null,
      type: '',
      uid: '',
      updatedElement: {},
      tabs: [
        {
          tab: 'templates',
          name: this.$t('CrfsView.tab1_title'),
          icon: 'mdi-alpha-t-circle-outline',
          iconColor: 'crfTemplate',
        },
        {
          tab: 'forms',
          name: this.$t('CrfsView.tab2_title'),
          icon: 'mdi-alpha-f-circle-outline',
          iconColor: 'crfForm',
        },
        {
          tab: 'item-groups',
          name: this.$t('CrfsView.tab3_title'),
          icon: 'mdi-alpha-g-circle-outline',
          iconColor: 'crfGroup',
        },
        {
          tab: 'items',
          name: this.$t('CrfsView.tab4_title'),
          icon: 'mdi-alpha-i-circle-outline',
          iconColor: 'crfItem',
        },
        { tab: 'crf-tree', name: this.$t('CrfsView.tab5_title') },
        { tab: 'odm-viewer', name: this.$t('CrfsView.tab6_title') },
        { tab: 'alias', name: this.$t('CrfsView.tab7_title') },
        { tab: 'extensions', name: this.$t('CrfsView.tab8_title') },
      ],
    }
  },
  watch: {
    tab(newValue) {
      const tab = newValue || this.tabs[0].tab
      const params = { tab: tab }
      if (this.uid && this.type) {
        params.type = this.type
        params.uid = this.uid
      }
      this.$router.push({
        name: 'Crfs',
        params: params,
      })
      const tabName = this.tabs.find((el) => el.tab === tab).name
      this.addBreadcrumbsLevel(
        tabName,
        { name: 'Crfs', params: { tab } },
        3,
        true
      )
    },
    'route.params.tab'(newValue) {
      this.tab = newValue
    },
  },
  mounted() {
    if (this.route.params.tab) {
      this.tab = this.route.params.tab
    }
    this.type = this.route.params.type
    this.uid = this.route.params.uid
  },
  methods: {
    redirectToPage(data) {
      this.uid = data.uid
      this.type = data.type
      this.tab = data.tab
    },
    clearUid() {
      this.uid = null
      this.type = null
    },
    updateElement(element) {
      this.updatedElement = element
    },
  },
}
</script>

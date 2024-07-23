<template>
  <div class="px-4">
    <div class="page-title d-flex align-center">
      {{ $t('FootnoteTemplatesView.title') }}
      <HelpButton :help-text="$t('_help.FootnotesTemplatesTable.general')" />
    </div>
    <v-tabs v-model="tab" bg-color="white">
      <v-tab
        v-for="type in footnoteTypes"
        :key="type.term_uid"
        :value="type.name.sponsor_preferred_name"
      >
        {{ type.name.sponsor_preferred_name }}
      </v-tab>
    </v-tabs>
    <v-window v-model="tab">
      <v-window-item
        v-for="type in footnoteTypes"
        :key="type.term_uid"
        :value="type.name.sponsor_preferred_name"
      >
        <FootnoteTemplateTable :key="type.term_uid" :footnote-type="type" />
      </v-window-item>
    </v-window>
  </div>
</template>

<script>
import FootnoteTemplateTable from '@/components/library/FootnoteTemplateTable.vue'
import HelpButton from '@/components/tools/HelpButton.vue'
import terms from '@/api/controlledTerminology/terms'
import { useAppStore } from '@/stores/app'

export default {
  components: {
    FootnoteTemplateTable,
    HelpButton,
  },
  setup() {
    const appStore = useAppStore()
    return {
      appStore,
    }
  },
  data() {
    return {
      footnoteTypes: [],
      tab: null,
    }
  },
  watch: {
    tab(newValue) {
      const params = { ...this.$route.params }
      params.type = newValue
      this.$router.push({
        name: 'FootnoteTemplates',
        params,
      })
      this.appStore.addBreadcrumbsLevel(newValue, undefined, 3, true)
    },
    '$route.params.type'(newValue) {
      this.tab = newValue
    },
  },
  mounted() {
    terms.getByCodelist('footnoteTypes').then((resp) => {
      this.footnoteTypes = resp.data.items
      this.tab = this.footnoteTypes[0].name.sponsor_preferred_name
      setTimeout(() => {
        this.appStore.addBreadcrumbsLevel(this.tab, undefined, 3, true)
      }, 100)
    })
  },
}
</script>

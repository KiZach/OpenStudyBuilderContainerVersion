<template>
  <div class="px-4">
    <div class="page-title">
      {{ $t('CodelistTermsView.codelist') }} {{ $route.params.codelist_id }} -
      {{ codelistAttributes.submission_value }} /
      {{ $t('CodelistTermDetail.term_detail') }} ({{
        $t('CodelistTermDetail.concept_id')
      }}: {{ $route.params.term_id }})
    </div>
    <CodelistTermDetail
      :codelist-uid="$route.params.codelist_id"
      :term-uid="$route.params.term_id"
    />
  </div>
</template>

<script>
import controlledTerminology from '@/api/controlledTerminology'
import CodelistTermDetail from '@/components/library/CodelistTermDetail.vue'
import { useAppStore } from '@/stores/app'

export default {
  components: {
    CodelistTermDetail,
  },
  setup() {
    const appStore = useAppStore()
    return {
      addBreadcrumbsLevel: appStore.addBreadcrumbsLevel,
    }
  },
  data() {
    return {
      codelistAttributes: {},
    }
  },
  mounted() {
    this.addBreadcrumbsLevel(this.$route.params.term_id, undefined, 6)
    controlledTerminology
      .getCodelistAttributes(this.$route.params.codelist_id)
      .then((resp) => {
        this.codelistAttributes = resp.data
      })
  },
}
</script>

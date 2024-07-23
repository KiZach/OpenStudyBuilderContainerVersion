<template>
  <div class="px-4">
    <div class="d-flex page-title">
      {{ compound.name }}
    </div>
    <CompoundOverview :compound="compound" />
  </div>
</template>

<script>
import CompoundOverview from '@/components/library/CompoundOverview.vue'
import compounds from '@/api/concepts/compounds'
import { useAppStore } from '@/stores/app'

export default {
  components: {
    CompoundOverview,
  },
  setup() {
    const appStore = useAppStore()
    return {
      addBreadcrumbsLevel: appStore.addBreadcrumbsLevel,
    }
  },
  data() {
    return {
      compound: {},
    }
  },
  created() {
    compounds.getObject(this.$route.params.id).then((resp) => {
      this.compound = resp.data
      this.addBreadcrumbsLevel(
        this.compound.name,
        { name: 'CompoundOverview', params: this.$route.params },
        4
      )
    })
  },
}
</script>

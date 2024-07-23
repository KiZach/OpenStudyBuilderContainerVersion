<template>
  <a :href="termBrowserUrl" target="_blank"> {{ conceptId }} </a>
</template>

<script>
export default {
  props: {
    conceptId: {
      type: String,
      default: '',
    },
  },
  computed: {
    termBrowserUrl() {
      return (
        'https://ncit.nci.nih.gov/ncitbrowser/ConceptReport.jsp?code=' +
        this.conceptId
      )
    },
  },
}
</script>

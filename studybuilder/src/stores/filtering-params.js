import { defineStore } from 'pinia'

export const useFilteringParamsStore = defineStore('filteringParams', {
  state: () => ({
    filteringParams: {},
  }),

  actions: {
    initiateFilteringParams() {
      let filtersFromLocalStorage = {}
      if (localStorage.getItem('filteringParams') != null) {
        filtersFromLocalStorage = JSON.parse(
          localStorage.getItem('filteringParams')
        )
      }
      this.filteringParams = filtersFromLocalStorage
    },
    setFilteringParams(params) {
      this.filteringParams = params
      localStorage.setItem(
        'filteringParams',
        JSON.stringify(this.filteringParams)
      )
    },
  },
})

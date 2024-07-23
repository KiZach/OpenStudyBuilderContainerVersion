import { defineStore } from 'pinia'
import dictionaries from '@/api/dictionaries'

export const useCompoundsStore = defineStore('compounds', {
  state: () => ({
    substances: [],
  }),

  actions: {
    fetchSubstances() {
      return dictionaries.getSubstances().then((resp) => {
        this.substances = resp.data.items
      })
    },
  },
})

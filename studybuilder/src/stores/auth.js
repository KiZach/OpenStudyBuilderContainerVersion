import { defineStore } from 'pinia'

import { auth } from '@/plugins/auth'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    userInfo: null,
    displayWelcomeMsg: false,
  }),

  actions: {
    initialize() {
      auth.getUserInfo().then((userInfo) => {
        this.userInfo = userInfo
      })
    },
    setWelcomeMsgFlag(value) {
      this.displayWelcomeMsg = value
    },
  },
})

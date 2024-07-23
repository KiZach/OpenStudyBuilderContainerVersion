import { createApp } from 'vue'
import { createPinia } from 'pinia'

import App from './App.vue'
import router from './router'

// Plugins
import appInsights from '@/plugins/appInsights'
import auth from '@/plugins/auth'
import eventBus from '@/plugins/eventBus'
import formRules from '@/plugins/formRules'
import i18n from '@/plugins/i18n'
import vuetify from '@/plugins/vuetify'

// Filters
import filters from '@/filters'

let globalConfig

/*
 * Convert some string values to more appropriate ones
 */
function prepareConfig(config) {
  const trueValues = ['1', 't', 'true', 'on', 'y', 'yes']
  for (const field of ['OAUTH_ENABLED', 'APPINSIGHTS_DISABLE']) {
    const currentValue = config[field].toLowerCase()
    config[field] = trueValues.indexOf(currentValue) !== -1
  }
}

fetch('/config.json').then((resp) => {
  resp.json().then((config) => {
    const app = createApp(App)
    prepareConfig(config)
    globalConfig = config
    app.config.globalProperties.$config = config
    app.config.globalProperties.$filters = filters
    app.config.globalProperties.$globals = {
      historyDialogMaxWidth: '1600px',
      historyDialogFullscreen: true,
    }
    app.provide('$config', config)
    app.use(createPinia())
    app.use(router)
    app.use(auth, { config })
    app.use(appInsights, {
      config,
      router,
      trackAppErrors: true,
      cloudRole: 'frontend',
      cloudRoleInstance: 'vue-app',
    })
    app.use(eventBus)
    app.use(formRules)
    app.use(i18n).provide('$i18n', i18n)
    app.use(vuetify)
    app.mount('#app')
  })
})

export const useGlobalConfig = () => globalConfig

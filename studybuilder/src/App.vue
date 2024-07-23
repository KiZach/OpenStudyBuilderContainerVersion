<template>
  <v-app full-height>
    <TopBar
      :hide-app-bar-nav-icon="layoutTemplate === 'empty'"
      @back-to-root="navigateToRoot"
    />

    <template v-if="layoutTemplate === 'empty'">
      <v-main class="bg-primary white-text">
        <router-view />
      </v-main>
    </template>

    <template v-else-if="layoutTemplate === 'error'">
      <v-main class="">
        <router-view />
      </v-main>
    </template>

    <template v-else>
      <SideBar />

      <v-main class="bg-dfltBackground">
        <v-container class="" fluid>
          <v-breadcrumbs :items="breadcrumbs" class="mb-2" />
          <router-view />
        </v-container>
      </v-main>
    </template>

    <v-snackbar
      v-model="snackbar"
      :color="notificationColor"
      :timeout="notificationTimeout"
      :min-width="550"
      location="top"
    >
      <v-row>
        <v-col cols="1">
          <v-icon
            color="white"
            class="mr-2"
            size="large"
            :icon="notificationIcon"
          />
        </v-col>
        <v-col cols="10">
          <div class="text-body-1 text-white mt-1">
            {{ notification }}
            <template v-if="correlationId">
              <p />
              <p class="text-body-2">
                <span class="font-weight-bold">{{
                  $t('_global.correlation_id')
                }}</span
                ><br />
                {{ correlationId }}
              </p>
            </template>
          </div>
        </v-col>
        <v-col cols="1">
          <v-btn
            color="white"
            size="small"
            icon="mdi-close"
            variant="text"
            @click="snackbar = false"
          />
        </v-col>
      </v-row>
    </v-snackbar>
  </v-app>
</template>
<script>
import { computed } from 'vue'
import { useAppStore } from '@/stores/app'
import { useAuthStore } from '@/stores/auth'
import SideBar from '@/components/layout/SideBar.vue'
import TopBar from '@/components/layout/TopBar.vue'
import { eventBus } from '@/plugins/eventBus'

export default {
  name: 'App',

  components: {
    SideBar,
    TopBar,
  },
  setup() {
    const appStore = useAppStore()
    const authStore = useAuthStore()

    return {
      breadcrumbs: computed(() => appStore.breadcrumbs),
      section: computed(() => appStore.section),
      userData: computed(() => appStore.userData),
      userInfo: computed(() => authStore.userInfo),
      displayWelcomeMsg: computed(() => authStore.displayWelcomeMsg),
      appStore,
      authStore,
    }
  },

  data: () => ({
    snackbar: false,
    correlationId: null,
    notification: '',
    notificationColor: null,
    notificationTimeout: -1,
    defaultNotificationTimeout: 3000,
  }),

  computed: {
    layoutTemplate() {
      return this.$route.meta.layoutTemplate || '2cols'
    },
    notificationIcon() {
      if (
        this.notificationColor === 'green' ||
        this.notificationColor === 'success'
      ) {
        return 'mdi-check-circle-outline'
      }
      if (this.notificationColor === 'info') {
        return 'mdi-information-outline'
      }
      if (this.notificationColor === 'warning') {
        return 'mdi-alert-outline'
      }
      if (
        this.notificationColor === 'error' ||
        this.notificationColor === '#E6553F'
      ) {
        return 'mdi-alert-octagon-outline'
      }
      return ''
    },
  },
  watch: {
    userInfo(newValue) {
      if (this.displayWelcomeMsg) {
        this.showNotification({
          msg: this.$t('_global.auth_success', { username: newValue.name }),
        })
        this.authStore.setWelcomeMsgFlag(false)
      }
    },
  },

  created() {
    this.$watch(
      () => eventBus.value.get('notification'),
      (args) => this.showNotification(...args)
    )
    this.$watch(
      () => eventBus.value.get('userSignedIn'),
      () => {
        this.authStore.initialize()
        this.authStore.setWelcomeMsgFlag(true)
      }
    )
    this.$watch(
      () => eventBus.value.get('backToRoot'),
      () => {
        this.appStore.resetBreadcrumbs()
        this.appStore.setSection('')
        this.$router.push('/')
      }
    )
  },

  mounted() {
    this.appStore.initialize()
    this.$vuetify.theme.dark = this.userData.darkTheme
    this.authStore.initialize()
  },

  methods: {
    navigateToRoot() {
      this.appStore.resetBreadcrumbs()
      this.appStore.setSection('')
      this.$router.push('/')
    },
    showNotification(options) {
      this.notification = options.msg
      if (options.type) {
        this.notificationColor =
          options.type === 'error' ? '#E6553F' : options.type
      } else {
        this.notificationColor = 'green'
      }
      this.notificationTimeout = options.timeout
        ? options.timeout
        : this.defaultNotificationTimeout
      this.correlationId = options.correlationId
      this.snackbar = true
      if (options.type === 'error') {
        console.log(options.msg)
        if (options.correlationId) {
          console.log(`Correlation ID: ${options.correlationId}`)
        }
      }
    },
  },
}
</script>

<style lang="scss" scoped>
.v-breadcrumbs {
  padding-top: 5px;
  padding-bottom: 5px;
  padding-left: 12px;
}
.v-container {
  position: relative;
  height: 100%;
}
</style>

import { inject } from 'vue'
import { useAuthStore } from '@/stores/auth'

export function useAccessGuard() {
  const authStore = useAuthStore()

  function checkPermission(permission) {
    const $config = inject('$config')
    if ($config.OAUTH_ENABLED) {
      return authStore.userInfo.roles.includes(permission)
    }
    return true
  }

  return {
    userInfo: authStore.userInfo,
    checkPermission,
  }
}

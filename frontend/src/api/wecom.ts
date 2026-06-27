import { getData } from './client'

declare global {
  interface Window {
    ww?: {
      register: (config: Record<string, unknown>) => void
      invoke: (name: string, payload: Record<string, unknown>, callback: (res: Record<string, unknown>) => void) => void
    }
  }
}

export async function getCurrentExternalContact(): Promise<string> {
  const devExternalId = import.meta.env.VITE_DEV_EXTERNAL_USERID
  if (!window.ww || devExternalId) {
    return devExternalId || 'external-dev-001'
  }

  const config = await getData<Record<string, unknown>>('/api/wecom/js-config', { url: window.location.href.split('#')[0] })
  window.ww.register({
    ...config,
    jsApiList: ['getCurExternalContact']
  })

  return new Promise((resolve, reject) => {
    window.ww?.invoke('getCurExternalContact', {}, (res) => {
      const externalUserId = String(res.userId || res.externalUserId || '')
      if (externalUserId) {
        resolve(externalUserId)
      } else {
        reject(new Error('无法获取当前客户'))
      }
    })
  })
}

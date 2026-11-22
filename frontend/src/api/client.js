import { useAuth0 } from '@auth0/auth0-react'
import { useCallback } from 'react'

export function useRequest() {
  const { getAccessTokenSilently } = useAuth0()
  return useCallback(async (path, options = {}) => {
    const token = await getAccessTokenSilently({
      authorizationParams: {
        audience: import.meta.env.VITE_AUTH0_AUDIENCE,
        scope: 'read:expenses write:expenses',
      },
    })
    const headers = new Headers(options.headers)
    headers.set('Authorization', `Bearer ${token}`)
    const response = await fetch(path, { ...options, headers })
    const result = await response.json()
    if (!response.ok) {
      const detail = result.detail
      throw new Error(Array.isArray(detail) ? detail.map((item) => item.msg.replace(/^Value error, /, '')).join(' ') : detail || 'Something went wrong.')
    }
    return result
  }, [getAccessTokenSilently])
}

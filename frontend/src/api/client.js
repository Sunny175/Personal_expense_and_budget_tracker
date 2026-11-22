export async function request(path, options) {
  const response = await fetch(path, options)
  const result = await response.json()
  if (!response.ok) {
    const detail = result.detail
    throw new Error(Array.isArray(detail) ? detail.map((item) => item.msg.replace(/^Value error, /, '')).join(' ') : detail || 'Something went wrong.')
  }
  return result
}

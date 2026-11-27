const BASE = '/api/v1'
export const getToken = () => localStorage.getItem('token')
export const getRole = () => localStorage.getItem('role')

export async function api(path, { method = 'GET', body } = {}) {
  const res = await fetch(BASE + path, {
    method,
    headers: { 'Content-Type': 'application/json', ...(getToken() && { Authorization: `Bearer ${getToken()}` }) },
    body: body && JSON.stringify(body),
  })
  if (!res.ok) throw Object.assign(new Error((await res.json().catch(() => ({}))).detail || res.statusText), { status: res.status })
  return res.json()
}

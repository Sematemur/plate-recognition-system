const API_BASE = '/api'

export async function recognizeImage(file) {
  const formData = new FormData()
  formData.append('image', file)
  const response = await fetch(`${API_BASE}/recognize`, {
    method: 'POST',
    body: formData,
  })
  const data = await response.json()
  if (!response.ok) {
    return { error: data.error || 'unknown_error', detail: data.detail }
  }
  return data
}

export async function registerVehicle(vehicleData) {
  const response = await fetch(`${API_BASE}/vehicles`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(vehicleData),
  })
  if (!response.ok) throw new Error('Failed to register vehicle')
  return response.json()
}

export async function updateVehicle(vehicleId, data) {
  const response = await fetch(`${API_BASE}/vehicles/${vehicleId}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  })
  if (!response.ok) throw new Error('Failed to update vehicle')
  return response.json()
}

export async function confirmLog(logId, plateConfirmed) {
  const response = await fetch(`${API_BASE}/logs/${logId}/confirm`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ plate_confirmed: plateConfirmed }),
  })
  if (!response.ok) throw new Error('Failed to confirm log')
  return response.json()
}

export async function fetchLogs(skip = 0, limit = 50) {
  const response = await fetch(`${API_BASE}/logs?skip=${skip}&limit=${limit}`)
  const data = await response.json()
  return data.items || data
}

export async function fetchVehicles(skip = 0, limit = 50) {
  const response = await fetch(`${API_BASE}/vehicles?skip=${skip}&limit=${limit}`)
  const data = await response.json()
  return data.items || data
}

export function createFeedSocket(onMessage) {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  const ws = new WebSocket(`${protocol}//${window.location.host}/ws/feed`)

  ws.onmessage = (event) => {
    const data = JSON.parse(event.data)
    onMessage(data)
  }

  return {
    start: (interval = 3) => ws.send(JSON.stringify({ command: 'start_feed', interval_seconds: interval })),
    pause: () => ws.send(JSON.stringify({ command: 'pause_feed' })),
    resume: () => ws.send(JSON.stringify({ command: 'resume_feed' })),
    close: () => ws.close(),
  }
}

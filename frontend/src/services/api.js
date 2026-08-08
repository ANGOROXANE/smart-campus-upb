const API_URL = "/api";

async function request(endpoint, options = {}) {
  const response = await fetch(`${API_URL}${endpoint}`, {
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
    ...options,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail || `Erreur HTTP ${response.status}`);
  }

  return response.json();
}

export const api = {
  getRooms: () => request("/rooms"),

  getSensors: () => request("/sensors"),

  getLatestMeasurements: (limit = 10) =>
    request(`/measurements/latest?limit=${limit}`),

  getMeasurementHistory: (start = "-24h", room = null, sensor = null) => {
    const params = new URLSearchParams({ start });

    if (room) params.append("room", room);
    if (sensor) params.append("sensor", sensor);

    return request(`/measurements/history?${params.toString()}`);
  },
};
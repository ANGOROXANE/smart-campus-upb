import api from "./api";

export const getLatestMeasurements = async (limit = 10) => {
  const response = await api.get("/measurements/latest", {
    params: { limit },
  });

  return response.data;
};

export const getMeasurementHistory = async ({
  start = "-24h",
  room,
  sensor,
} = {}) => {
  const response = await api.get("/measurements/history", {
    params: {
      start,
      ...(room && { room }),
      ...(sensor && { sensor }),
    },
  });

  return response.data;
};
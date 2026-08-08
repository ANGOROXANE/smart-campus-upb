import api from "./api";

export const getSensors = async () => {
  const response = await api.get("/sensors");
  return response.data;
};

export const createSensor = async (sensor) => {
  const response = await api.post("/sensors", sensor);
  return response.data;
};
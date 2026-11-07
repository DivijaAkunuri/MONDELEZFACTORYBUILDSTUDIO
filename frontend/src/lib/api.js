
import axios from "axios";

const BACKEND_URL =
  process.env.REACT_APP_BACKEND_URL ||
  "https://constructionestimator-3iti.onrender.com";

export const API = `${BACKEND_URL}/api`;

export const api = axios.create({
  baseURL: API,
  timeout: 60000,
});

export async function getReference() {
  const { data } = await api.get("/estimator/reference");
  return data;
}

export async function calculate(inputs) {
  const { data } = await api.post("/estimator/calculate", inputs);
  return data;
}

export async function calculateFast(inputs) {
  const { data } = await api.post("/estimator/calculate-fast", inputs);
  return data;
}

export async function getInsights(inputs, result) {
  const { data } = await api.post("/estimator/insights", {
    inputs,
    result,
  });
  return data;
}

export async function saveEstimate(inputs, result) {
  const { data } = await api.post("/estimator/save", {
    inputs,
    result,
  });
  return data;
}

export async function lookupLocation(city) {
  const { data } = await api.get("/estimator/location-lookup", {
    params: { city },
  });
  return data;
}

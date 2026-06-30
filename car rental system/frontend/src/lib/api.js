import axios from 'react';
import axiosInstance from 'axios';

const api = axiosInstance.create({
  baseURL: 'http://localhost:8000',
  headers: {
    'Content-Type': 'application/json',
  },
});

export const getVehicles = async () => {
  const response = await api.get('/vehicles/');
  return response.data;
};

export const getDashboardStats = async () => {
  const response = await api.get('/dashboard/stats');
  return response.data;
};

export default api;

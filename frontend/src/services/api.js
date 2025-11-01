import axios from 'axios';

const API_URL = import.meta.env.DEV 
  ? '/api' 
  : import.meta.env.VITE_API_URL || 'http://localhost:3000';

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

api.interceptors.request.use((config) => {
  const userId = window.Telegram?.WebApp?.initDataUnsafe?.user?.id;
  if (userId) {
    config.headers['X-User-ID'] = userId;
  }
  return config;
});

export const userAPI = {
  register: (userData) => api.post('/users/register', userData),
  getOrders: (userId) => api.get(`/users/${userId}/orders/`),
};

export const itemsAPI = {
  getAll: () => api.get('/items/'),
};

export const categoriesAPI = {
  getAll: () => api.get('/categories/'),
};

export const basketAPI = {
  get: (userId) => api.post(`/basket/${userId}`),
  addItem: (userId, itemData) => api.post(`/basket/${userId}/items`, itemData),
  removeItem: (userId, itemId) => api.delete(`/basket/${userId}/items/${itemId}`),
};

export const ordersAPI = {
  createFromBasket: (userId, orderData) => api.post(`/orders/from_basket/${userId}`, orderData),
  updateStatus: (orderId, statusData) => api.patch(`/orders/${orderId}/status`, statusData),
};

export default api;

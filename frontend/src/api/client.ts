/**
 * Axios API client with base configuration.
 * Person 6 owns this file.
 */
import axios from 'axios';

const apiClient = axios.create({
  baseURL: '/api/v1',
  timeout: 120000,
  headers: { 'Content-Type': 'application/json' },
});

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 429) {
      console.warn('Rate limited. Please wait before trying again.');
    }
    return Promise.reject(error);
  }
);

export default apiClient;

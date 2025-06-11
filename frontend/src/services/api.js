import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 300000, // 5 minutes timeout for long processing
  // Don't set Content-Type here - let axios handle it for different request types
});

// Request interceptor
api.interceptors.request.use(
  (config) => {
    // Add any auth headers here if needed in the future
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor
api.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    // Handle common errors
    if (error.response?.status === 413) {
      error.message = 'File too large. Please try a smaller file.';
    } else if (error.response?.status === 422) {
      error.message = 'Invalid file format. Please check supported formats.';
    } else if (error.response?.status >= 500) {
      error.message = 'Server error. Please try again later.';
    }
    
    return Promise.reject(error);
  }
);

export default api; 
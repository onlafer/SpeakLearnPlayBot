import axios from 'axios';

// Get api_url from the page URL query parameters (useful for local backend + Vercel frontend)
const urlParams = new URLSearchParams(window.location.search);
let queryApiUrl = urlParams.get('api_url');

console.log('[API Client] Initializing...');
console.log('[API Client] Full URL:', window.location.href);
console.log('[API Client] Parsed api_url from URL search params:', queryApiUrl);

if (queryApiUrl) {
  localStorage.setItem('api_url', queryApiUrl);
  console.log('[API Client] Saved api_url to localStorage:', queryApiUrl);
} else {
  queryApiUrl = localStorage.getItem('api_url');
  console.log('[API Client] Retrieved api_url from localStorage:', queryApiUrl);
}

const activeBaseUrl = queryApiUrl || import.meta.env.VITE_API_URL || '';
console.log('[API Client] Active Base URL configured:', activeBaseUrl);

const client = axios.create({
  baseURL: activeBaseUrl,
  timeout: 10000, // 10 seconds timeout
});

// Add Request interceptor for logging
client.interceptors.request.use((config) => {
  console.log(`[API Request] ${config.method?.toUpperCase()} ${config.baseURL}${config.url}`, {
    params: config.params,
    data: config.data,
  });
  return config;
}, (error) => {
  console.error('[API Request Error]', error);
  return Promise.reject(error);
});

// Add Response interceptor for logging
client.interceptors.response.use((response) => {
  console.log(`[API Response] ${response.status} ${response.config.url}`, response.data);
  return response;
}, (error) => {
  console.error('[API Response Error]', {
    message: error.message,
    status: error.response?.status,
    data: error.response?.data,
    url: error.config?.url,
    baseURL: error.config?.baseURL,
  });
  return Promise.reject(error);
});

export default client;


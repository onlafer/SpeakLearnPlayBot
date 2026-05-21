import axios from 'axios';

// Get api_url from the page URL query parameters (useful for local backend + Vercel frontend)
const urlParams = new URLSearchParams(window.location.search);
let queryApiUrl = urlParams.get('api_url');

if (queryApiUrl) {
  localStorage.setItem('api_url', queryApiUrl);
} else {
  queryApiUrl = localStorage.getItem('api_url');
}

const client = axios.create({
  baseURL: queryApiUrl || import.meta.env.VITE_API_URL || '',
});

export default client;

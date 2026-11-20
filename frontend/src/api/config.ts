const developmentApiUrl = import.meta.env.DEV ? 'http://localhost:8000' : '';

export const API_BASE_URL = (
  import.meta.env.VITE_API_URL ?? developmentApiUrl
).replace(/\/+$/, '');

export const API_DISPLAY_URL = API_BASE_URL || window.location.origin;

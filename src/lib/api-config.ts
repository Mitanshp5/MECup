// Centralized API configuration
export const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:5001";

// Helper function to construct API URLs
export const getApiUrl = (path: string) => `${API_BASE_URL}${path}`;

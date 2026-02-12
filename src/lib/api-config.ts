// Centralized API configuration
// Centralized API configuration
const getBaseUrl = () => {
    if (typeof window === 'undefined') return "http://localhost:5001";

    const host = window.location.hostname;
    if (host === 'localhost' || host === '127.0.0.1') {
        return "http://localhost:5001";
    }
    // Assume same host, port 5002 for mobile backend
    return `http://${host}:5002`;
};

export const API_BASE_URL = import.meta.env.VITE_API_URL || getBaseUrl();

// Helper function to construct API URLs
export const getApiUrl = (path: string) => `${API_BASE_URL}${path}`;

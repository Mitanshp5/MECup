export const API_CONFIG = {
    // Default to 5001 for web development if not set
    BASE_URL: "http://localhost:5001",
};

export const getBaseUrl = () => API_CONFIG.BASE_URL;

export const setBaseUrl = (url: string) => {
    console.log(`[Config] Updating API Base URL to: ${url}`);
    API_CONFIG.BASE_URL = url;
};

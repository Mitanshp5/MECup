import React, { createContext, useContext, useState, useEffect } from 'react';

// API Base URL
const API_BASE_URL = "http://127.0.0.1:5001";

interface User {
    username: string;
    role: 'admin' | 'operator' | 'viewer';
}

interface AuthContextType {
    user: User | null;
    token: string | null;
    login: (username: string, password: string) => Promise<{ success: boolean; message?: string }>;
    logout: () => void;
    isAuthenticated: boolean;
    hasRole: (roles: string[]) => boolean;
}

const AuthContext = createContext<AuthContextType | null>(null);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
    const [user, setUser] = useState<User | null>(null);
    const [token, setToken] = useState<string | null>(null);

    // Load token from localStorage on startup
    useEffect(() => {
        const storedToken = localStorage.getItem('token');
        const storedRole = localStorage.getItem('role');
        const storedUser = localStorage.getItem('username');

        if (storedToken && storedUser) {
            setToken(storedToken);
            setUser({
                username: storedUser,
                role: (storedRole as any) || 'viewer'
            });
        }
    }, []);

    const login = async (username: string, password: string): Promise<{ success: boolean; message?: string }> => {
        try {
            const formData = new URLSearchParams();
            formData.append('username', username);
            formData.append('password', password);

            const res = await fetch(`${API_BASE_URL}/token`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: formData.toString(),
            });

            if (!res.ok) {
                const errorData = await res.json().catch(() => ({ detail: res.statusText }));
                console.error("Login API Error:", res.status, errorData);

                if (res.status === 401) {
                    return { success: false, message: 'Invalid credentials' };
                }
                if (res.status === 422) {
                    return { success: false, message: 'Validation Error (422): ' + JSON.stringify(errorData) };
                }
                return { success: false, message: `Server Error (${res.status}): ${errorData.detail || 'Unknown error'}` };
            }

            const data = await res.json();
            const accessToken = data.access_token;
            const role = data.role;

            // Save to state
            setToken(accessToken);
            setUser({ username, role });

            // Save to local storage
            localStorage.setItem('token', accessToken);
            localStorage.setItem('username', username);
            localStorage.setItem('role', role);

            return { success: true };
        } catch (error: any) {
            console.error("Login Error:", error);
            // Propagate the specific error message if possible
            if (error.message === 'Failed to fetch') {
                // Network error (backend down)
                console.error("Backend seems to be offline");
                return { success: false, message: 'Backend unreachable. Is server running?' };
            }
            return { success: false, message: error.message || 'Login failed' };
        }
    };

    const logout = () => {
        setToken(null);
        setUser(null);
        localStorage.removeItem('token');
        localStorage.removeItem('username');
        localStorage.removeItem('role');
    };

    const hasRole = (allowedRoles: string[]) => {
        if (!user) return false;
        return allowedRoles.includes(user.role);
    };

    return (
        <AuthContext.Provider value={{ user, token, login, logout, isAuthenticated: !!user, hasRole }}>
            {children}
        </AuthContext.Provider>
    );
};

export const useAuth = () => {
    const context = useContext(AuthContext);
    if (!context) throw new Error('useAuth must be used within an AuthProvider');
    return context;
};

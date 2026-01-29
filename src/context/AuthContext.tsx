import React, { createContext, useContext, useState, useEffect } from "react";
import { toast } from "sonner";

export enum UserRole {
    ADMIN = "ADMIN",
    OPERATOR = "OPERATOR",
    VIEWER = "VIEWER"
}

interface User {
    username: string;
    role: UserRole;
    is_active: boolean;
}

interface AuthContextType {
    user: User | null;
    token: string | null;
    isLoading: boolean;
    login: (username: string, password: string) => Promise<boolean>;
    logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
    const [user, setUser] = useState<User | null>({
        username: "admin",
        role: UserRole.ADMIN,
        is_active: true
    });
    const [token, setToken] = useState<string | null>("bypass-token");
    const [isLoading, setIsLoading] = useState(false);

    // Hydrate user on mount if token exists
    useEffect(() => {
        // BYPASS: No hydration needed
    }, []);

    const fetchUser = async (authToken: string) => {
        try {
            const res = await fetch("http://localhost:5001/users/me", {
                headers: { Authorization: `Bearer ${authToken}` }
            });
            if (res.ok) {
                const userData = await res.json();
                setUser(userData);
            } else {
                logout(); // Invalid token
            }
        } catch (e) {
            console.error("Auth hydration failed", e);
            logout();
        } finally {
            setIsLoading(false);
        }
    };

    const login = async (username: string, password: string) => {
        try {
            const formData = new URLSearchParams();
            formData.append("username", username);
            formData.append("password", password);

            const res = await fetch("http://localhost:5001/token", {
                method: "POST",
                headers: { "Content-Type": "application/x-www-form-urlencoded" },
                body: formData,
            });

            if (res.ok) {
                const data = await res.json();
                const accessToken = data.access_token;
                setToken(accessToken);
                localStorage.setItem("token", accessToken);
                // Fetch user details immediately to get role
                await fetchUser(accessToken);
                toast.success("Welcome back!", { description: `Logged in as ${username}` });
                return true;
            } else {
                toast.error("Login Failed", { description: "Invalid username or password" });
                return false;
            }
        } catch (e) {
            toast.error("Network Error", { description: "Could not reach authentication server" });
            return false;
        }
    };

    const logout = () => {
        setUser(null);
        setToken(null);
        localStorage.removeItem("token");
        toast.info("Logged Out");
    };

    return (
        <AuthContext.Provider value={{ user, token, isLoading, login, logout }}>
            {children}
        </AuthContext.Provider>
    );
};

export const useAuth = () => {
    const context = useContext(AuthContext);
    if (!context) throw new Error("useAuth must be used within an AuthProvider");
    return context;
};

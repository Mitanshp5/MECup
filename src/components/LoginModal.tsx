import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { X, Lock, User } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

interface LoginModalProps {
    isOpen: boolean;
    onClose: () => void;
}

const LoginModal: React.FC<LoginModalProps> = ({ isOpen, onClose }) => {
    const { login } = useAuth();
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        setError('');

        const result = await login(username, password);
        setLoading(false);

        if (result.success) {
            onClose();
            setUsername('');
            setPassword('');
        } else {
            setError(result.message || 'Login failed');
        }
    };

    if (!isOpen) return null;

    return (
        <AnimatePresence>
            <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
                <motion.div
                    initial={{ opacity: 0, scale: 0.95 }}
                    animate={{ opacity: 1, scale: 1 }}
                    exit={{ opacity: 0, scale: 0.95 }}
                    className="bg-card w-full max-w-sm rounded-lg border border-border shadow-xl overflow-hidden"
                >
                    {/* Header */}
                    <div className="flex items-center justify-between p-4 border-b border-border bg-secondary/50">
                        <h2 className="text-lg font-semibold text-foreground flex items-center gap-2">
                            <Lock className="w-4 h-4 text-primary" />
                            System Login
                        </h2>
                        <button onClick={onClose} className="text-muted-foreground hover:text-foreground">
                            <X className="w-5 h-5" />
                        </button>
                    </div>

                    {/* Form */}
                    <form onSubmit={handleSubmit} className="p-6 space-y-4">
                        {error && (
                            <div className="p-3 bg-destructive/10 border border-destructive/20 rounded text-sm text-destructive">
                                {error}
                            </div>
                        )}

                        <div className="space-y-2">
                            <label className="text-sm font-medium text-muted-foreground">Username</label>
                            <div className="relative">
                                <User className="absolute left-3 top-2.5 w-4 h-4 text-muted-foreground" />
                                <input
                                    type="text"
                                    value={username}
                                    onChange={(e) => setUsername(e.target.value)}
                                    className="w-full pl-9 pr-3 py-2 bg-background border border-input rounded-md focus:outline-none focus:ring-2 focus:ring-primary/50 text-foreground"
                                    placeholder="Username"
                                    required
                                />
                            </div>
                        </div>

                        <div className="space-y-2">
                            <label className="text-sm font-medium text-muted-foreground">Password</label>
                            <div className="relative">
                                <Lock className="absolute left-3 top-2.5 w-4 h-4 text-muted-foreground" />
                                <input
                                    type="password"
                                    value={password}
                                    onChange={(e) => setPassword(e.target.value)}
                                    className="w-full pl-9 pr-3 py-2 bg-background border border-input rounded-md focus:outline-none focus:ring-2 focus:ring-primary/50 text-foreground"
                                    placeholder="Password"
                                />
                            </div>
                        </div>

                        <button
                            type="submit"
                            disabled={loading}
                            className="w-full py-2 bg-primary text-primary-foreground font-medium rounded-md hover:bg-primary/90 transition-colors disabled:opacity-50"
                        >
                            {loading ? 'Authenticating...' : 'Login'}
                        </button>
                    </form>
                </motion.div>
            </div>
        </AnimatePresence>
    );
};

export default LoginModal;

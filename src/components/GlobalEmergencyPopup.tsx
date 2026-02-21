import { useState, useEffect } from "react";
import { AlertTriangle, RotateCcw } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

const getApiBaseUrl = () => {
    if (!window.location.hostname) return 'http://127.0.0.1:5001';
    return `http://${window.location.hostname}:5001`;
};

const API_BASE_URL = getApiBaseUrl();

const GlobalEmergencyPopup = () => {
    const [isEmergency, setIsEmergency] = useState(false);
    const [isResetting, setIsResetting] = useState(false);

    useEffect(() => {
        let timeoutId: NodeJS.Timeout;
        const checkStatus = async () => {
            try {
                const res = await fetch(`${API_BASE_URL}/plc/control-status`);
                const data = await res.json();
                if (data.m599 === 1) {
                    setIsEmergency(true);
                } else {
                    setIsEmergency(false);
                }
            } catch (e) {
                // Ignore errors, retry silently
            }
            timeoutId = setTimeout(checkStatus, 1000);
        };

        checkStatus();
        return () => clearTimeout(timeoutId);
    }, []);

    const handleReset = async () => {
        setIsResetting(true);
        try {
            await fetch(`${API_BASE_URL}/plc/cycle-reset`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({})
            });
            // Optimistic close? Or wait for poll?
            // Wait for poll to clear it naturally, but maybe delay button re-enable
            await new Promise(r => setTimeout(r, 1000));
        } catch (e) {
            console.error("Reset failed", e);
        } finally {
            setIsResetting(false);
        }
    };

    return (
        <AnimatePresence>
            {isEmergency && (
                <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    className="fixed inset-0 z-[9999] bg-black/90 backdrop-blur-sm flex items-center justify-center p-4"
                >
                    <motion.div
                        initial={{ scale: 0.9, y: 20 }}
                        animate={{ scale: 1, y: 0 }}
                        className="bg-destructive text-destructive-foreground border-4 border-red-500 rounded-2xl shadow-[0_0_100px_rgba(239,68,68,0.5)] p-8 max-w-lg w-full text-center space-y-8"
                    >
                        <div className="flex justify-center">
                            <div className="w-24 h-24 rounded-full bg-red-600 flex items-center justify-center animate-pulse">
                                <AlertTriangle className="w-12 h-12 text-white" />
                            </div>
                        </div>

                        <div className="space-y-2">
                            <h1 className="text-4xl font-black tracking-tighter uppercase mb-2">
                                EMERGENCY STOP
                            </h1>
                            <p className="text-xl font-medium text-red-100/90">
                                SYSTEM HALTED
                            </p>
                            <p className="text-sm text-red-200/70">
                                The machine has been stopped due to an emergency condition.
                                Resolve the issue before resetting.
                            </p>
                        </div>

                        {/* <button
                            onClick={handleReset}
                            disabled={isResetting}
                            className={`
                                w-full py-6 text-2xl font-bold uppercase tracking-widest rounded-xl transition-all
                                flex items-center justify-center gap-4
                                ${isResetting
                                    ? 'bg-white/20 cursor-wait'
                                    : 'bg-white text-destructive hover:bg-gray-100 hover:scale-[1.02] shadow-xl'
                                }
                            `}
                        >
                            <RotateCcw className={`w-8 h-8 ${isResetting ? 'animate-spin' : ''}`} />
                            {isResetting ? 'RESETTING...' : 'RESET SYSTEM'}
                        </button> */}

                    </motion.div>
                </motion.div>
            )}
        </AnimatePresence>
    );
};

export default GlobalEmergencyPopup;

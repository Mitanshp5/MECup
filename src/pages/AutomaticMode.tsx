import { useState, useEffect, useCallback } from "react";
import { motion } from "framer-motion";
import { toast } from "sonner";
import { Play, Square, Camera, AlertTriangle, Grid2x2Check, RotateCcw, Home, Zap, X, Image as ImageIcon } from "lucide-react";

interface Defect {
  id: string;
  type: string;
  location: string;
  timestamp: string;
  imageUrl?: string;
}

interface InferenceResult {
  success: boolean;
  inference_time_ms: number;
  defects: {
    type: string;
    class_id: number;
    pixel_count: number;
    area_ratio: number;
    severity: string;
  }[];
  mask_url: string | null;
  overlay_url: string | null;
  message: string | null;
}

const AutomaticMode = () => {
  const MOCK_MODE = true; // TOGGLE THIS FOR MOCK MODE

  const [isScanning, setIsScanning] = useState(false);
  const [gridTriggered, setGridTriggered] = useState(false);
  const [defects, setDefects] = useState<Defect[]>([]);
  const [totalDefectCount, setTotalDefectCount] = useState(0);
  const [resultImageUrl, setResultImageUrl] = useState<string | null>(null);
  const [selectedDefectImage, setSelectedDefectImage] = useState<string | null>(null);
  const [isInferencing, setIsInferencing] = useState(false);
  const [lastInferenceTime, setLastInferenceTime] = useState<number | null>(null);

  useEffect(() => {
    // Connect to camera on mount (Skip in mock mode if no camera needed, but kept for realism)
    if (!MOCK_MODE) {
      fetch('http://localhost:5001/camera/connect', { method: 'POST' })
        .catch(err => console.error("Failed to connect camera:", err));
    }

    // Sync scan state from PLC on mount and periodically
    const syncScanState = async () => {
      if (MOCK_MODE) return;

      try {
        const res = await fetch('http://localhost:5001/plc/control-status');
        const data = await res.json();
        if (data.m5 !== null && data.m5 !== undefined) {
          const plcScanning = data.m5 === 1;
          setIsScanning(plcScanning);
          // If M5 is off, also reset grid state
          if (!plcScanning) {
            setGridTriggered(false);
          }
        }
      } catch (err) {
        console.error("Failed to sync scan state:", err);
      }
    };

    syncScanState();
    const interval = setInterval(syncScanState, 2000); // Poll every 2 seconds

    return () => clearInterval(interval);
  }, [MOCK_MODE]);

  // Mock Mode: Trigger inference periodically when scanning
  useEffect(() => {
    if (!MOCK_MODE || !isScanning) return;

    const runMockInference = async () => {
      try {
        await fetch('http://localhost:5001/inference/mock-run', { method: 'POST' });
      } catch (e) {
        console.error("Mock run error:", e);
      }
    };

    const interval = setInterval(runMockInference, 5000); // Trigger every 5 seconds
    return () => clearInterval(interval);
  }, [MOCK_MODE, isScanning]);


  // Poll for latest inference results (PLC or Mock)
  const [lastInferenceTimestamp, setLastInferenceTimestamp] = useState<string | null>(null);

  useEffect(() => {
    const pollLatestInference = async () => {
      try {
        const endpoint = MOCK_MODE
          ? 'http://localhost:5001/inference/mock-latest'
          : 'http://localhost:5001/plc/latest-inference';

        const res = await fetch(endpoint);
        const data = await res.json();

        if (data.has_result && data.timestamp !== lastInferenceTimestamp) {
          // New result available
          setLastInferenceTimestamp(data.timestamp);
          setLastInferenceTime(data.inference_time_ms);

          // Set result image
          if (data.overlay_url) {
            setResultImageUrl(`http://localhost:5001${data.overlay_url}`);
          }

          // Add defects
          if (data.defects && data.defects.length > 0) {
            const timestamp = new Date().toLocaleTimeString();
            const imageUrl = data.overlay_url ? `http://localhost:5001${data.overlay_url}` : undefined;
            // Show only one image entry per inference (regardless of defect count/types)
            const newDefect: Defect = {
              id: `${Date.now()}`,
              type: "Defect",
              location: "Detected",
              timestamp,
              imageUrl,
            };

            setDefects(prev => {
              // Prevent adding duplicate images (compare base URL without query params)
              const newBaseUrl = imageUrl?.split('?')[0];
              const prevBaseUrl = prev.length > 0 ? prev[0].imageUrl?.split('?')[0] : null;

              if (newBaseUrl && prevBaseUrl && newBaseUrl === prevBaseUrl) {
                return prev;
              }
              return [newDefect, ...prev].slice(0, 50);
            });
            setTotalDefectCount(prev => prev + data.defects.length);
            toast.success(`${data.defects.length} Defect(s) Found`, {
              description: `Inference: ${data.inference_time_ms.toFixed(1)}ms (${MOCK_MODE ? 'Mock' : 'Live'})`
            });
          }
        }
      } catch (err) {
        // Silent fail for polling
      }
    };

    // Poll every 500ms for responsive updates
    const interval = setInterval(pollLatestInference, 500);

    return () => clearInterval(interval);
  }, [lastInferenceTimestamp, MOCK_MODE]);

  const handleStartScan = async () => {
    if (MOCK_MODE) {
      setIsScanning(true);
      toast.success("Mock Scan Started", { description: "Simulating M5 ON" });
      return;
    }

    try {
      const res = await fetch("http://localhost:5001/plc/scan-start", {
        method: "POST",
      });
      const data = await res.json();

      if (data.success) {
        setIsScanning(true);
        toast.success("Scan Started", { description: "M5 set to ON" });
      } else {
        toast.error("Failed to start scan", { description: data.error || "PLC Error" });
      }
    } catch (e) {
      console.error("Start scan error:", e);
      toast.error("Failed to start scan", { description: "Network error" });
    }
  };

  const handleStopScan = async () => {
    if (MOCK_MODE) {
      setIsScanning(false);
      setGridTriggered(false);
      toast.info("Mock Scan Stopped", { description: "Simulating M5 OFF" });
      return;
    }

    try {
      const res = await fetch("http://localhost:5001/plc/write", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ device: "M5", value: 0 }),
      });
      const data = await res.json();

      if (data.success) {
        setIsScanning(false);
        setGridTriggered(false); // Reset grid state on stop
        toast.info("Scan Stopped", { description: "M5 set to OFF" });
      } else {
        toast.error("Failed to stop scan", { description: data.error || "PLC Error" });
      }
    } catch (e) {
      console.error("Stop scan error:", e);
      setIsScanning(false);
      setGridTriggered(false); // Reset grid state on stop
      toast.error("Failed to stop scan", { description: "Network error" });
    }
  };

  const handleGridOne = async () => {
    if (MOCK_MODE) {
      setGridTriggered(true);
      toast.success("Mock Grid One", { description: "Simulated M4 ON" });
      return;
    }

    try {
      const res = await fetch("http://localhost:5001/plc/grid-one", { method: "POST" });
      const data = await res.json();
      if (data.success) {
        setGridTriggered(true);
        toast.success("Grid One Triggered", { description: "M4 set to ON" });
      } else {
        toast.error("Grid One Failed", { description: data.error || "PLC Error" });
      }
    } catch (e) {
      console.error("Grid One error:", e);
      toast.error("Grid One Failed", { description: "Network error" });
    }
  };

  const handleCycleReset = async () => {
    if (MOCK_MODE) {
      setDefects([]);
      setTotalDefectCount(0);
      setResultImageUrl(null);
      toast.success("Mock Cycle Reset", { description: "Cleared results" });
      return;
    }

    try {
      const res = await fetch("http://localhost:5001/plc/cycle-reset", { method: "POST" });
      const data = await res.json();
      if (data.success) {
        toast.success("Cycle Reset", { description: "M120 set to ON" });
      } else {
        toast.error("Cycle Reset Failed", { description: data.error || "PLC Error" });
      }
    } catch (e) {
      console.error("Cycle Reset error:", e);
      toast.error("Cycle Reset Failed", { description: "Network error" });
    }
  };

  const handleHomingStart = async () => {
    if (MOCK_MODE) {
      toast.success("Mock Homing", { description: "Simulated Homing" });
      return;
    }

    try {
      const res = await fetch("http://localhost:5001/plc/homing-start", { method: "POST" });
      const data = await res.json();
      if (data.success) {
        toast.success("Homing Started", { description: "M1 set to ON" });
      } else {
        toast.error("Homing Failed", { description: data.error || "PLC Error" });
      }
    } catch (e) {
      console.error("Homing error:", e);
      toast.error("Homing Failed", { description: "Network error" });
    }
  };

  const handleRunInference = useCallback(async () => {
    if (isInferencing) return;
    setIsInferencing(true);
    try {
      const endpoint = MOCK_MODE ? "http://localhost:5001/inference/mock-run" : "http://localhost:5001/inference/run";
      const res = await fetch(endpoint, { method: "POST" });
      const data = await res.json();

      if (data.success) {
        setLastInferenceTime(data.inference_time_ms);

        const imageUrl = data.overlay_url
          ? `http://localhost:5001${data.overlay_url}?t=${Date.now()}`
          : null;

        if (imageUrl) {
          setResultImageUrl(imageUrl);
        }

        const timestamp = new Date().toLocaleTimeString();

        if (data.defects && data.defects.length > 0) {
          // Show only one image entry per inference
          const newDefect: Defect = {
            id: `${Date.now()}`,
            type: "Defect",
            location: "Detected",
            timestamp,
            imageUrl: imageUrl || undefined,
          };

          setDefects(prev => {
            // Prevent adding duplicate images (compare base URL without query params)
            const newBaseUrl = imageUrl?.split('?')[0];
            const prevBaseUrl = prev.length > 0 ? prev[0].imageUrl?.split('?')[0] : null;

            if (newBaseUrl && prevBaseUrl && newBaseUrl === prevBaseUrl) {
              return prev;
            }
            return [newDefect, ...prev].slice(0, 50);
          });
          setTotalDefectCount(prev => prev + data.defects.length);
          toast.success(`${data.defects.length} Defect(s) Found`, {
            description: `Inference: ${data.inference_time_ms.toFixed(1)}ms`
          });
        } else {
          toast.success("No Defects", { description: `Inference: ${data.inference_time_ms.toFixed(1)}ms` });
        }
      } else {
        toast.error("Inference Failed", { description: data.message || "Unknown error" });
      }
    } catch (e) {
      console.error("Inference error:", e);
      toast.error("Inference Failed", { description: "Network error" });
    } finally {
      setIsInferencing(false);
    }
  }, [isInferencing]);

  return (
    <div className="h-full grid grid-cols-12 gap-4">
      {/* Left Section: Camera Feed + Controls */}
      <div className="col-span-8 flex flex-col gap-3 h-full">
        {/* Top row: Camera + Start/Stop buttons */}
        <div className="flex-1 flex gap-3 min-h-0">
          {/* Camera Feed - 4:3 aspect ratio */}
          <div className="flex-1 industrial-panel relative overflow-hidden bg-black">
            <div className="absolute top-4 left-4 z-10 flex items-center gap-3">
              <div className="flex items-center gap-2 px-3 py-1.5 bg-background/80 backdrop-blur-sm rounded border border-border">
                <Camera className="w-4 h-4 text-primary" />
                <span className="text-xs font-medium text-foreground">LIVE FEED</span>
                {isScanning && (
                  <span className="flex items-center gap-1.5">
                    <span className="w-2 h-2 rounded-full bg-destructive animate-pulse" />
                    <span className="text-xs text-destructive font-mono">REC</span>
                  </span>
                )}
              </div>
            </div>

            {/* 4:3 aspect ratio container */}
            <div className="absolute inset-0 flex items-center justify-center">
              <div className="w-full h-full max-w-full max-h-full" style={{ aspectRatio: '4/3' }}>
                <img
                  src="http://localhost:5001/camera/stream"
                  className="w-full h-full object-contain"
                  alt="Live Feed"
                  onError={(e) => {
                    e.currentTarget.style.display = 'none';
                    const parent = e.currentTarget.parentElement;
                    if (parent) {
                      parent.classList.add('bg-black/80', 'flex', 'items-center', 'justify-center', 'border', 'border-destructive/30');
                      // Create offline message element
                      const offlineMsg = document.createElement('div');
                      offlineMsg.className = 'flex flex-col items-center text-destructive animate-pulse';
                      offlineMsg.innerHTML = `
                        <svg width="48" height="48" viewBox="0 0 24 24" fill="none" class="mb-2" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                          <line x1="2" x2="22" y1="2" y2="22"></line>
                          <path d="M7 7H4a2 2 0 0 0-2 2v9a2 2 0 0 0 2 2h16"></path>
                          <path d="M9.5 14.5 12 12l2.5 2.5"></path>
                          <path d="M16 16v4a2 2 0 0 0 2 2h4"></path>
                        </svg>
                        <span class="text-sm font-mono font-bold">CAMERA OFFLINE</span>
                      `;
                      parent.appendChild(offlineMsg);
                    }
                  }}
                />
              </div>
            </div>

            {/* Fallback placeholder */}
            <div className="absolute inset-0 flex items-center justify-center -z-10">
              <div className="text-center">
                <Camera className="w-12 h-12 text-muted-foreground/50 mx-auto mb-2" />
                <p className="text-muted-foreground text-sm">Waiting for live feed...</p>
              </div>
            </div>

            {/* Scan overlay */}
            {isScanning && (
              <motion.div
                className="absolute inset-0 pointer-events-none"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
              >
                <div className="absolute inset-0 border-2 border-primary/50 animate-pulse" />
              </motion.div>
            )}
          </div>

          {/* Start/Stop Buttons - Vertical on right of camera */}
          <div className="w-20 flex flex-col gap-2">
            {/* Status indicator */}
            <div className="industrial-panel p-2 flex items-center justify-center gap-1.5">
              <span className={`w-2 h-2 rounded-full ${isScanning ? 'bg-success animate-pulse' : 'bg-muted-foreground/30'}`} />
              <span className="text-[10px] text-muted-foreground font-mono">
                {isScanning ? 'SCAN' : 'IDLE'}
              </span>
            </div>

            {/* Start */}
            <motion.button
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              onClick={handleStartScan}
              disabled={isScanning}
              className={`flex-1 flex flex-col items-center justify-center gap-1 p-2 rounded-lg font-medium transition-all shadow-lg ${isScanning
                ? "bg-secondary/50 text-muted-foreground cursor-not-allowed border border-border/50"
                : "bg-gradient-to-br from-success to-success/80 text-success-foreground hover:from-success/90 hover:to-success/70 border border-success/30"
                }`}
            >
              <Play className={`w-6 h-6 ${isScanning ? '' : 'drop-shadow-md'}`} />
              <span className="text-xs font-bold">START</span>
            </motion.button>

            {/* Stop */}
            <motion.button
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              onClick={handleStopScan}
              disabled={!isScanning}
              className={`flex-1 flex flex-col items-center justify-center gap-1 p-2 rounded-lg font-medium transition-all shadow-lg ${!isScanning
                ? "bg-secondary/50 text-muted-foreground cursor-not-allowed border border-border/50"
                : "bg-gradient-to-br from-red-500 to-red-600 text-white hover:from-red-400 hover:to-red-500 border-2 border-red-400 ring-2 ring-red-500/30"
                }`}
            >
              <Square className={`w-6 h-6 ${isScanning ? 'drop-shadow-md' : ''}`} />
              <span className="text-xs font-bold">STOP</span>
            </motion.button>
          </div>
        </div>

        {/* Bottom row: Grid, Reset, Home buttons */}
        <div className="industrial-panel p-3">
          <div className="grid grid-cols-3 gap-3">
            {/* Grid */}
            <motion.button
              whileHover={{ scale: (isScanning || gridTriggered) ? 1 : 1.02 }}
              whileTap={{ scale: (isScanning || gridTriggered) ? 1 : 0.98 }}
              onClick={handleGridOne}
              disabled={isScanning || gridTriggered}
              className={`flex flex-col items-center justify-center gap-1 p-3 rounded-lg font-medium transition-all shadow-lg ${(isScanning || gridTriggered)
                ? "bg-secondary/50 text-muted-foreground cursor-not-allowed border border-border/50"
                : "bg-gradient-to-br from-sky-500 to-sky-600 text-white hover:from-sky-400 hover:to-sky-500 border border-sky-400/30"
                }`}
            >
              <Grid2x2Check className={`w-5 h-5 ${(isScanning || gridTriggered) ? '' : 'drop-shadow-md'}`} />
              <span className="text-xs font-bold">GRID ONE</span>
            </motion.button>

            {/* Reset */}
            <motion.button
              whileHover={{ scale: isScanning ? 1 : 1.02 }}
              whileTap={{ scale: isScanning ? 1 : 0.98 }}
              onClick={handleCycleReset}
              disabled={isScanning}
              className={`flex flex-col items-center justify-center gap-1 p-3 rounded-lg font-medium transition-all shadow-lg ${isScanning
                ? "bg-secondary/50 text-muted-foreground cursor-not-allowed border border-border/50"
                : "bg-gradient-to-br from-amber-500 to-amber-600 text-white hover:from-amber-400 hover:to-amber-500 border border-amber-400/30"
                }`}
            >
              <RotateCcw className={`w-5 h-5 ${isScanning ? '' : 'drop-shadow-md'}`} />
              <span className="text-xs font-bold">RESET</span>
            </motion.button>

            {/* Home */}
            <motion.button
              whileHover={{ scale: isScanning ? 1 : 1.02 }}
              whileTap={{ scale: isScanning ? 1 : 0.98 }}
              onClick={handleHomingStart}
              disabled={isScanning}
              className={`flex flex-col items-center justify-center gap-1 p-3 rounded-lg font-medium transition-all shadow-lg ${isScanning
                ? "bg-secondary/50 text-muted-foreground cursor-not-allowed border border-border/50"
                : "bg-gradient-to-br from-slate-600 to-slate-700 text-white hover:from-slate-500 hover:to-slate-600 border border-slate-500/30"
                }`}
            >
              <Home className={`w-5 h-5 ${isScanning ? '' : 'drop-shadow-md'}`} />
              <span className="text-xs font-bold">HOME</span>
            </motion.button>
          </div>
        </div>
      </div>


      {/* Defect Panel */}
      <div className="col-span-4 industrial-panel p-4 flex flex-col overflow-hidden">
        {/* Result Image Placeholder */}
        <div className="mb-4 flex-shrink-0">
          <div className="flex items-center justify-between mb-2">
            <h3 className="text-sm font-medium text-muted-foreground">RESULT IMAGE</h3>
            {lastInferenceTime && (
              <span className="text-xs text-success font-mono">{lastInferenceTime.toFixed(1)}ms</span>
            )}
          </div>
          <div className="aspect-[4/3] bg-black rounded-lg border border-border overflow-hidden flex items-center justify-center">
            {resultImageUrl ? (
              <img
                src={resultImageUrl}
                className="w-full h-full object-contain"
                alt="Inference Result"
              />
            ) : (
              <div className="text-center">
                <ImageIcon className="w-10 h-10 text-muted-foreground/30 mx-auto mb-2" />
              </div>
            )}
          </div>
        </div>

        {/* Defects List Header */}
        <div className="flex items-center justify-between mb-3 flex-shrink-0">
          <h3 className="text-sm font-medium text-muted-foreground">DEFECTS FOUND</h3>
          <span className="px-2 py-1 bg-destructive/10 text-destructive text-xs font-medium rounded">
            {totalDefectCount}
          </span>
        </div>

        {/* Scrollable Defects Grid */}
        <div className="flex-1 overflow-y-auto min-h-0 bg-secondary/30 rounded-lg p-2">
          {defects.length > 0 ? (
            <div className="grid grid-cols-3 gap-2">
              {defects.map((defect) => (
                <motion.button
                  key={defect.id}
                  layout
                  initial={{ opacity: 0, scale: 0.8 }}
                  animate={{ opacity: 1, scale: 1 }}
                  onClick={() => defect.imageUrl && setSelectedDefectImage(defect.imageUrl)}
                  className="aspect-square bg-black/50 rounded overflow-hidden relative group border border-transparent hover:border-primary/50 transition-colors"
                >
                  {defect.imageUrl ? (
                    <img
                      src={defect.imageUrl}
                      alt={defect.type}
                      className="w-full h-full object-cover"
                    />
                  ) : (
                    <div className="flex w-full h-full items-center justify-center">
                      <AlertTriangle className="w-5 h-5 text-destructive/50" />
                    </div>
                  )}

                </motion.button>
              ))}
            </div>
          ) : (
            <div className="h-full flex flex-col items-center justify-center text-muted-foreground/50">
              <span className="text-xs">No defects yet</span>
            </div>
          )}
        </div>
      </div>

      {/* Image Modal */}
      {selectedDefectImage && (
        <div
          className="fixed inset-0 bg-black/80 z-50 flex items-center justify-center p-8"
          onClick={() => setSelectedDefectImage(null)}
        >
          <div className="relative max-w-4xl max-h-full">
            <button
              onClick={() => setSelectedDefectImage(null)}
              className="absolute -top-10 right-0 p-2 text-white hover:text-primary transition-colors"
            >
              <X className="w-6 h-6" />
            </button>
            <img
              src={selectedDefectImage}
              className="max-w-full max-h-[80vh] object-contain rounded-lg"
              alt="Defect Image"
            />
          </div>
        </div>
      )}
    </div>
  );
};

export default AutomaticMode;

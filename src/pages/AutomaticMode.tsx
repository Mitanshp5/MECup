import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { toast } from "sonner";
import { Play, Pause, Square, Camera, AlertTriangle, CheckCircle } from "lucide-react";

interface Defect {
  id: string;
  type: string;
  location: string;
  severity: "low" | "medium" | "high";
  timestamp: string;
}

const AutomaticMode = () => {
  const [isScanning, setIsScanning] = useState(false);
  // const [scanProgress, setScanProgress] = useState(0); // Removed simulation
  const [defects, setDefects] = useState<Defect[]>([
    { id: "1", type: "Orange Peel", location: "Front Hood - Left", severity: "low", timestamp: "10:45:23" },
    { id: "2", type: "Dust Nib", location: "Driver Door", severity: "medium", timestamp: "10:45:31" },
  ]);

  useEffect(() => {
    // Connect to camera on mount
    fetch('http://localhost:5001/camera/connect', { method: 'POST' })
      .catch(err => console.error("Failed to connect camera:", err));

    // Optional: Disconnect on unmount? 
    // For now, let's keep it connected to avoid frequent reconnections if user switches tabs.
    // return () => {
    //   fetch('http://localhost:5001/camera/disconnect', { method: 'POST' });
    // };
  }, []);

  const handleStartScan = async () => {
    try {
      // Trigger PLC M5
      const res = await fetch("http://localhost:5001/plc/write", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ device: "M5", value: 1 }),
      });
      const data = await res.json();

      if (data.success) {
        setIsScanning(true);
        toast.success("Scan Started", { description: "PLC M5 set to ON" });
      } else {
        toast.error("Failed to start scan", { description: data.error || "PLC Error" });
      }
    } catch (e) {
      console.error("Start scan error:", e);
      toast.error("Failed to start scan", { description: "Network error" });
    }
  };

  const handleStopScan = async () => {
    // Optional: Logic to stop scan / turn off M5? 
    // User only asked for start, but stop button is there.
    setIsScanning(false);
    toast.info("Scan Stopped");
  };

  return (
    <div className="h-full grid grid-cols-12 gap-6">
      {/* Camera Feed */}
      <div className="col-span-8 space-y-4">
        <div className="industrial-panel h-[60%] relative overflow-hidden">
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

          {/* Live camera view */}
          <div className="w-full h-full bg-black relative flex items-center justify-center">
            <img
              src="http://localhost:5001/camera/stream"
              className="max-w-full max-h-full aspect-[4/3] object-contain"
              alt="Live Feed"
              onError={(e) => {
                // If stream fails, maybe show a "Connecting..." or "No Signal" placeholder
                // For now, let's keep it simple or fallback to a placeholder color
                e.currentTarget.style.display = 'none';
                e.currentTarget.parentElement?.classList.add('bg-secondary');
              }}
            />
            {/* Fallback placeholder if image is hidden/error */}
            <div className="absolute inset-0 flex items-center justify-center -z-10">
              <div className="text-center">
                <Camera className="w-12 h-12 text-muted-foreground/50 mx-auto mb-2" />
                <p className="text-muted-foreground text-sm">Waiting for live feed...</p>
              </div>
            </div>
          </div>

          {/* Scan overlay - Kept visual indicator of active scan but removed progress bar */}
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

        {/* Controls */}
        <div className="industrial-panel p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <button
                onClick={handleStartScan}
                disabled={isScanning}
                className={`flex items-center gap-2 px-6 py-3 rounded-md font-medium transition-all ${isScanning
                  ? "bg-secondary text-muted-foreground cursor-not-allowed"
                  : "bg-success text-success-foreground hover:bg-success/90"
                  }`}
              >
                <Play className="w-5 h-5" />
                Start Scan
              </button>
              <button
                disabled={!isScanning}
                className={`flex items-center gap-2 px-6 py-3 rounded-md font-medium transition-all ${!isScanning
                  ? "bg-secondary text-muted-foreground cursor-not-allowed"
                  : "bg-warning text-warning-foreground hover:bg-warning/90"
                  }`}
              >
                <Pause className="w-5 h-5" />
                Pause
              </button>
              <button
                disabled={!isScanning}
                className={`flex items-center gap-2 px-6 py-3 rounded-md font-medium transition-all ${!isScanning
                  ? "bg-secondary text-muted-foreground cursor-not-allowed"
                  : "bg-destructive text-destructive-foreground hover:bg-destructive/90"
                  }`}
              >
                <Square className="w-5 h-5" />
                Stop
              </button>
            </div>

            {/* Progress bar removed as requested */}
            {/* <div className="flex items-center gap-6"> ... </div> */}
          </div>
        </div>
      </div>

      {/* Defect Panel */}
      <div className="col-span-4 industrial-panel p-4 flex flex-col">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-sm font-medium text-muted-foreground">DETECTED DEFECTS</h3>
          <span className="px-2 py-1 bg-destructive/10 text-destructive text-xs font-medium rounded">
            {defects.length} Found
          </span>
        </div>

        <div className="flex-1 overflow-y-auto space-y-3">
          {defects.map((defect) => (
            <motion.div
              key={defect.id}
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              className="p-3 bg-secondary/50 rounded-md border border-border"
            >
              <div className="flex items-start justify-between mb-2">
                <div className="flex items-center gap-2">
                  <AlertTriangle className={`w-4 h-4 ${defect.severity === "high" ? "text-destructive" :
                    defect.severity === "medium" ? "text-warning" : "text-muted-foreground"
                    }`} />
                  <span className="font-medium text-foreground text-sm">{defect.type}</span>
                </div>
                <span className={`px-2 py-0.5 text-xs rounded ${defect.severity === "high" ? "bg-destructive/20 text-destructive" :
                  defect.severity === "medium" ? "bg-warning/20 text-warning" : "bg-muted text-muted-foreground"
                  }`}>
                  {defect.severity.toUpperCase()}
                </span>
              </div>
              <p className="text-xs text-muted-foreground">{defect.location}</p>
              <p className="text-xs text-muted-foreground font-mono mt-1">{defect.timestamp}</p>
            </motion.div>
          ))}
        </div>

        {/* Summary */}
        <div className="mt-4 pt-4 border-t border-border">
          <div className="grid grid-cols-3 gap-2 text-center">
            <div className="p-2 bg-destructive/10 rounded">
              <p className="text-lg font-bold text-destructive font-mono">0</p>
              <p className="text-xs text-muted-foreground">High</p>
            </div>
            <div className="p-2 bg-warning/10 rounded">
              <p className="text-lg font-bold text-warning font-mono">1</p>
              <p className="text-xs text-muted-foreground">Medium</p>
            </div>
            <div className="p-2 bg-muted rounded">
              <p className="text-lg font-bold text-muted-foreground font-mono">1</p>
              <p className="text-xs text-muted-foreground">Low</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AutomaticMode;

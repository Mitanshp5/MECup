import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { ArrowUp, ArrowDown, ArrowLeft, ArrowRight, Home, RotateCcw, Zap, Lightbulb, AlertCircle } from "lucide-react";

import { useAuth } from "@/context/AuthContext";

const getApiBaseUrl = () => {
  if (!window.location.hostname) return 'http://127.0.0.1:5001';
  return `http://${window.location.hostname}:5001`;
};

const API_BASE_URL = getApiBaseUrl();

const ManualMode = () => {
  const { hasRole } = useAuth();
  const canControl = hasRole(['admin', 'operator']);

  const [position, setPosition] = useState({ x: 0, y: 0, z: 0 });
  const [speeds, setSpeeds] = useState({ x: 3500, y: 3500, z: 800 });
  const [jogDistance, setJogDistance] = useState(10);
  const [plcConnected, setPlcConnected] = useState(false);
  const [lightsOn, setLightsOn] = useState(false);

  // Poll PLC connection status and read current speeds
  useEffect(() => {
    const checkPlc = async () => {
      try {
        const res = await fetch(`${API_BASE_URL}/plc/control-status`);
        const data = await res.json();

        // Check m5/m4 etc but primarily we need m99 for servo
        // If control-status endpoint returns m99, use it.
        // Or if we need connection status, we might need to check how backend handles it.
        // Wait, get_plc_status is /plc/status (endpoints line 216).
        // control-status is /plc/control-status (endpoints line 347).
        // The original checkPlc used /plc/status which returns connection info.
        // We should probably call control-status as well to get M99.

        const statusRes = await fetch(`${API_BASE_URL}/plc/status`);
        const statusData = await statusRes.json();
        setPlcConnected(statusData.connected);

        if (statusData.connected) {
          try {
            const ctrlRes = await fetch(`${API_BASE_URL}/plc/control-status`);
            const ctrlData = await ctrlRes.json();
            if (ctrlData.m190 !== undefined && ctrlData.m190 !== null) {
              setServoEnabled(ctrlData.m190 === 1);
            }
            if (ctrlData.y0 !== undefined && ctrlData.y0 !== null) {
              setLightsOn(ctrlData.y0 === 1);
            }
          } catch (e) { console.error("Control status poll failed", e); }
        }

        // Read current servo speeds from PLC
        if (statusData.connected) {
          const speedsRes = await fetch(`${API_BASE_URL}/servo/speeds`);
          const speedsData = await speedsRes.json();
          if (speedsData.connected) {
            setSpeeds({ x: speedsData.x, y: speedsData.y, z: speedsData.z });
          }
        }
      } catch (e) {
        setPlcConnected(false);
      }
    };

    checkPlc();
    const interval = setInterval(checkPlc, 2000);
    return () => clearInterval(interval);
  }, []);

  const [servoEnabled, setServoEnabled] = useState(false);

  const handleServoToggle = async () => {
    try {
      await fetch(`${API_BASE_URL}/servo/enable`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ enable: true })
      });
      // State updated via polling
    } catch (error) {
      console.error("Failed to toggle servo:", error);
    }
  };

  const handleMove = async (command: string) => {
    if (!canControl) return; // Prevent unauthorized moves
    if (!servoEnabled) {
      alert("Please Enable Servo First!");
      return;
    }
    try {
      await fetch(`${API_BASE_URL}/servo/move`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ command })
      });
    } catch (error) {
      alert("Move Failed: " + error);
    }
  };

  const handleHome = () => {
    setPosition({ x: 0, y: 0, z: 0 });
  };

  return (
    <div className="h-full grid grid-cols-12 gap-6 relative">
      {/* Blocking Overlay */}
      {/* {!plcConnected && (
        <div className="absolute inset-0 z-50 bg-background/80 backdrop-blur-sm flex items-center justify-center rounded-lg border border-destructive/50">
          <div className="text-center space-y-4 p-8 bg-card border border-destructive rounded-xl shadow-lg">
            <div className="h-12 w-12 rounded-full bg-destructive/20 flex items-center justify-center mx-auto animate-pulse">
              <Zap className="h-6 w-6 text-destructive" />
            </div>
            <div>
              <h3 className="text-xl font-bold text-destructive">PLC DISCONNECTED</h3>
              <p className="text-muted-foreground mt-2">Manual controls are disabled.</p>
              <p className="text-xs text-muted-foreground mt-1">Please check connection in Settings.</p>
            </div>
          </div>
        </div>
      )} */}

      {/* Main Control Panel */}
      <div className="col-span-8 space-y-6">
        {/* Position Display */}
        <div className="industrial-panel p-6">
          <h3 className="text-sm font-medium text-muted-foreground mb-4">CURRENT POSITION</h3>
          <div className="grid grid-cols-3 gap-6">
            {["X", "Y", "Z"].map((axis) => (
              <div key={axis} className="text-center">
                <div className="data-display text-2xl font-bold text-primary mb-2">
                  {position[axis.toLowerCase() as "x" | "y" | "z"].toFixed(2)}
                  <span className="text-sm text-muted-foreground ml-1">mm</span>
                </div>
                <p className="text-sm text-muted-foreground">{axis}-Axis</p>
              </div>
            ))}
          </div>
        </div>

        {/* Jog Controls */}
        <div className={`industrial-panel p-6 ${!canControl ? 'opacity-50 pointer-events-none' : ''}`}>
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-sm font-medium text-muted-foreground">JOG CONTROLS</h3>
            {!canControl && <span className="text-xs text-destructive font-bold">READ ONLY</span>}
          </div>

          <div className="grid grid-cols-2 gap-8">
            {/* XY Control */}
            <div>
              <p className="text-xs text-muted-foreground mb-3 text-center">X/Y AXIS</p>
              <div className="grid grid-cols-3 gap-3 max-w-xs mx-auto">
                <div />
                <div /> {/* Placeholder for Up */}
                {/* <JogButton icon={ArrowUp} onClick={() => handleMove("y_fwd_12.5")} label="Y+ (12.5mm)" /> */}
                <div />

                <JogButton icon={ArrowLeft} onClick={() => handleMove("x_left_17")} label="X- (17mm)" />
                <div /> {/* Placeholder for Center */}
                {/* <button
                  onClick={() => handleMove("x_home")}
                  className="p-4 bg-primary/10 border border-primary/30 rounded-md text-primary hover:bg-primary/20 transition-colors"
                  title="X Home"
                >
                  <Home className="w-5 h-5 mx-auto" />
                </button> */}
                <div /> {/* Placeholder for Right */}
                {/* <JogButton icon={ArrowRight} onClick={() => handleMove("x_right_17")} label="X+ (17mm)" /> */}

                <div />
                <JogButton icon={ArrowDown} onClick={() => handleMove("y_back_12.5")} label="Y- (12.5mm)" />
                <div />
              </div>
            </div>

            {/* Z Control */}
            <div>
              <p className="text-xs text-muted-foreground mb-3 text-center">Z AXIS</p>
              <div className="flex flex-col gap-2 items-center">
                {/* <JogButton icon={ArrowUp} onClick={() => handleMove("z_up_5")} label="Z+ (5mm)" /> */}
                <div className="h-8" />
                <JogButton icon={ArrowDown} onClick={() => handleMove("z_down_5")} label="Z- (5mm)" />
              </div>
            </div>
          </div>
        </div>

        {/* Speed & Distance */}
        <div className="grid grid-cols-2 gap-6">
          <div className={`industrial-panel p-4 ${!canControl ? 'opacity-50 pointer-events-none' : ''}`}>
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-sm font-medium text-muted-foreground">AXIS SPEEDS</h3>
            </div>
            <div className="space-y-4">
              <div className="grid grid-cols-3 gap-2">
                {/* X Axis */}
                <div className="space-y-1">
                  <div className="flex justify-between text-xs">
                    <span className="font-bold">X</span>
                  </div>
                  <input
                    type="number"
                    min={0}
                    max={50000}
                    value={speeds.x}
                    onChange={(e) => setSpeeds(prev => ({ ...prev, x: Math.max(0, Math.min(50000, Number(e.target.value))) }))}
                    className="w-full bg-secondary border border-border rounded px-2 py-1 text-sm text-center"
                    disabled={!canControl}
                  />
                </div>
                {/* Y Axis */}
                <div className="space-y-1">
                  <div className="flex justify-between text-xs">
                    <span className="font-bold">Y</span>
                  </div>
                  <input
                    type="number"
                    min={0}
                    max={50000}
                    value={speeds.y}
                    onChange={(e) => setSpeeds(prev => ({ ...prev, y: Math.max(0, Math.min(50000, Number(e.target.value))) }))}
                    className="w-full bg-secondary border border-border rounded px-2 py-1 text-sm text-center"
                    disabled={!canControl}
                  />
                </div>
                {/* Z Axis */}
                <div className="space-y-1">
                  <div className="flex justify-between text-xs">
                    <span className="font-bold">Z</span>
                  </div>
                  <input
                    type="number"
                    min={0}
                    max={50000}
                    value={speeds.z}
                    onChange={(e) => setSpeeds(prev => ({ ...prev, z: Math.max(0, Math.min(50000, Number(e.target.value))) }))}
                    className="w-full bg-secondary border border-border rounded px-2 py-1 text-sm text-center"
                    disabled={!canControl}
                  />
                </div>
              </div>
              {/* <button
                onClick={() => {
                  fetch(`${API_BASE_URL}/servo/speeds`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(speeds)
                  })
                    .then(async res => {
                      if (!res.ok) {
                        const err = await res.json();
                        alert(err.detail || "Failed to set speeds");
                      } else {
                        alert("Speeds Set Successfully");
                      }
                    })
                    .catch(err => alert("Connection Error: " + err));
                }}
                className="w-full py-2 bg-primary text-primary-foreground rounded-md text-sm font-medium hover:bg-primary/90 transition-colors mt-2"
                disabled={!canControl}
              >
                SET SPEEDS
              </button> */}
            </div>
          </div>

          {/* <div className="industrial-panel p-4">
            <h3 className="text-sm font-medium text-muted-foreground mb-3">JOG DISTANCE</h3>
            <div className="flex gap-2">
              {[1, 10, 50, 100].map((dist) => (
                <button
                  key={dist}
                  onClick={() => setJogDistance(dist)}
                  className={`flex-1 py-2 rounded-md text-sm font-mono transition-colors ${jogDistance === dist
                    ? "bg-primary text-primary-foreground"
                    : "bg-secondary text-foreground hover:bg-secondary/80"
                    }`}
                >
                  {dist}mm
                </button>
              ))}
            </div>
          </div> */}
        </div>
      </div>

      {/* Side Panel */}
      <div className="col-span-4 space-y-4">
        {/* Live Camera View */}
        <div className="industrial-panel p-4">
          <h3 className="text-sm font-medium text-muted-foreground mb-3">LIVE CAMERA VIEW</h3>
          <div className="aspect-[4/3] bg-black rounded-md overflow-hidden border border-border relative">
            <img
              src={`${API_BASE_URL}/camera/stream`}
              alt="Camera Stream"
              className="w-full h-full object-contain"
              onError={(e) => {
                (e.target as HTMLImageElement).style.display = "none";
                const parent = (e.target as HTMLImageElement).parentElement;
                if (parent && !parent.querySelector('.offline-overlay')) {
                  const overlay = document.createElement('div');
                  overlay.className = 'offline-overlay absolute inset-0 flex flex-col items-center justify-center text-muted-foreground';
                  overlay.innerHTML = `
                    <svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" class="mb-3 opacity-50">
                      <path d="M14.5 4h-5L7 7H4a2 2 0 0 0-2 2v9a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V9a2 2 0 0 0-2-2h-3l-2.5-3z"/>
                      <circle cx="12" cy="13" r="3"/>
                    </svg>
                    <span class="text-sm font-medium">Camera Offline</span>
                  `;
                  parent.appendChild(overlay);
                }
              }}
              onLoad={(e) => {
                (e.target as HTMLImageElement).style.display = "block";
                const parent = (e.target as HTMLImageElement).parentElement;
                const overlay = parent?.querySelector('.offline-overlay');
                if (overlay) overlay.remove();
              }}
            />
          </div>
        </div>

        {/* Lights Control */}
        <div className="industrial-panel p-4">
          <h3 className="text-sm font-medium text-muted-foreground mb-3">LIGHT CONTROL</h3>
          <button
            onClick={async () => {
              try {
                const res = await fetch(`${API_BASE_URL}/plc/lights`, {
                  method: "POST",
                  headers: { "Content-Type": "application/json" },
                  body: JSON.stringify({})
                });
                const data = await res.json();
                if (data.success) {
                  setLightsOn(data.state);
                }
              } catch (e) {
                console.error("Failed to toggle lights:", e);
              }
            }}
            className={`w-full flex items-center justify-center gap-2 px-3 py-2.5 rounded-md font-medium text-sm transition-all ${lightsOn
              ? "bg-warning text-warning-foreground border-2 border-warning shadow-lg"
              : "bg-secondary text-foreground border border-border hover:bg-secondary/80"
              }`}
          >
            <Lightbulb className={`w-4 h-4 ${lightsOn ? "fill-current" : ""}`} />
            <span>{lightsOn ? "LIGHTS OFF" : "LIGHTS ON"}</span>
          </button>

          {/* Error Reset Button */}
          <button
            onClick={async () => {
              try {
                // Trigger reset (Pulse M15 handled by backend)
                await fetch(`${API_BASE_URL}/plc/error-reset`, {
                  method: "POST",
                  headers: { "Content-Type": "application/json" },
                  body: JSON.stringify({})
                });

              } catch (e) {
                console.error("Failed to reset error:", e);
              }
            }}
            className="w-full flex items-center justify-center gap-2 px-3 py-2.5 mt-3 rounded-md font-medium text-sm transition-all bg-destructive/10 text-destructive border border-destructive/30 hover:bg-destructive/20"
          >
            <AlertCircle className="w-4 h-4" />
            <span>ERROR RESET (M15)</span>
          </button>
        </div>

        {/* Servo Status */}
        <div className={`industrial-panel p-4 ${!canControl ? 'opacity-50 pointer-events-none' : ''}`}>
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-medium text-muted-foreground">SERVO CONTROL</h3>
            <button
              onClick={handleServoToggle}
              className={`px-3 py-1 rounded text-xs font-bold transition-all ${servoEnabled ? "bg-success text-success-foreground" : "bg-destructive text-destructive-foreground"}`}
              disabled={!canControl}
            >
              {servoEnabled ? "ON" : "OFF"}
            </button>
          </div>

          <div className="space-y-3">
            <div className="flex items-center justify-between p-3 bg-secondary/50 rounded-md">
              <div className="flex items-center gap-3">
                <Zap className={`w-4 h-4 ${servoEnabled ? "text-success" : "text-destructive"}`} />
                <span className="text-sm text-foreground">Servo Power (M190)</span>
              </div>
              <span className={`text-xs font-medium ${servoEnabled ? "text-success" : "text-destructive"}`}>
                {servoEnabled ? "ENABLED" : "DISABLED"}
              </span>
            </div>
          </div>
        </div>

        {/* Position History */}
        {/* <div className="industrial-panel p-4 flex-1">
          <h3 className="text-sm font-medium text-muted-foreground mb-4">POSITION LOG</h3>
          <div className="space-y-2 text-xs font-mono">
            <div className="text-muted-foreground">
              {`[${new Date().toLocaleTimeString()}] Position: X:${position.x} Y:${position.y} Z:${position.z}`}
            </div>
          </div>
        </div> */}
      </div>
    </div>
  );
};

const JogButton = ({ icon: Icon, onClick, label }: { icon: React.ElementType; onClick: () => void; label: string }) => (
  <motion.button
    whileHover={{ scale: 1.05 }}
    whileTap={{ scale: 0.95 }}
    onClick={onClick}
    className="p-4 bg-secondary border border-border rounded-md text-foreground hover:bg-secondary/80 hover:border-primary/50 transition-colors"
    title={label}
  >
    <Icon className="w-5 h-5 mx-auto" />
  </motion.button>
);

export default ManualMode;

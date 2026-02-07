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
  const [lightMode, setLightMode] = useState<'off' | 'white' | 'green'>('off');
  const [directionState, setDirectionState] = useState({ up: false, down: false, left: false, right: false });

  // Poll PLC connection status and read current speeds
  useEffect(() => {
    // checkPlc definition
    let timeoutId: NodeJS.Timeout;
    const checkPlc = async () => {
      try {
        const res = await fetch(`${API_BASE_URL}/plc/control-status`);
        const data = await res.json();


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
            // Parse new bits if available
            if (ctrlData.m103 !== undefined) {
              if (ctrlData.m103) setLightMode('white');
              else if (ctrlData.m104) setLightMode('green');
              else setLightMode('off');
            }
            if (ctrlData.m68 !== undefined) {
              setDirectionState({
                up: ctrlData.m68 === 0,
                down: ctrlData.m69 === 0,
                right: ctrlData.m70 === 0,
                left: ctrlData.m71 === 0
              });
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

      // Schedule next poll
      timeoutId = setTimeout(checkPlc, 2000);
    };

    checkPlc();
    // const interval = setInterval(checkPlc, 2000);
    return () => clearTimeout(timeoutId);
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

  const toggleDirection = async (direction: string, currentState: boolean) => {
    // Optimistic update
    setDirectionState(prev => ({ ...prev, [direction]: !currentState }));

    try {
      const res = await fetch(`${API_BASE_URL}/plc/light-direction`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ direction, state: !currentState })
      });
      if (!res.ok) throw new Error("Failed to toggle light");
    } catch (e) {
      console.error(e);
      // Revert on failure
      setDirectionState(prev => ({ ...prev, [direction]: currentState }));
    }
  };

  return (
    <div className="h-full grid grid-cols-12 gap-6 relative">
      {/* Blocking Overlay */}
      {!plcConnected && (
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
      )}

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

        {/* Speed & Servo Control Grid */}
        <div className="grid grid-cols-2 gap-6">
          {/* Axis Speeds */}
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
            </div>
          </div>

          {/* Servo Control (Moved Here) */}
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

              {/* Error Reset */}
              <button
                onClick={async () => {
                  try {
                    await fetch(`${API_BASE_URL}/plc/error-reset`, {
                      method: "POST",
                      headers: { "Content-Type": "application/json" },
                      body: JSON.stringify({})
                    });
                  } catch (e) { console.error("Reset failed", e); }
                }}
                className="w-full flex items-center justify-center gap-2 px-3 py-2 rounded-md font-medium text-xs bg-destructive text-destructive-foreground hover:bg-destructive/90 transition-all shadow-sm"
              >
                <AlertCircle className="w-3 h-3" />
                <span>ERROR RESET (M15)</span>
              </button>
            </div>
          </div>
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

        {/* Advanced Light Control Panel */}
        <div className="industrial-panel p-6 relative overflow-hidden flex flex-col items-center justify-center min-h-[400px]">
          {/* Background Grid/Effect */}
          <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,_var(--tw-gradient-stops))] from-white/5 via-transparent to-transparent opacity-50 pointer-events-none" />

          <h3 className="text-xs font-bold tracking-widest text-muted-foreground/70 mb-8 z-10">LIGHTING ARRAY CONTROL</h3>

          <div className="relative w-full max-w-[300px] aspect-square flex items-center justify-center">

            {/* Light Rays Layer */}
            <div className="absolute inset-0 pointer-events-none z-0">
              {/* Up Ray */}
              <div className={`absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-[120%] w-16 h-32 bg-gradient-to-t from-primary/20 to-transparent transition-all duration-300 ${directionState.up ? 'opacity-100' : 'opacity-0'}`} />
              {/* Down Ray */}
              <div className={`absolute top-1/2 left-1/2 -translate-x-1/2 translate-y-[20%] w-16 h-32 bg-gradient-to-b from-primary/20 to-transparent transition-all duration-300 ${directionState.down ? 'opacity-100' : 'opacity-0'}`} />
              {/* Left Ray */}
              <div className={`absolute top-1/2 left-1/2 -translate-x-[120%] -translate-y-1/2 w-32 h-16 bg-gradient-to-l from-primary/20 to-transparent transition-all duration-300 ${directionState.left ? 'opacity-100' : 'opacity-0'}`} />
              {/* Right Ray */}
              <div className={`absolute top-1/2 left-1/2 translate-x-[20%] -translate-y-1/2 w-32 h-16 bg-gradient-to-r from-primary/20 to-transparent transition-all duration-300 ${directionState.right ? 'opacity-100' : 'opacity-0'}`} />
            </div>

            {/* Controls Grid - Rotated 45deg to fit or just standard cross? Standard cross for now based on previous requests */}
            <div className="relative z-10 grid grid-cols-3 grid-rows-3 gap-4 w-full h-full">

              {/* Top Center: Controls DOWN */}
              <div className="col-start-2 row-start-1 flex justify-center items-end">
                <LightPanel
                  active={directionState.down}
                  disabled={lightMode === 'off'}
                  onClick={() => toggleDirection('down', directionState.down)}
                  orientation="vertical"
                />
              </div>

              {/* Middle Left: LEFT */}
              <div className="col-start-1 row-start-2 flex justify-end items-center">
                <LightPanel
                  active={directionState.left}
                  disabled={lightMode === 'off'}
                  onClick={() => toggleDirection('left', directionState.left)}
                  orientation="horizontal"
                />
              </div>

              {/* Center: MODE TOGGLE */}
              <div className="col-start-2 row-start-2 flex justify-center items-center">
                <button
                  onClick={async () => {
                    const nextMode = lightMode === 'off' ? 'white' : lightMode === 'white' ? 'green' : 'off';
                    try {
                      await fetch(`${API_BASE_URL}/plc/light-mode`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ mode: nextMode })
                      });
                      setLightMode(nextMode); // Optimistic update
                    } catch (e) { console.error(e); }
                  }}
                  className={`w-20 h-20 rounded-full flex items-center justify-center transition-all duration-300 shadow-lg border-2 z-20 relative overflow-hidden group
                            ${lightMode === 'off' ? 'bg-zinc-800 border-zinc-700 text-zinc-600' :
                      lightMode === 'white' ? 'bg-white border-white text-zinc-900 shadow-[0_0_30px_rgba(255,255,255,0.4)]' :
                        'bg-emerald-500 border-emerald-400 text-white shadow-[0_0_30px_rgba(16,185,129,0.4)]'
                    }`}
                >
                  {/* Shine effect */}
                  <div className="absolute inset-0 bg-gradient-to-br from-white/40 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500" />

                  <div className="flex flex-col items-center gap-1">
                    <Lightbulb className={`w-8 h-8 ${lightMode !== 'off' ? 'fill-current' : ''}`} />
                    <span className="text-[10px] font-bold uppercase tracking-wider">{lightMode}</span>
                  </div>
                </button>
              </div>

              {/* Middle Right: RIGHT */}
              <div className="col-start-3 row-start-2 flex justify-start items-center">
                <LightPanel
                  active={directionState.right}
                  disabled={lightMode === 'off'}
                  onClick={() => toggleDirection('right', directionState.right)}
                  orientation="horizontal"
                />
              </div>

              {/* Bottom Center: Controls UP */}
              <div className="col-start-2 row-start-3 flex justify-center items-start">
                <LightPanel
                  active={directionState.up}
                  disabled={lightMode === 'off'}
                  onClick={() => toggleDirection('up', directionState.up)}
                  orientation="vertical"
                />
              </div>

            </div>
          </div>
        </div>
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

const LightPanel = ({ active, disabled, onClick, orientation }: { active: boolean, disabled: boolean, onClick: () => void, orientation: 'horizontal' | 'vertical' }) => {
  return (
    <motion.button
      onClick={() => !disabled && onClick()}
      whileTap={!disabled ? { scale: 0.95 } : {}}
      disabled={disabled}
      className={`
                relative flex items-center justify-center transition-all duration-300
                ${orientation === 'vertical' ? 'w-24 h-14' : 'w-14 h-24'}
                ${disabled ? 'opacity-30 cursor-not-allowed grayscale' : 'cursor-pointer'}
            `}
    >
      {/* Base Glass Layer */}
      <div className={`
                absolute inset-0 rounded-xl border backdrop-blur-md transition-all duration-300
                ${active
          ? 'bg-primary/20 border-primary shadow-[0_0_20px_rgba(var(--primary),0.2)]'
          : 'bg-card/40 border-white/5 hover:bg-card/60'
        }
            `} />

      {/* Brightness Indicator Bar */}
      <div className={`
                absolute bg-current transition-all duration-300 rounded-full
                ${active ? 'opacity-100' : 'opacity-20'}
                ${orientation === 'vertical'
          ? 'bottom-2 left-2 right-2 h-1'
          : 'right-2 top-2 bottom-2 w-1'
        }
                ${active ? 'bg-primary shadow-[0_0_10px_currentColor]' : 'bg-muted-foreground'}
            `} />

      {/* Glow Core */}
      {active && (
        <div className="absolute inset-0 rounded-xl bg-primary/10 animate-pulse" />
      )}

    </motion.button>
  );
};

export default ManualMode;

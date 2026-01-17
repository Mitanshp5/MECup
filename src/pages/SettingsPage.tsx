import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { Save, Network, Camera, Palette, Monitor, Shield, Bell, Database } from "lucide-react";

const SettingsPage = () => {
  const [plcSettings, setPlcSettings] = useState({
    ip: "169.254.180.21",
    port: "5000",
    timeout: "5000",
  });

  const [cameraSettings, setCameraSettings] = useState({
    exposure: "5000",
    gain: "0",
  });

  const [theme, setTheme] = useState("dark");

  // Sync settings from backend on mount
  useEffect(() => {
    // Fetch PLC Settings
    fetch("http://localhost:5001/plc/status")
      .then(res => res.json())
      .then(data => {
        console.log("Fetched PLC Settings:", data);
        if (data.ip && data.port) {
          setPlcSettings(prev => ({ ...prev, ip: data.ip, port: String(data.port) }));
        }
      })
      .catch(err => console.error("Failed to fetch PLC settings:", err));

    // Fetch Camera Settings
    fetch("http://localhost:5001/camera/settings")
      .then(res => res.json())
      .then(data => {
        console.log("Fetched Camera Settings:", data);
        setCameraSettings({
          exposure: String(data.exposure),
          gain: String(data.gain)
        });
      })
      .catch(err => console.error("Failed to fetch camera settings:", err));
  }, []);

  const handleSave = async () => {
    try {
      // Save PLC Settings
      const plcResponse = await fetch("http://localhost:5001/plc/connect", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          ip: plcSettings.ip,
          port: parseInt(plcSettings.port),
        }),
      });
      const plcData = await plcResponse.json();

      // Save Camera Settings
      const camResponse = await fetch("http://localhost:5001/camera/settings", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          exposure: parseFloat(cameraSettings.exposure),
          gain: parseFloat(cameraSettings.gain)
        }),
      });
      const camData = await camResponse.json();

      if (plcData.connected && camData.success) {
        alert("Settings saved! PLC Connected. Camera settings applied.");
      } else {
        let msg = "Settings saved with warnings:\n";
        if (!plcData.connected) msg += `- PLC: ${plcData.error || "Failed"}\n`;
        if (!camData.success) msg += `- Camera: ${camData.message || "Failed"}\n`;
        alert(msg);
      }
    } catch (error) {
      console.error("Error saving settings:", error);
      alert("Failed to save settings. Check console for details.");
    }
  };

  return (
    <div className="h-full overflow-y-auto">
      <div className="max-w-4xl mx-auto space-y-6">
        {/* PLC Settings */}
        <div className="industrial-panel p-6">
          <div className="flex items-center gap-3 mb-6">
            <div className="w-10 h-10 rounded-md bg-primary/10 flex items-center justify-center border border-primary/20">
              <Network className="w-5 h-5 text-primary" />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-foreground">PLC Connection</h3>
              <p className="text-sm text-muted-foreground">Configure the PLC connection settings</p>
            </div>
          </div>

          <div className="grid grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-muted-foreground mb-2">IP Address</label>
              <input
                type="text"
                value={plcSettings.ip}
                onChange={(e) => setPlcSettings(prev => ({ ...prev, ip: e.target.value }))}
                className="w-full px-4 py-2.5 bg-secondary border border-border rounded-md text-foreground font-mono focus:outline-none focus:ring-1 focus:ring-primary"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-muted-foreground mb-2">Port</label>
              <input
                type="text"
                value={plcSettings.port}
                onChange={(e) => setPlcSettings(prev => ({ ...prev, port: e.target.value }))}
                className="w-full px-4 py-2.5 bg-secondary border border-border rounded-md text-foreground font-mono focus:outline-none focus:ring-1 focus:ring-primary"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-muted-foreground mb-2">Timeout (ms)</label>
              <input
                type="text"
                value={plcSettings.timeout}
                onChange={(e) => setPlcSettings(prev => ({ ...prev, timeout: e.target.value }))}
                className="w-full px-4 py-2.5 bg-secondary border border-border rounded-md text-foreground font-mono focus:outline-none focus:ring-1 focus:ring-primary"
              />
            </div>
          </div>
        </div>

        {/* Camera Settings */}
        <div className="industrial-panel p-6">
          <div className="flex items-center gap-3 mb-6">
            <div className="w-10 h-10 rounded-md bg-primary/10 flex items-center justify-center border border-primary/20">
              <Camera className="w-5 h-5 text-primary" />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-foreground">Camera Settings</h3>
              <p className="text-sm text-muted-foreground">Configure camera capture parameters</p>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-muted-foreground mb-2">Exposure Time (µs)</label>
              <input
                type="number"
                value={cameraSettings.exposure}
                onChange={(e) => setCameraSettings(prev => ({ ...prev, exposure: e.target.value }))}
                className="w-full px-4 py-2.5 bg-secondary border border-border rounded-md text-foreground focus:outline-none focus:ring-1 focus:ring-primary"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-muted-foreground mb-2">Gain</label>
              <input
                type="number"
                value={cameraSettings.gain}
                onChange={(e) => setCameraSettings(prev => ({ ...prev, gain: e.target.value }))}
                className="w-full px-4 py-2.5 bg-secondary border border-border rounded-md text-foreground focus:outline-none focus:ring-1 focus:ring-primary"
              />
            </div>
          </div>
        </div>

        {/* Theme Settings */}
        <div className="industrial-panel p-6">
          <div className="flex items-center gap-3 mb-6">
            <div className="w-10 h-10 rounded-md bg-primary/10 flex items-center justify-center border border-primary/20">
              <Palette className="w-5 h-5 text-primary" />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-foreground">Appearance</h3>
              <p className="text-sm text-muted-foreground">Customize the application theme</p>
            </div>
          </div>

          <div className="flex gap-4">
            {["dark", "light", "system"].map((t) => (
              <button
                key={t}
                onClick={() => setTheme(t)}
                className={`flex-1 py-3 rounded-md font-medium capitalize transition-colors ${theme === t
                  ? "bg-primary text-primary-foreground"
                  : "bg-secondary text-foreground hover:bg-secondary/80"
                  }`}
              >
                {t}
              </button>
            ))}
          </div>
        </div>

        {/* Other Settings */}
        <div className="grid grid-cols-2 gap-6">
          <SettingsCard
            icon={Monitor}
            title="Display"
            description="Screen brightness and orientation"
          />
          <SettingsCard
            icon={Shield}
            title="Security"
            description="Access control and permissions"
          />
          <SettingsCard
            icon={Bell}
            title="Notifications"
            description="Alert preferences and sounds"
          />
          <SettingsCard
            icon={Database}
            title="Data Management"
            description="Storage and backup options"
          />
        </div>

        {/* Save Button */}
        <div className="flex justify-end">
          <button
            onClick={handleSave}
            className="flex items-center gap-2 px-6 py-3 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 transition-colors"
          >
            <Save className="w-5 h-5" />
            Save Changes
          </button>
        </div>
      </div>
    </div>
  );
};

const SettingsCard = ({ icon: Icon, title, description }: { icon: React.ElementType; title: string; description: string }) => (
  <motion.div
    whileHover={{ scale: 1.02 }}
    className="industrial-panel p-4 cursor-pointer transition-all hover:border-primary/50"
  >
    <div className="flex items-center gap-3">
      <div className="w-10 h-10 rounded-md bg-secondary flex items-center justify-center">
        <Icon className="w-5 h-5 text-muted-foreground" />
      </div>
      <div>
        <h4 className="font-medium text-foreground">{title}</h4>
        <p className="text-xs text-muted-foreground">{description}</p>
      </div>
    </div>
  </motion.div>
);

export default SettingsPage;

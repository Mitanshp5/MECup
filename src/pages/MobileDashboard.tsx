import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { Activity, FileText, Heart, ChevronRight, Cpu } from "lucide-react";

const MobileDashboard = () => {
  const navigate = useNavigate();

  const pages = [
    {
      id: "health",
      title: "System Health",
      description: "Monitor cameras, PLC, gantry axes, and system resources in real-time",
      icon: Heart,
      path: "/mobile/health",
      color: "text-emerald-400",
      bgColor: "bg-emerald-400/10",
      borderColor: "border-emerald-400/30",
    },
    {
      id: "report",
      title: "Scan Reports",
      description: "View past inspection scans, defect summaries, and detailed reports",
      icon: FileText,
      path: "/mobile/report",
      color: "text-blue-400",
      bgColor: "bg-blue-400/10",
      borderColor: "border-blue-400/30",
    },
  ];

  return (
    <div className="min-h-screen bg-background flex flex-col">
      {/* Header */}
      <div className="sticky top-0 z-50 bg-background/95 backdrop-blur border-b border-border">
        <div className="px-4 py-3">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-primary/10 flex items-center justify-center border border-primary/30 p-1">
              <img
                src="/assets/icon.ico"
                alt="CON-SOL-E"
                className="w-full h-full object-contain"
              />
            </div>
            <div>
              <h1 className="text-base font-bold text-foreground leading-none">CON-SOL-E</h1>
              <p className="text-[10px] text-muted-foreground font-mono">Mobile Dashboard</p>
            </div>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 px-4 py-4 space-y-6">
        {/* Welcome Section */}
        <div>
          <h2 className="text-xl font-bold text-foreground mb-0.5">Welcome</h2>
          <p className="text-xs text-muted-foreground">Select a module to monitor</p>
        </div>

        {/* Navigation Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {pages.map((page, index) => {
            const Icon = page.icon;
            return (
              <motion.button
                key={page.id}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.1, duration: 0.2 }}
                onClick={() => navigate(page.path)}
                className={`w-full text-left bg-card/40 rounded-xl p-4 border ${page.borderColor} active:scale-[0.98] transition-all touch-manipulation`}
              >
                <div className="flex items-center gap-3">
                  <div className={`w-10 h-10 rounded-lg ${page.bgColor} flex items-center justify-center flex-shrink-0`}>
                    <Icon className={`w-5 h-5 ${page.color}`} />
                  </div>
                  <div className="flex-1 min-w-0">
                    <h3 className="text-sm font-semibold text-foreground">{page.title}</h3>
                    <p className="text-[11px] text-muted-foreground leading-tight mt-0.5 truncate">{page.description}</p>
                  </div>
                  <ChevronRight className="w-4 h-4 text-muted-foreground/50 flex-shrink-0" />
                </div>
              </motion.button>
            );
          })}
        </div>

        {/* About Info (Aligned with Desktop Dashboard) */}
        <div className="bg-card/20 rounded-xl p-4 border border-border/50">
          <div className="flex items-center gap-3 mb-3">
            <div className="w-8 h-8 rounded-lg bg-primary/10 flex items-center justify-center border border-primary/20 flex-shrink-0">
              <Cpu className="w-4 h-4 text-primary" />
            </div>
            <h3 className="text-sm font-bold text-foreground uppercase tracking-wide">About Spectra-Scan</h3>
          </div>

          <p className="text-xs text-muted-foreground leading-relaxed mb-4">
            Spectra-Scan is an advanced automated inspection system developed by <span className="text-primary font-semibold">Team CON-SOL-E 5.0</span>.
          </p>

          {/* MECUP Badge */}
          <div className="flex items-center gap-3 bg-secondary/30 rounded-lg p-3 border border-border">
            <img
              src="/assets/MECUP_logo.png"
              alt="MECUP"
              className="h-10 w-10 object-contain flex-shrink-0"
            />
            <div>
              <div className="text-[10px] text-muted-foreground uppercase tracking-wide font-medium">Competition</div>
              <div className="text-xl font-bold text-foreground tracking-tight leading-none">MECUP</div>
            </div>
          </div>
        </div>

      </div>

      {/* Bottom Status Bar */}
      <div className="px-4 py-3 border-t border-border bg-card/20 mt-auto">
        <div className="flex items-center justify-center gap-2 text-[10px] text-muted-foreground/60">
          <Activity className="w-3 h-3" />
          <span className="font-mono">CON-SOL-E v5.0 Mobile</span>
        </div>
      </div>
    </div>
  );
};

export default MobileDashboard;

import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { Activity, FileText, Heart, ChevronRight } from "lucide-react";

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
        <div className="px-5 py-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center border border-primary/30 p-1.5">
              <img
                src="/assets/icon.ico"
                alt="CON-SOL-E"
                className="w-full h-full object-contain"
              />
            </div>
            <div>
              <h1 className="text-lg font-bold text-foreground">CON-SOL-E</h1>
              <p className="text-xs text-muted-foreground font-mono">Mobile Dashboard</p>
            </div>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 px-5 py-6">
        {/* Welcome Section */}
        <div className="mb-8">
          <h2 className="text-2xl font-bold text-foreground mb-1">Welcome</h2>
          <p className="text-sm text-muted-foreground">Select a section to monitor your system</p>
        </div>

        {/* Navigation Cards */}
        <div className="space-y-4">
          {pages.map((page, index) => {
            const Icon = page.icon;
            return (
              <motion.button
                key={page.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.1, duration: 0.3 }}
                onClick={() => navigate(page.path)}
                className={`w-full text-left bg-card/50 rounded-xl p-5 border ${page.borderColor} active:scale-[0.98] transition-transform`}
              >
                <div className="flex items-center gap-4">
                  <div className={`w-14 h-14 rounded-xl ${page.bgColor} flex items-center justify-center flex-shrink-0`}>
                    <Icon className={`w-7 h-7 ${page.color}`} />
                  </div>
                  <div className="flex-1 min-w-0">
                    <h3 className="text-base font-semibold text-foreground mb-1">{page.title}</h3>
                    <p className="text-xs text-muted-foreground leading-relaxed">{page.description}</p>
                  </div>
                  <ChevronRight className="w-5 h-5 text-muted-foreground flex-shrink-0" />
                </div>
              </motion.button>
            );
          })}
        </div>
      </div>

      {/* Bottom Status Bar */}
      <div className="px-5 py-4 border-t border-border bg-card/30">
        <div className="flex items-center justify-center gap-2 text-xs text-muted-foreground">
          <Activity className="w-3 h-3" />
          <span className="font-mono">CON-SOL-E v5.0</span>
        </div>
      </div>
    </div>
  );
};

export default MobileDashboard;

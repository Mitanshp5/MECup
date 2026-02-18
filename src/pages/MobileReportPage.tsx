import { useState, useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import {
  ArrowLeft,
  Search,
  CheckCircle,
  AlertTriangle,
  Eye,
  FileText,
  Calendar,
  Clock,
} from "lucide-react";
import { API_BASE_URL } from "@/lib/api-config";
import PrintableReport from "@/components/reports/PrintableReport";
import type { ScanDetails } from "@/components/reports/PrintableReport";

interface ScanRecord {
  id: string;
  date: string;
  time: string;
  image_count: number;
  defect_count: number;
  status: "pass" | "fail";
  scanned_by?: string;
}

const MobileReportPage = () => {
  const navigate = useNavigate();
  const isMounted = useRef(true);
  const [scans, setScans] = useState<ScanRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedScan, setSelectedScan] = useState<ScanDetails | null>(null);
  const [showReport, setShowReport] = useState(false);

  useEffect(() => {
    isMounted.current = true;
    return () => {
      isMounted.current = false;
    };
  }, []);

  useEffect(() => {
    const fetchScans = async () => {
      try {
        const res = await fetch(`${API_BASE_URL}/scans/list`);
        if (!isMounted.current) return;
        const data = await res.json();
        if (!isMounted.current) return;
        setScans(data.scans || []);
      } catch (e) {
        console.error("Failed to fetch scans:", e);
      } finally {
        if (isMounted.current) setLoading(false);
      }
    };
    fetchScans();
  }, []);

  const handleSelectScan = async (scanId: string) => {
    try {
      const res = await fetch(`${API_BASE_URL}/scans/${scanId}`);
      if (!isMounted.current) return;
      const data = await res.json();
      if (!isMounted.current) return;
      setSelectedScan(data);
      setShowReport(false);
    } catch (e) {
      console.error("Failed to fetch scan details:", e);
    }
  };

  const filteredScans = scans.filter(
    (scan) =>
      scan.id.toLowerCase().includes(searchTerm.toLowerCase()) ||
      scan.date.toLowerCase().includes(searchTerm.toLowerCase())
  );

  // List View
  if (!selectedScan) {
    return (
      <div className="min-h-screen bg-background flex flex-col">
        {/* Header */}
        <div className="sticky top-0 z-50 bg-background/95 backdrop-blur border-b border-border">
          <div className="px-4 py-3">
            <div className="flex items-center gap-3 mb-3">
              <button
                onClick={() => navigate("/mobile")}
                className="w-10 h-10 flex items-center justify-center rounded-full bg-card/60 border border-border/50 active:scale-95 transition-transform"
              >
                <ArrowLeft className="w-5 h-5" />
              </button>
              <h1 className="text-xl font-bold flex items-center gap-2">
                <FileText className="w-5 h-5 text-blue-400" />
                Scan Reports
              </h1>
            </div>

            {/* Search */}
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
              <input
                type="text"
                placeholder="Search by ID or date..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-10 pr-4 py-2.5 bg-card/40 border border-border/50 rounded-lg text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-primary text-sm"
              />
            </div>
          </div>
        </div>

        {/* Scan List */}
        <div className="flex-1 px-4 py-3 grid grid-cols-1 md:grid-cols-2 gap-2 content-start">
          {loading ? (
            <div className="col-span-full py-12 text-center text-muted-foreground text-sm">Loading scans...</div>
          ) : filteredScans.length === 0 ? (
            <div className="col-span-full py-12 text-center text-muted-foreground text-sm">No scans found</div>
          ) : (
            filteredScans.map((scan) => (
              <motion.button
                key={scan.id}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                onClick={() => handleSelectScan(scan.id)}
                className="w-full text-left bg-card/40 rounded-lg p-3 border border-border/50 active:scale-[0.98] transition-transform"
              >
                <div className="flex items-center justify-between mb-2">
                  <span className="font-mono text-xs text-muted-foreground truncate max-w-[60%]">
                    {scan.id}
                  </span>
                  <span
                    className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium ${scan.status === "pass"
                      ? "bg-success/10 text-success"
                      : "bg-destructive/10 text-destructive"
                      }`}
                  >
                    {scan.status === "pass" ? (
                      <CheckCircle className="w-3 h-3" />
                    ) : (
                      <AlertTriangle className="w-3 h-3" />
                    )}
                    {scan.status.toUpperCase()}
                  </span>
                </div>
                <div className="flex items-center justify-between text-xs">
                  <span className="text-muted-foreground">
                    {scan.date} • {scan.time}
                  </span>
                  <div className="flex gap-3">
                    <span className="text-muted-foreground">
                      {scan.image_count} img
                    </span>
                    <span
                      className={
                        scan.defect_count > 0 ? "text-warning" : "text-success"
                      }
                    >
                      {scan.defect_count} defects
                    </span>
                  </div>
                </div>
              </motion.button>
            ))
          )}
        </div>
      </div>
    );
  }

  // Full Report View — uses the shared PrintableReport (identical to desktop PDF)
  if (showReport) {
    return (
      <div className="min-h-screen bg-background">
        <PrintableReport scan={selectedScan} onBack={() => setShowReport(false)} />
      </div>
    );
  }

  // Detail View (scan summary + view report button)
  return (
    <div className="min-h-screen bg-background flex flex-col">
      {/* Header */}
      <div className="sticky top-0 z-50 bg-background/95 backdrop-blur border-b border-border">
        <div className="px-4 py-3 flex items-center gap-3">
          <button
            onClick={() => setSelectedScan(null)}
            className="w-10 h-10 flex items-center justify-center rounded-full bg-card/60 border border-border/50 active:scale-95 transition-transform"
          >
            <ArrowLeft className="w-5 h-5" />
          </button>
          <h1 className="text-lg font-bold">Scan Details</h1>
        </div>
      </div>

      {/* Details Content */}
      <div className="flex-1 px-4 py-4 space-y-3">
        {/* Status Banner */}
        <div
          className={`rounded-lg p-4 flex items-center gap-3 ${selectedScan.status === "pass"
            ? "bg-success/10 border border-success/30"
            : "bg-destructive/10 border border-destructive/30"
            }`}
        >
          {selectedScan.status === "pass" ? (
            <CheckCircle className="w-8 h-8 text-success flex-shrink-0" />
          ) : (
            <AlertTriangle className="w-8 h-8 text-destructive flex-shrink-0" />
          )}
          <div>
            <p className={`text-lg font-bold ${selectedScan.status === "pass" ? "text-success" : "text-destructive"}`}>
              {selectedScan.status === "pass" ? "PASSED" : "FAILED"}
            </p>
            <p className="text-xs text-muted-foreground">Inspection Result</p>
          </div>
        </div>

        {/* Info Grid */}
        <div className="bg-card/40 rounded-lg p-4 border border-border/50 space-y-3">
          <DetailRow label="Scan ID" value={selectedScan.id} mono />
          <DetailRow label="Date" value={selectedScan.date} icon={<Calendar className="w-3.5 h-3.5" />} />
          <DetailRow label="Time" value={selectedScan.time} icon={<Clock className="w-3.5 h-3.5" />} />
          <DetailRow label="Images Scanned" value={String(selectedScan.image_count)} />
          <DetailRow label="Total Defects" value={String(selectedScan.total_defects)} highlight={selectedScan.total_defects > 0} />
          <DetailRow label="Scanned By" value={selectedScan.scanned_by || "Unknown"} />
        </div>

        {/* Defect Type Summary */}
        {Object.keys(selectedScan.defect_types).length > 0 && (
          <div className="bg-card/40 rounded-lg p-4 border border-border/50">
            <h3 className="text-sm font-medium text-muted-foreground mb-3">DEFECT BREAKDOWN</h3>
            <div className="flex flex-wrap gap-2">
              {Object.entries(selectedScan.defect_types).map(([type, count]) => (
                <span
                  key={type}
                  className="px-2.5 py-1 bg-warning/10 text-warning text-xs rounded border border-warning/20 font-medium"
                >
                  {type}: {count}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* View Report Button */}
        <motion.button
          whileTap={{ scale: 0.97 }}
          onClick={() => setShowReport(true)}
          className="w-full py-3.5 bg-primary text-primary-foreground rounded-lg font-medium flex items-center justify-center gap-2 shadow-lg"
        >
          <Eye className="w-4 h-4" />
          View Full Inspection Report
        </motion.button>
      </div>
    </div>
  );
};

const DetailRow = ({
  label,
  value,
  mono,
  icon,
  highlight,
}: {
  label: string;
  value: string;
  mono?: boolean;
  icon?: React.ReactNode;
  highlight?: boolean;
}) => (
  <div className="flex items-center justify-between text-sm">
    <span className="text-muted-foreground flex items-center gap-1.5">
      {icon}
      {label}
    </span>
    <span
      className={`${mono ? "font-mono text-xs" : ""} ${highlight ? "text-warning font-bold" : "text-foreground"} font-medium`}
    >
      {value}
    </span>
  </div>
);

export default MobileReportPage;

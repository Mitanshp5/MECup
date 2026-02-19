import { useState, useEffect, useRef } from "react";
import { motion } from "framer-motion";
import { Search, Filter, Download, Eye, Calendar, User, CheckCircle, AlertTriangle, X, Image as ImageIcon, Trash2, FileText, Loader2 } from "lucide-react";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { API_BASE_URL } from "@/lib/api-config";
import ScanReport from "@/components/reports/ScanReport";

interface ScanRecord {
  id: string;
  date: string;
  time: string;
  image_count: number;
  defect_count: number;
  status: "pass" | "fail";
  scanned_by?: string;
}

interface ScanDetails {
  id: string;
  date: string;
  time: string;
  image_count: number;
  images: string[];
  total_defects: number;
  defect_types: { [key: string]: number };
  defects: {
    image: string;
    overlay: string;
    overlay_url: string;
    image_url?: string;
    defect_count?: number;
    defect_details?: { type: string; pixel_count: number; area_ratio: number }[];
  }[];
  status: "pass" | "fail";
  scanned_by?: string;
}

const PastScans = () => {
  const isMounted = useRef(true);
  const [scans, setScans] = useState<ScanRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");
  const [displayCount, setDisplayCount] = useState(5);
  const [selectedScan, setSelectedScan] = useState<ScanDetails | null>(null);
  const [selectedImage, setSelectedImage] = useState<string | null>(null);
  const [scanToDelete, setScanToDelete] = useState<string | null>(null);
  const [isGeneratingReport, setIsGeneratingReport] = useState(false);
  const [reportGenerated, setReportGenerated] = useState<{[key: string]: boolean}>({});

  const [showFullDetails, setShowFullDetails] = useState(false);

  // Cleanup on unmount
  useEffect(() => {
    isMounted.current = true;
    return () => {
      isMounted.current = false;
    };
  }, []);

  // Fetch scans on mount
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
        if (isMounted.current) {
          setLoading(false);
        }
      }
    };
    fetchScans();
  }, []);

  // Fetch scan details when selected
  const handleSelectScan = async (scanId: string) => {
    try {
      const res = await fetch(`${API_BASE_URL}/scans/${scanId}`);
      if (!isMounted.current) return;
      const data = await res.json();
      if (!isMounted.current) return;
      setSelectedScan(data);
      setShowFullDetails(false); // Reset to list view when selecting new scan
    } catch (e) {
      console.error("Failed to fetch scan details:", e);
    }
  };

  const confirmDelete = async () => {
    if (!scanToDelete) return;

    try {
      const res = await fetch(`${API_BASE_URL}/scans/${scanToDelete}`, {
        method: "DELETE",
      });

      if (res.ok) {
        // Remove from list
        setScans(prev => prev.filter(s => s.id !== scanToDelete));
        // If selected, deselect
        if (selectedScan?.id === scanToDelete) {
          setSelectedScan(null);
          setShowFullDetails(false);
        }
      } else {
        alert("Failed to delete scan");
      }
    } catch (e) {
      console.error("Failed to delete scan:", e);
      alert("Error deleting scan");
    } finally {
      setScanToDelete(null);
    }
  };

  const handleDeleteScan = (scanId: string) => {
    setScanToDelete(scanId);
  };

  const filteredScans = scans.filter(scan =>
    scan.id.toLowerCase().includes(searchTerm.toLowerCase()) ||
    scan.date.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const displayedScans = filteredScans.slice(0, displayCount);

  return (
    <div className="h-full grid grid-cols-12 gap-6">
      {/* Main Content Area (List or Details or Report) */}
      <div className="col-span-8 industrial-panel flex flex-col h-full overflow-hidden">
        {showFullDetails && selectedScan ? (
          // Report Component View
          <ScanReport
            scan={selectedScan}
            onBack={() => setShowFullDetails(false)}
          />
        ) : (
          <>
            {/* Header - Only show if NO report is showing */}
            <div className="p-4 border-b border-border flex-shrink-0">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-foreground">Scan History</h3>
              </div>

              <div className="flex gap-3">
                <div className="flex-1 relative">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                  <input
                    type="text"
                    placeholder="Search by ID or date..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="w-full pl-10 pr-4 py-2 bg-secondary border border-border rounded-md text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-primary"
                  />
                </div>
                <button className="flex items-center gap-2 px-4 py-2 bg-secondary border border-border rounded-md text-foreground hover:bg-secondary/80 transition-colors">
                  <Filter className="w-4 h-4" />
                  Filter
                </button>
              </div>
            </div>

            {/* Table */}
            <div className="flex-1 overflow-y-auto">
              {loading ? (
                <div className="p-8 text-center text-muted-foreground">Loading scans...</div>
              ) : filteredScans.length === 0 ? (
                <div className="p-8 text-center text-muted-foreground">No scans found</div>
              ) : (
                <table className="w-full">
                  <thead className="sticky top-0 bg-card z-10">
                    <tr className="border-b border-border">
                      <th className="text-left p-4 text-xs font-medium text-muted-foreground uppercase">Scan ID</th>
                      <th className="text-left p-4 text-xs font-medium text-muted-foreground uppercase">Date/Time</th>
                      <th className="text-left p-4 text-xs font-medium text-muted-foreground uppercase">Images</th>
                      <th className="text-left p-4 text-xs font-medium text-muted-foreground uppercase">Defects</th>
                      <th className="text-left p-4 text-xs font-medium text-muted-foreground uppercase">Status</th>
                      <th className="text-left p-4 text-xs font-medium text-muted-foreground uppercase">Scanned By</th>
                      <th className="text-left p-4 text-xs font-medium text-muted-foreground uppercase">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {displayedScans.map((scan) => (
                      <motion.tr
                        key={scan.id}
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        className={`border-b border-border/50 hover:bg-secondary/30 cursor-pointer transition-colors ${selectedScan?.id === scan.id ? "bg-primary/5" : ""
                          }`}
                        onClick={() => handleSelectScan(scan.id)}
                      >
                        <td className="p-4 font-mono text-sm text-foreground">{scan.id}</td>
                        <td className="p-4">
                          <div className="text-sm text-foreground">{scan.date}</div>
                          <div className="text-xs text-muted-foreground font-mono">{scan.time}</div>
                        </td>
                        <td className="p-4 font-mono text-sm text-foreground">{scan.image_count}</td>
                        <td className="p-4">
                          <span className={`font-mono text-sm ${scan.defect_count > 0 ? "text-warning" : "text-success"}`}>
                            {scan.defect_count}
                          </span>
                        </td>
                        <td className="p-4">
                          <span className={`inline-flex items-center gap-1.5 px-2 py-1 rounded text-xs font-medium ${scan.status === "pass"
                            ? "bg-success/10 text-success"
                            : "bg-destructive/10 text-destructive"
                            }`}>
                            {scan.status === "pass" ? (
                              <CheckCircle className="w-3 h-3" />
                            ) : (
                              <AlertTriangle className="w-3 h-3" />
                            )}
                            {scan.status.toUpperCase()}
                          </span>
                        </td>
                        <td className="p-4">
                          <div className="flex items-center gap-2">
                            <User className="w-3 h-3 text-muted-foreground" />
                            <span className="text-sm text-foreground">{scan.scanned_by || 'Unknown'}</span>
                          </div>
                        </td>
                        <td className="p-4">
                          <button
                            className="p-2 hover:bg-secondary rounded-md transition-colors"
                            onClick={(e) => {
                              e.stopPropagation();
                              handleSelectScan(scan.id);
                            }}
                          >
                            <Eye className="w-4 h-4 text-muted-foreground" />
                          </button>
                          <button
                            className="p-2 hover:bg-destructive/10 rounded-md transition-colors group"
                            title="Delete Scan"
                            onClick={(e) => {
                              e.stopPropagation();
                              handleDeleteScan(scan.id);
                            }}
                          >
                            <Trash2 className="w-4 h-4 text-muted-foreground group-hover:text-destructive transition-colors" />
                          </button>
                        </td>
                      </motion.tr>
                    ))}
                  </tbody>
                </table>
              )}

              {!loading && filteredScans.length > displayCount && (
                <div className="p-4 flex justify-center border-t border-border">
                  <button
                    onClick={() => setDisplayCount(prev => prev + 5)}
                    className="px-4 py-2 bg-secondary hover:bg-secondary/80 text-foreground rounded-md transition-colors text-sm font-medium"
                  >
                    Load More ({filteredScans.length - displayCount} remaining)
                  </button>
                </div>
              )}
            </div>
          </>
        )}
      </div>

      {/* Right Sidebar - Summary Only */}
      <div className="col-span-4 h-full flex flex-col overflow-hidden">
        {selectedScan ? (
          <div className="space-y-4">
            <div className="industrial-panel p-4">
              <h3 className="text-sm font-medium text-muted-foreground mb-4">SCAN DETAILS</h3>
              <div className="space-y-3">
                <div className="flex justify-between text-sm">
                  <span className="text-muted-foreground">Scan ID</span>
                  <span className="font-mono text-foreground text-xs">{selectedScan.id}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-muted-foreground">Date</span>
                  <span className="font-mono text-foreground">{selectedScan.date}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-muted-foreground">Time</span>
                  <span className="font-mono text-foreground">{selectedScan.time}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-muted-foreground">Total Images</span>
                  <span className="font-mono text-foreground">{selectedScan.image_count}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-muted-foreground">Status</span>
                  <span className={`font-medium ${selectedScan.status === "pass" ? "text-success" : "text-destructive"}`}>
                    {selectedScan.status.toUpperCase()}
                  </span>
                </div>
              </div>
            </div>

            {!showFullDetails && (
              <div className="space-y-3">
                {!reportGenerated[selectedScan.id] ? (
                  <button
                    onClick={async () => {
                      setIsGeneratingReport(true);
                      try {
                        const res = await fetch(`${API_BASE_URL}/scans/${selectedScan.id}/generate-report`, {
                          method: 'POST'
                        });
                        const data = await res.json();
                        if (data.success) {
                          setReportGenerated(prev => ({ ...prev, [selectedScan.id]: true }));
                        }
                      } catch (err) {
                        console.error('Failed to generate report:', err);
                      } finally {
                        setIsGeneratingReport(false);
                      }
                    }}
                    disabled={isGeneratingReport}
                    className="w-full py-3 bg-blue-600 text-white rounded-md font-medium hover:bg-blue-700 disabled:opacity-70 disabled:cursor-not-allowed transition-all shadow-lg flex items-center justify-center gap-2"
                  >
                    {isGeneratingReport ? (
                      <>
                        <Loader2 className="w-4 h-4 animate-spin" />
                        Generating Report...
                      </>
                    ) : (
                      <>
                        <FileText className="w-4 h-4" />
                        Generate Report
                      </>
                    )}
                  </button>
                ) : (
                  <button
                    onClick={() => setShowFullDetails(true)}
                    className="w-full py-3 bg-primary text-primary-foreground rounded-md font-medium hover:bg-primary/90 transition-all shadow-lg flex items-center justify-center gap-2"
                  >
                    <Eye className="w-4 h-4" />
                    View Full Inspection Report
                  </button>
                )}
              </div>
            )}

            {/* Defect Types Breakdown (Small summary) */}
            {Object.keys(selectedScan.defect_types).length > 0 && (
              <div className="industrial-panel p-4">
                <h3 className="text-sm font-medium text-muted-foreground mb-3">DEFECT SUMMARY</h3>
                <div className="flex flex-wrap gap-2">
                  {Object.entries(selectedScan.defect_types).map(([type, count]) => (
                    <span key={type} className="px-2 py-1 bg-warning/10 text-warning text-xs rounded border border-warning/20">
                      {type}: {count}
                    </span>
                  ))}
                </div>
              </div>
            )}

          </div>
        ) : (
          <div className="industrial-panel p-6 text-center">
            <Calendar className="w-12 h-12 text-muted-foreground mx-auto mb-3" />
            <p className="text-muted-foreground">Select a scan to view details</p>
          </div>
        )}
      </div>

      {/* Image Modal */}
      {selectedImage && (
        <div
          className="fixed inset-0 bg-black/80 z-50 flex items-center justify-center p-8"
          onClick={() => setSelectedImage(null)}
        >
          <div className="relative max-w-4xl max-h-full">
            <button
              onClick={() => setSelectedImage(null)}
              className="absolute -top-10 right-0 p-2 text-white hover:text-primary transition-colors"
            >
              <X className="w-6 h-6" />
            </button>
            <img
              src={selectedImage}
              className="max-w-full max-h-[80vh] object-contain rounded-lg"
              alt="Scan Image"
            />
          </div>
        </div>
      )}
      <AlertDialog open={!!scanToDelete} onOpenChange={(open) => !open && setScanToDelete(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Are you absolutely sure?</AlertDialogTitle>
            <AlertDialogDescription>
              This action cannot be undone. This will permanently delete the scan record
              <span className="font-mono font-medium text-foreground ml-1">{scanToDelete}</span> and remove all associated data and images from the server.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction onClick={confirmDelete} className="bg-destructive hover:bg-destructive/90 text-destructive-foreground">
              Delete Scan
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
};

export default PastScans;

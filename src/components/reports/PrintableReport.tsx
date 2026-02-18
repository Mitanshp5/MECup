import React, { useState, useRef } from "react";
import {
  CheckCircle,
  AlertTriangle,
  Calendar,
  Clock,
  Printer,
  ArrowLeft,
  FileText,
  ChevronDown,
  ChevronUp,
  BarChart3,
  TrendingUp,
  AlertCircle,
  Shield,
} from "lucide-react";
import { API_BASE_URL } from "@/lib/api-config";
import html2pdf from "html2pdf.js";

export interface ScanDefect {
  image: string;
  overlay: string;
  overlay_url: string;
  image_url?: string;
  defect_count?: number;
  defect_details?: { type: string; pixel_count: number; area_ratio: number }[];
}

export interface ScanDetails {
  id: string;
  date: string;
  time: string;
  image_count: number;
  images: string[];
  total_defects: number;
  defect_types: { [key: string]: number };
  defects: ScanDefect[];
  status: "pass" | "fail";
  scanned_by?: string;
}

interface PrintableReportProps {
  scan: ScanDetails;
  onBack: () => void;
}

// --- Vision Analytics Logic ---
function generateVisionAnalytics(scan: ScanDetails) {
  const { defect_types, total_defects, image_count, defects } = scan;
  const types = Object.entries(defect_types);
  const insights: { title: string; detail: string; severity: "info" | "warning" | "critical" }[] = [];
  const recommendations: string[] = [];

  const scratchCount = defect_types["Scratch"] || 0;
  const dustCount = defect_types["Dust"] || 0;
  const rundownCount = defect_types["RunDown"] || 0;

  // Defect density
  const defectDensity = image_count > 0 ? (total_defects / image_count) : 0;

  // Scratch analysis
  if (scratchCount > 0) {
    const scratchPct = total_defects > 0 ? ((scratchCount / total_defects) * 100).toFixed(1) : "0";
    if (scratchCount > total_defects * 0.5) {
      insights.push({
        title: "High Scratch Concentration",
        detail: `Scratches account for ${scratchPct}% of all defects (${scratchCount}/${total_defects}). This pattern typically indicates mechanical contact issues in the paint line — possibly worn conveyor guides, improper handling fixtures, or debris on rollers.`,
        severity: "critical",
      });
      recommendations.push("Inspect conveyor belt guides and rollers for debris or wear.");
      recommendations.push("Check handling fixtures and jigs for sharp edges or misalignment.");
      recommendations.push("Review surface preparation stage for residual particulate matter.");
    } else if (scratchCount > 0) {
      insights.push({
        title: "Scratch Defects Detected",
        detail: `${scratchCount} scratch-type defects found (${scratchPct}% of total). Minor scratching may indicate early-stage wear in material handling equipment.`,
        severity: "warning",
      });
      recommendations.push("Schedule preventive maintenance on material handling equipment.");
    }
  }

  // Dust analysis
  if (dustCount > 0) {
    const dustPct = total_defects > 0 ? ((dustCount / total_defects) * 100).toFixed(1) : "0";
    if (dustCount > total_defects * 0.4) {
      insights.push({
        title: "Excessive Dust Contamination",
        detail: `Dust defects represent ${dustPct}% of findings (${dustCount}/${total_defects}). High dust levels suggest contamination in the paint booth environment — likely inadequate air filtration, poor booth sealing, or insufficient pre-paint cleaning.`,
        severity: "critical",
      });
      recommendations.push("Replace or clean paint booth air filters immediately.");
      recommendations.push("Verify booth positive pressure and door seals.");
      recommendations.push("Enhance pre-paint surface cleaning (tack cloth / ionized air blow-off).");
    } else if (dustCount > 0) {
      insights.push({
        title: "Dust Particles Present",
        detail: `${dustCount} dust-type inclusions detected (${dustPct}% of total). Some dust contamination is within tolerance but should be monitored.`,
        severity: "info",
      });
      recommendations.push("Monitor air filtration system performance at next scheduled check.");
    }
  }

  // RunDown analysis
  if (rundownCount > 0) {
    const runPct = total_defects > 0 ? ((rundownCount / total_defects) * 100).toFixed(1) : "0";
    if (rundownCount > total_defects * 0.3) {
      insights.push({
        title: "Significant Paint Run-Down",
        detail: `Run-down defects at ${runPct}% (${rundownCount}/${total_defects}). Excessive runs/sags indicate paint viscosity issues, over-application, or incorrect spray gun distance and angle settings.`,
        severity: "critical",
      });
      recommendations.push("Verify paint viscosity is within specification (check temperature and thinner ratio).");
      recommendations.push("Calibrate spray gun flow rate and atomization pressure.");
      recommendations.push("Review robot spray path distance and angle parameters.");
    } else if (rundownCount > 0) {
      insights.push({
        title: "Paint Run-Down Detected",
        detail: `${rundownCount} run-down defects found (${runPct}% of total). Minor runs may occur on vertical surfaces but should be minimized.`,
        severity: "warning",
      });
      recommendations.push("Fine-tune spray parameters for vertical and curved surfaces.");
    }
  }

  // Overall quality assessment
  if (total_defects === 0) {
    insights.push({
      title: "Clean Inspection",
      detail: "No defects detected across all scanned regions. The painting process is operating within quality specifications.",
      severity: "info",
    });
  }

  // Defect density insight
  if (defectDensity > 2) {
    insights.push({
      title: "High Defect Density",
      detail: `Average of ${defectDensity.toFixed(1)} defects per scanned region. This exceeds the recommended threshold of 1.0 defects/region and suggests a systemic process issue rather than isolated incidents.`,
      severity: "critical",
    });
    recommendations.push("Conduct a full process audit of the paint line before the next production run.");
  } else if (defectDensity > 1) {
    insights.push({
      title: "Elevated Defect Rate",
      detail: `Defect density of ${defectDensity.toFixed(1)} per region is above the ideal target of < 1.0. Trend monitoring recommended.`,
      severity: "warning",
    });
  }

  // Area coverage analysis from defect_details
  let totalAreaRatio = 0;
  let areaCount = 0;
  for (const defect of defects) {
    if (defect.defect_details) {
      for (const dd of defect.defect_details) {
        if (dd.area_ratio > 0) {
          totalAreaRatio += dd.area_ratio;
          areaCount++;
        }
      }
    }
  }
  const avgArea = areaCount > 0 ? (totalAreaRatio / areaCount) * 100 : 0;
  if (avgArea > 5) {
    insights.push({
      title: "Large Defect Areas",
      detail: `Average defect coverage is ${avgArea.toFixed(2)}% per affected image. Large defect areas indicate severe process deviations.`,
      severity: "critical",
    });
  }

  if (recommendations.length === 0 && total_defects > 0) {
    recommendations.push("Continue routine monitoring and preventive maintenance schedules.");
  }

  return {
    insights,
    recommendations,
    defectDensity,
    scratchCount,
    dustCount,
    rundownCount,
  };
}

const PrintableReport: React.FC<PrintableReportProps> = ({ scan, onBack }) => {
  const [showAllImages, setShowAllImages] = useState(false);
  const [isGeneratingPdf, setIsGeneratingPdf] = useState(false);
  const reportContentRef = useRef<HTMLDivElement>(null);
  const analytics = generateVisionAnalytics(scan);

  const handlePrint = async () => {
    const element = reportContentRef.current;
    if (!element) return;

    setIsGeneratingPdf(true);
    try {
      const filename = `inspection-report-${scan.id.replace(/[^a-zA-Z0-9_-]/g, "_")}.pdf`;
      await html2pdf()
        .set({
          margin: 10,
          filename,
          image: { type: "jpeg", quality: 0.98 },
          html2canvas: { scale: 2, useCORS: true },
          jsPDF: { unit: "mm", format: "a4", orientation: "portrait" },
        })
        .from(element)
        .save();
    } catch (err) {
      console.error("PDF generation failed:", err);
    } finally {
      setIsGeneratingPdf(false);
    }
  };

  const getImageSrc = (defect: ScanDefect) => {
    if (defect.overlay_url) {
      return `${API_BASE_URL}${defect.overlay_url}`;
    }
    if (defect.image_url) {
      return `${API_BASE_URL}${defect.image_url}`;
    }
    return `${API_BASE_URL}/scans/${scan.id}/image/${defect.image}`;
  };

  return (
    <div className="print-container flex flex-col h-full bg-gray-100 relative">
      {/* Toolbar - Hidden when printing */}
      <div className="bg-white border-b border-gray-200 p-3 sm:p-4 flex justify-between items-center print:hidden shadow-sm z-50 sticky top-0">
        <button onClick={onBack} className="flex items-center gap-2 text-sm text-gray-600 hover:text-gray-900 transition-colors px-4 py-3 rounded-md hover:bg-gray-100 active:bg-gray-200">
          <ArrowLeft className="w-5 h-5" />
          Back
        </button>
        <button
          onClick={handlePrint}
          disabled={isGeneratingPdf}
          className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 disabled:opacity-70 disabled:cursor-not-allowed text-white px-4 py-2 rounded-md shadow-sm transition-colors text-sm font-medium"
        >
          <Printer className="w-4 h-4" />
          {isGeneratingPdf ? "Generating PDF..." : "Print / Save PDF"}
        </button>
      </div>

      {/* Report Content */}
      <div className="report-scroll-wrapper flex-1 overflow-auto p-4 sm:p-8 print:p-0 print:overflow-visible print:h-auto bg-gray-100">
        <div ref={reportContentRef} className="report-content max-w-[210mm] mx-auto bg-white text-black shadow-xl print:shadow-none print:max-w-none print:w-full min-h-[297mm] print:min-h-0">

          {/* ===== PAGE HEADER ===== */}
          <div className="p-6 sm:p-8 border-b-2 border-gray-800">
            {/* Logos Row */}
            <div className="flex items-center justify-between mb-4">
              <img src="/assets/MECUP_logo.png" alt="MECUP Logo" className="h-12 sm:h-16 object-contain" />
              <img src="/assets/icon.ico" alt="Console Logo" className="h-12 sm:h-16 object-contain" />
            </div>
            
            {/* Title and Report ID Row */}
            <div className="flex flex-col sm:flex-row justify-between items-start gap-4">
              <div>
                <div className="flex items-center gap-3 mb-2">
                  <FileText className="w-7 h-7 sm:w-8 sm:h-8 text-blue-800" />
                  <h1 className="text-xl sm:text-2xl font-bold uppercase tracking-wider text-gray-900">
                    Inspection Report
                  </h1>
                </div>
                <p className="text-xs sm:text-sm text-gray-500 font-medium">
                  Automatic Car Paint Defect Detection System
                </p>
              </div>
              <div className="text-right">
                <div className="inline-block bg-gray-50 px-4 py-2 rounded border border-gray-200 print:bg-white print:border-2 print:border-gray-800">
                  <p className="text-[10px] font-mono text-gray-500 uppercase tracking-widest mb-1 print:text-black print:font-bold">Report ID</p>
                  <p className="font-mono font-bold text-base sm:text-lg text-gray-900 print:text-xl print:text-black">
                    {scan.id.slice(-8).toUpperCase()}
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* ===== INFO GRID ===== */}
          <div className="p-6 sm:p-8 grid grid-cols-2 gap-x-8 sm:gap-x-12 gap-y-5 sm:gap-y-6 bg-gray-50/50 border-b border-gray-200">
            <div className="space-y-4">
              <InfoItem icon={<Calendar className="w-5 h-5 text-gray-400" />} label="Inspection Date" value={scan.date} />
              <InfoItem icon={<Clock className="w-5 h-5 text-gray-400" />} label="Inspection Time" value={scan.time} />
            </div>
            <div className="space-y-4">
              <div className="flex items-center gap-3">
                <div className={`w-7 h-7 sm:w-8 sm:h-8 rounded-full flex items-center justify-center ${scan.status === "pass" ? "bg-green-100 text-green-600" : "bg-red-100 text-red-600"}`}>
                  {scan.status === "pass" ? <CheckCircle className="w-4 h-4 sm:w-5 sm:h-5" /> : <AlertTriangle className="w-4 h-4 sm:w-5 sm:h-5" />}
                </div>
                <div>
                  <p className="text-[10px] text-gray-500 uppercase font-bold tracking-wider">Overall Status</p>
                  <p className={`font-bold text-base sm:text-lg ${scan.status === "pass" ? "text-green-700" : "text-red-700"}`}>
                    {scan.status.toUpperCase()}
                  </p>
                </div>
              </div>
              <div>
                <p className="text-[10px] text-gray-500 uppercase font-bold tracking-wider">Operator</p>
                <p className="font-medium text-gray-900 text-sm">{scan.scanned_by || "System Admin"}</p>
              </div>
            </div>
          </div>

          {/* ===== 1. EXECUTIVE SUMMARY ===== */}
          <div className="p-6 sm:p-8 border-b border-gray-200">
            <SectionTitle number={1} title="Executive Summary" />
            <p className="text-gray-700 leading-relaxed mb-6 text-xs sm:text-sm text-justify">
              The automated optical inspection (AOI) system has completed the full surface scan.
              The system analyzed <span className="font-bold">{scan.image_count}</span> distinct regions of interest.
              Based on the analysis, a total of{" "}
              <span className="font-bold border-b-2 border-red-200">
                {scan.total_defects} potential defect(s)
              </span>{" "}
              were identified during the inspection.
            </p>

            <div className="bg-gray-50 p-4 sm:p-6 rounded border border-gray-200">
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-4 sm:gap-6 text-center">
                <StatBox label="Total Defects" value={scan.total_defects} large />
                <StatBox label="Total Scanned" value={scan.image_count} />
                <StatBox
                  label="Defect Rate"
                  value={`${scan.image_count > 0 ? ((scan.total_defects / scan.image_count) * 100).toFixed(1) : 0}%`}
                />
              </div>
            </div>

            {/* Defect Type Breakdown */}
            {Object.keys(scan.defect_types).length > 0 && (
              <div className="mt-6">
                <p className="text-[10px] text-gray-500 uppercase font-bold tracking-wider mb-3">
                  Defect Classification Breakdown
                </p>
                <div className="grid grid-cols-3 gap-3">
                  {Object.entries(scan.defect_types).map(([type, count]) => (
                    <div key={type} className="bg-white border border-gray-200 rounded p-3 text-center">
                      <p className="text-[10px] text-gray-500 uppercase font-bold mb-1">{type}</p>
                      <p className="text-xl font-bold text-gray-800">{count}</p>
                      <p className="text-[10px] text-gray-400 mt-0.5">
                        {scan.total_defects > 0 ? ((count / scan.total_defects) * 100).toFixed(1) : 0}%
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            )}
            {Object.keys(scan.defect_types).length === 0 && scan.total_defects > 0 && (
              <p className="text-xs text-gray-400 italic mt-4">
                Defect type classification data not available for this scan.
              </p>
            )}
          </div>

          {/* ===== 2. FULL SURFACE OVERVIEW ===== */}
          <div className="p-6 sm:p-8 border-b border-gray-200 break-inside-avoid">
            <SectionTitle number={2} title="Full Surface Overview (Stitched)" />
            <p className="text-xs text-gray-600 mb-4 leading-relaxed">
              The following image shows the complete stitched view of all scanned regions, providing a comprehensive overview of the entire inspected surface.
            </p>
            <div className="bg-gray-100 border border-gray-200 rounded-lg p-4">
              <div className="aspect-[16/9] bg-white relative overflow-hidden rounded border border-gray-300">
                <img
                  src={`${API_BASE_URL}/scans/${scan.id}/stitched`}
                  alt="Stitched Surface Overview"
                  crossOrigin="anonymous"
                  className="w-full h-full object-contain"
                  onError={(e) => {
                    const el = e.currentTarget;
                    const parent = el.parentElement;
                    if (!parent) return;
                    el.style.display = "none";
                    parent.classList.add("flex", "items-center", "justify-center");
                    const span = document.createElement("span");
                    span.className = "text-gray-400 text-xs italic";
                    span.textContent = "Stitched image not available for this scan";
                    parent.appendChild(span);
                  }}
                />
              </div>
              <p className="text-[10px] text-gray-400 mt-2 text-center italic">
                Composite image generated from {scan.image_count} individual scans
              </p>
            </div>
          </div>

          {/* ===== 3. VISION ANALYTICS ===== */}
          <div className="p-6 sm:p-8 border-b border-gray-200 break-inside-avoid">
            <SectionTitle number={3} title="Vision Analytics &amp; Process Insights" />

            {analytics.insights.length > 0 ? (
              <div className="space-y-3 mb-6">
                {analytics.insights.map((insight, i) => (
                  <div
                    key={i}
                    className={`rounded border p-3 sm:p-4 ${insight.severity === "critical"
                      ? "bg-red-50 border-red-200"
                      : insight.severity === "warning"
                        ? "bg-amber-50 border-amber-200"
                        : "bg-blue-50 border-blue-200"
                      }`}
                  >
                    <div className="flex items-start gap-2">
                      {insight.severity === "critical" ? (
                        <AlertCircle className="w-4 h-4 text-red-600 mt-0.5 flex-shrink-0" />
                      ) : insight.severity === "warning" ? (
                        <AlertTriangle className="w-4 h-4 text-amber-600 mt-0.5 flex-shrink-0" />
                      ) : (
                        <TrendingUp className="w-4 h-4 text-blue-600 mt-0.5 flex-shrink-0" />
                      )}
                      <div>
                        <p className={`text-xs sm:text-sm font-bold ${insight.severity === "critical"
                          ? "text-red-800"
                          : insight.severity === "warning"
                            ? "text-amber-800"
                            : "text-blue-800"
                          }`}>
                          {insight.title}
                        </p>
                        <p className="text-[11px] sm:text-xs text-gray-700 mt-1 leading-relaxed">
                          {insight.detail}
                        </p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-xs text-gray-500 italic mb-6">No significant patterns detected.</p>
            )}

            {/* Recommendations */}
            {analytics.recommendations.length > 0 && (
              <div className="bg-gray-50 border border-gray-200 rounded p-4">
                <div className="flex items-center gap-2 mb-3">
                  <Shield className="w-4 h-4 text-gray-600" />
                  <p className="text-[10px] text-gray-600 uppercase font-bold tracking-wider">
                    Recommended Actions
                  </p>
                </div>
                <ol className="space-y-2">
                  {analytics.recommendations.map((rec, i) => (
                    <li key={i} className="flex items-start gap-2 text-xs text-gray-700">
                      <span className="font-mono font-bold text-gray-400 flex-shrink-0 w-5 text-right">
                        {i + 1}.
                      </span>
                      <span>{rec}</span>
                    </li>
                  ))}
                </ol>
              </div>
            )}
          </div>

          {/* ===== 4. VISUAL EVIDENCE ===== */}
          <div className="p-6 sm:p-8 border-b border-gray-200 break-inside-avoid">
            <div className="flex justify-between items-center mb-4">
              <SectionTitle number={4} title="Visual Evidence" />
              {scan.defects.length > 4 && (
                <button
                  onClick={() => setShowAllImages(!showAllImages)}
                  className="text-xs flex items-center gap-1 text-blue-600 hover:text-blue-800 print:hidden font-medium"
                >
                  {showAllImages ? (
                    <>Show Summary <ChevronUp className="w-3 h-3" /></>
                  ) : (
                    <>View All ({scan.defects.length}) <ChevronDown className="w-3 h-3" /></>
                  )}
                </button>
              )}
            </div>

            {scan.defects.length > 0 ? (
              <div className={`grid grid-cols-2 ${showAllImages ? "gap-3" : "gap-4 sm:gap-6"}`}>
                {(showAllImages ? scan.defects : scan.defects.slice(0, 4)).map((defect, i) => (
                  <div key={i} className="border border-gray-200 rounded-lg p-2 sm:p-3 bg-white shadow-sm break-inside-avoid">
                    <div className="aspect-video bg-gray-100 relative overflow-hidden mb-2 sm:mb-3 rounded border border-gray-100">
                      <img
                        src={getImageSrc(defect)}
                        alt={`Defect View ${i + 1}`}
                        crossOrigin="anonymous"
                        className="w-full h-full object-contain"
                        onError={(e) => {
                          const el = e.currentTarget;
                          const parent = el.parentElement;
                          if (!parent) return;

                          // Try fallback to original image if overlay failed
                          if (defect.image_url && el.src.includes("/results/")) {
                            el.src = `${API_BASE_URL}${defect.image_url}`;
                          } else if (!el.dataset.fallbackAttempted) {
                            // Mark as attempted to prevent infinite loop
                            el.dataset.fallbackAttempted = "true";
                            // Try one more fallback
                            el.src = `${API_BASE_URL}/scans/${scan.id}/image/${defect.image}`;
                          } else {
                            // All fallbacks failed, show placeholder
                            el.style.display = "none";
                            parent.classList.add("flex", "items-center", "justify-center");
                            const span = document.createElement("span");
                            span.className = "text-gray-400 text-xs italic";
                            span.textContent = "Image Not Available";
                            parent.appendChild(span);
                          }
                        }}
                      />
                    </div>
                    <div className="flex justify-between items-end border-t border-gray-100 pt-2">
                      <div>
                        <p className="text-[10px] font-mono text-gray-400 uppercase">Image Ref</p>
                        <p className="text-[10px] sm:text-xs font-mono text-gray-600 truncate max-w-[100px] sm:max-w-[120px]">
                          {defect.image}
                        </p>
                      </div>
                      <span className="text-[10px] sm:text-xs font-bold bg-red-100 text-red-700 px-2 py-1 rounded">
                        {defect.defect_count || 1} Defect(s)
                      </span>
                    </div>
                    {/* Per-image defect breakdown */}
                    {defect.defect_details && defect.defect_details.length > 0 && (
                      <div className="mt-2 pt-2 border-t border-gray-100">
                        <div className="flex flex-wrap gap-1">
                          {defect.defect_details
                            .filter((d) => d.type !== "Background")
                            .map((d, j) => (
                              <span key={j} className="text-[9px] px-1.5 py-0.5 bg-gray-100 text-gray-600 rounded font-medium">
                                {d.type}: {(d.area_ratio * 100).toFixed(2)}%
                              </span>
                            ))}
                        </div>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <div className="h-32 flex items-center justify-center bg-gray-50 rounded border border-dashed border-gray-300">
                <p className="text-gray-400 text-sm">No visual defects to display</p>
              </div>
            )}

            {!showAllImages && scan.defects.length > 4 && (
              <p className="text-xs text-center text-gray-500 italic mt-4 print:block">
                + {scan.defects.length - 4} additional images available in the digital archive.
              </p>
            )}
          </div>

          {/* ===== 5. DEFECT STATISTICS ===== */}
          <div className="p-6 sm:p-8 border-b border-gray-200">
            <SectionTitle number={5} title="Defect Statistics" />

            {scan.total_defects > 0 ? (
              <table className="w-full border-collapse text-xs sm:text-sm">
                <thead>
                  <tr className="bg-gray-100 border-b-2 border-gray-300 text-left">
                    <th className="p-2 sm:p-3 font-bold text-gray-600 uppercase tracking-wider text-[10px] sm:text-xs">
                      Defect Category
                    </th>
                    <th className="p-2 sm:p-3 font-bold text-gray-600 uppercase tracking-wider text-right text-[10px] sm:text-xs">
                      Count
                    </th>
                    <th className="p-2 sm:p-3 font-bold text-gray-600 uppercase tracking-wider text-right text-[10px] sm:text-xs">
                      % of Total
                    </th>
                    <th className="p-2 sm:p-3 font-bold text-gray-600 uppercase tracking-wider text-right text-[10px] sm:text-xs">
                      Severity
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {Object.entries(scan.defect_types).length > 0 ? (
                    Object.entries(scan.defect_types).map(([type, count], idx) => {
                      const percentage = ((count / scan.total_defects) * 100).toFixed(1);
                      const severity =
                        count > scan.total_defects * 0.5
                          ? "High"
                          : count > scan.total_defects * 0.2
                            ? "Medium"
                            : "Low";
                      const severityColor =
                        severity === "High"
                          ? "bg-red-100 text-red-800"
                          : severity === "Medium"
                            ? "bg-yellow-100 text-yellow-800"
                            : "bg-green-100 text-green-800";
                      return (
                        <tr key={idx} className="border-b border-gray-200 hover:bg-gray-50">
                          <td className="p-2 sm:p-3 font-semibold text-gray-900 capitalize">{type}</td>
                          <td className="p-2 sm:p-3 font-mono text-gray-900 text-right">{count}</td>
                          <td className="p-2 sm:p-3 font-mono text-gray-600 text-right">{percentage}%</td>
                          <td className="p-2 sm:p-3 text-right">
                            <div className="flex justify-end">
                              <span className={`inline-block px-2 py-0.5 text-[10px] rounded-full uppercase font-bold tracking-wide ${severityColor}`}>
                                {severity}
                              </span>
                            </div>
                          </td>
                        </tr>
                      );
                    })
                  ) : (
                    <tr className="border-b border-gray-200">
                      <td className="p-2 sm:p-3 text-gray-500 italic" colSpan={4}>
                        Unclassified — {scan.total_defects} defect(s) detected without type breakdown
                      </td>
                    </tr>
                  )}
                  <tr className="bg-gray-50 font-bold border-t-2 border-gray-300">
                    <td className="p-2 sm:p-3 text-gray-900 uppercase tracking-wider text-[10px] sm:text-xs">
                      Total Defects
                    </td>
                    <td className="p-2 sm:p-3 font-mono text-gray-900 text-right">{scan.total_defects}</td>
                    <td className="p-2 sm:p-3 font-mono text-gray-900 text-right">100.0%</td>
                    <td className="p-2 sm:p-3"></td>
                  </tr>
                </tbody>
              </table>
            ) : (
              <div className="p-6 text-center border border-dashed border-gray-300 rounded bg-gray-50">
                <p className="text-gray-500 text-sm">No defects recorded — surface passed inspection.</p>
              </div>
            )}
          </div>

          {/* ===== 6. FINAL REMARKS ===== */}
          <div className="p-6 sm:p-8 mt-auto bg-gray-50 border-t border-gray-200 break-inside-avoid">
            <SectionTitle number={6} title="Final Remarks" />
            <div className="border border-gray-300 bg-white p-4 min-h-[60px] sm:min-h-[80px] mb-8 shadow-inner">
              <p className="text-xs sm:text-sm text-gray-700 font-serif italic leading-relaxed">
                {scan.status === "pass"
                  ? "The inspected surface meets all quality assurance standards. No critical defects were identified requiring rework. All findings are within acceptable tolerance levels."
                  : "CRITICAL ALERT: Defects detected exceed acceptable quality thresholds. Surface requires immediate rework or defined manual inspection as per standard operating procedures (SOP-QC-2024). Refer to Section 2 for recommended corrective actions."}
              </p>
            </div>

            <div className="grid grid-cols-2 gap-8 sm:gap-12 pt-4">
              <div>
                <p className="text-[10px] text-gray-400 uppercase font-bold tracking-widest mb-6">
                  Generated Automatically By
                </p>
                <div className="border-b border-gray-400 pb-2">
                  <p className="font-bold text-gray-900 text-xs sm:text-sm">CON-SOL-E Auto-System v5.0</p>
                </div>
                <p className="text-[10px] text-gray-400 mt-1">System ID: SYS-001</p>
              </div>
              <div>
                <p className="text-[10px] text-gray-400 uppercase font-bold tracking-widest mb-6">
                  Quality Control Approval
                </p>
                <div className="border-b border-gray-400 h-8"></div>
                <p className="text-[10px] text-gray-400 mt-1">Signature / Date</p>
              </div>
            </div>
            <div className="text-center mt-8">
              <p className="text-[9px] text-gray-400 uppercase tracking-[0.2em]">
                Confidential Inspection Record
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

// --- Reusable Sub-Components ---

const SectionTitle = ({ number, title }: { number: number; title: string }) => (
  <h2 className="text-sm sm:text-lg font-bold uppercase mb-4 text-gray-800 border-l-4 border-blue-800 pl-3">
    {number}. {title}
  </h2>
);

const InfoItem = ({ icon, label, value }: { icon: React.ReactNode; label: string; value: string }) => (
  <div className="flex items-center gap-3">
    {icon}
    <div>
      <p className="text-[10px] text-gray-500 uppercase font-bold tracking-wider">{label}</p>
      <p className="font-medium text-gray-900 text-sm">{value}</p>
    </div>
  </div>
);

const StatBox = ({ label, value, large }: { label: string; value: string | number; large?: boolean }) => (
  <div>
    <p className="text-[10px] text-gray-500 uppercase font-bold tracking-wider mb-1 sm:mb-2">{label}</p>
    <p className={`font-bold text-gray-900 ${large ? "text-2xl sm:text-3xl" : "text-lg sm:text-xl"}`}>
      {value}
    </p>
  </div>
);

export default PrintableReport;

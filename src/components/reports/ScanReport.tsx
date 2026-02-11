import React, { useState } from "react";
import { CheckCircle, AlertTriangle, Calendar, Clock, Printer, ArrowLeft, FileText, ChevronDown, ChevronUp } from "lucide-react";
import { Button } from "@/components/ui/button";
import { API_BASE_URL } from "@/lib/api-config";

// Interface must match what's used in PastScans
export interface ScanDetails {
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
        defect_count?: number;
        defect_details?: { type: string; pixel_count: number; area_ratio: number }[];
    }[];
    status: "pass" | "fail";
    scanned_by?: string;
}

interface ScanReportProps {
    scan: ScanDetails;
    onBack: () => void;
}

const ScanReport: React.FC<ScanReportProps> = ({ scan, onBack }) => {
    const [showAllImages, setShowAllImages] = useState(false);

    const handlePrint = () => {
        window.print();
    };

    // Flatten defects for calculations if needed, though we use defect_types for summary
    const allDefectsCount = scan.total_defects;

    return (
        <div className="flex flex-col h-full bg-gray-100 dark:bg-zinc-900 overflow-hidden relative">
            {/* Toolbar - Hidden when printing */}
            <div className="bg-white dark:bg-zinc-950 border-b border-border p-4 flex justify-between items-center print:hidden shadow-sm z-50 sticky top-0">
                <Button variant="ghost" onClick={onBack} className="gap-2">
                    <ArrowLeft className="w-4 h-4" />
                    Back to List
                </Button>
                <div className="flex gap-2">
                    <button
                        onClick={handlePrint}
                        className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded shadow-sm transition-colors"
                    >
                        <Printer className="w-4 h-4" />
                        Print / Save PDF
                    </button>
                </div>
            </div>

            {/* Report Content - Scrollable on screen, Full on print */}
            <div className="flex-1 overflow-auto p-8 print:p-0 print:overflow-visible print:h-auto print:block bg-gray-100 dark:bg-zinc-900">
                <div className="max-w-[210mm] mx-auto bg-white text-black shadow-xl print:shadow-none print:max-w-none print:w-full min-h-[297mm] flex flex-col print:absolute print:top-0 print:left-0">

                    {/* Header */}
                    <div className="p-8 border-b-2 border-gray-800 flex justify-between items-start">
                        <div>
                            <div className="flex items-center gap-3 mb-2">
                                <FileText className="w-8 h-8 text-blue-800" />
                                <h1 className="text-2xl font-bold uppercase tracking-wider text-gray-900">Inspection Report</h1>
                            </div>
                            <p className="text-sm text-gray-500 font-medium">Automatic Car Paint Defect Detection System</p>
                        </div>
                        <div className="text-right">
                            <div className="inline-block bg-gray-50 px-4 py-2 rounded border border-gray-200">
                                <p className="text-[10px] font-mono text-gray-500 uppercase tracking-widest mb-1">Report ID</p>
                                <p className="font-mono font-bold text-lg text-gray-900">{scan.id.slice(-8).toUpperCase()}</p>
                            </div>
                        </div>
                    </div>

                    {/* Info Grid */}
                    <div className="p-8 grid grid-cols-2 gap-x-12 gap-y-6 bg-gray-50/50 border-b border-gray-200">
                        <div className="space-y-4">
                            <div className="flex items-center gap-3">
                                <Calendar className="w-5 h-5 text-gray-400" />
                                <div>
                                    <p className="text-[10px] text-gray-500 uppercase font-bold tracking-wider">Inspection Date</p>
                                    <p className="font-medium text-gray-900">{scan.date}</p>
                                </div>
                            </div>
                            <div className="flex items-center gap-3">
                                <Clock className="w-5 h-5 text-gray-400" />
                                <div>
                                    <p className="text-[10px] text-gray-500 uppercase font-bold tracking-wider">Inspection Time</p>
                                    <p className="font-medium text-gray-900">{scan.time}</p>
                                </div>
                            </div>
                        </div>
                        <div className="space-y-4">
                            <div className="flex items-center gap-3">
                                <div className={`w-8 h-8 rounded-full flex items-center justify-center ${scan.status === 'pass' ? 'bg-green-100 text-green-600' : 'bg-red-100 text-red-600'}`}>
                                    {scan.status === 'pass' ? <CheckCircle className="w-5 h-5" /> : <AlertTriangle className="w-5 h-5" />}
                                </div>
                                <div>
                                    <p className="text-[10px] text-gray-500 uppercase font-bold tracking-wider">Overall Status</p>
                                    <p className={`font-bold text-lg ${scan.status === 'pass' ? 'text-green-700' : 'text-red-700'}`}>
                                        {scan.status.toUpperCase()}
                                    </p>
                                </div>
                            </div>
                            <div>
                                <p className="text-[10px] text-gray-500 uppercase font-bold tracking-wider">Operator</p>
                                <p className="font-medium text-gray-900">{scan.scanned_by || "System Admin"}</p>
                            </div>
                        </div>
                    </div>

                    {/* Executive Summary */}
                    <div className="p-8 border-b border-gray-200">
                        <h2 className="text-lg font-bold uppercase mb-4 text-gray-800 border-l-4 border-blue-800 pl-3">1. Executive Summary</h2>
                        <p className="text-gray-700 leading-relaxed mb-6 text-sm text-justify">
                            The automated optical inspection (AOI) system has completed the full surface scan.
                            The system analyzed <span className="font-bold">{scan.image_count}</span> distinct regions of interest.
                            Based on the analysis, a total of <span className="font-bold border-b-2 border-red-200">{scan.total_defects} potential defect(s)</span> were identified.
                        </p>

                        <div className="bg-gray-50 p-6 rounded border border-gray-200">
                            <div className="grid grid-cols-2 md:grid-cols-4 gap-6 text-center">
                                <div>
                                    <p className="text-[10px] text-gray-500 uppercase font-bold tracking-wider mb-2">Total Defects</p>
                                    <p className="text-3xl font-bold text-gray-900">{scan.total_defects}</p>
                                </div>
                                <div className="col-span-3 flex justify-around items-center border-l border-gray-300">
                                    {Object.entries(scan.defect_types).map(([type, count]) => (
                                        <div key={type}>
                                            <p className="text-[10px] text-gray-500 uppercase font-bold tracking-wider mb-1">{type}</p>
                                            <p className="text-xl font-bold text-gray-800">{count}</p>
                                        </div>
                                    ))}
                                    {Object.keys(scan.defect_types).length === 0 && (
                                        <div className="text-gray-400 italic text-sm">No specific defect types recorded</div>
                                    )}
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* Visual Inspection Section */}
                    <div className="p-8 border-b border-gray-200 break-inside-avoid">
                        <div className="flex justify-between items-center mb-4">
                            <h2 className="text-lg font-bold uppercase text-gray-800 border-l-4 border-blue-800 pl-3">2. Visual Evidence</h2>
                            {scan.defects.length > 4 && (
                                <button
                                    onClick={() => setShowAllImages(!showAllImages)}
                                    className="text-xs flex items-center gap-1 text-blue-600 hover:text-blue-800 print:hidden font-medium"
                                >
                                    {showAllImages ? (
                                        <>Show Summary <ChevronUp className="w-3 h-3" /></>
                                    ) : (
                                        <>View All Images ({scan.defects.length}) <ChevronDown className="w-3 h-3" /></>
                                    )}
                                </button>
                            )}
                        </div>

                        {/* Defects Grid */}
                        {scan.defects.length > 0 ? (
                            <div className={`grid grid-cols-2 ${showAllImages ? 'gap-4' : 'gap-6'}`}>
                                {(showAllImages ? scan.defects : scan.defects.slice(0, 4)).map((defect, i) => (
                                    <div key={i} className="border border-gray-200 rounded-lg p-3 bg-white shadow-sm break-inside-avoid">
                                        <div className="aspect-video bg-gray-100 relative overflow-hidden mb-3 rounded border border-gray-100">
                                            <img
                                                src={`${API_BASE_URL}${defect.overlay_url}`}
                                                alt={`Defect View ${i + 1}`}
                                                className="w-full h-full object-contain"
                                                crossOrigin="anonymous"
                                                onError={(e) => {
                                                    e.currentTarget.style.display = 'none';
                                                    e.currentTarget.parentElement!.classList.add('flex', 'items-center', 'justify-center');
                                                    e.currentTarget.parentElement!.innerHTML += '<span class="text-gray-400 text-xs italic">Image Preview Unavailable</span>';
                                                }}
                                            />
                                        </div>
                                        <div className="flex justify-between items-end border-t border-gray-100 pt-2">
                                            <div>
                                                <p className="text-[10px] font-mono text-gray-400 uppercase">Image Ref</p>
                                                <p className="text-xs font-mono text-gray-600 truncate max-w-[120px]">{defect.image}</p>
                                            </div>
                                            <span className="text-xs font-bold bg-red-100 text-red-700 px-2 py-1 rounded">
                                                {defect.defect_count || 1} Defect(s)
                                            </span>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        ) : (
                            <div className="h-32 flex items-center justify-center bg-gray-50 rounded border border-dashed border-gray-300">
                                <p className="text-gray-400 text-sm">No visual defects to display</p>
                            </div>
                        )}

                        {!showAllImages && scan.defects.length > 4 && (
                            <p className="text-xs text-center text-gray-500 italic mt-4 print:block">+ {scan.defects.length - 4} additional images available in the digital archive.</p>
                        )}
                    </div>

                    {/* Defect Statistics (was Defect Log) */}
                    <div className="p-8 flex-1">
                        <h2 className="text-lg font-bold uppercase mb-4 text-gray-800 border-l-4 border-blue-800 pl-3">3. Defect Statistics</h2>

                        {scan.total_defects > 0 ? (
                            <table className="w-full border-collapse text-sm">
                                <thead>
                                    <tr className="bg-gray-100 border-b-2 border-gray-300 text-left">
                                        <th className="p-3 font-bold text-gray-600 uppercase tracking-wider">Defect Category</th>
                                        <th className="p-3 font-bold text-gray-600 uppercase tracking-wider text-right">Count</th>
                                        <th className="p-3 font-bold text-gray-600 uppercase tracking-wider text-right">% of Total</th>
                                        <th className="p-3 font-bold text-gray-600 uppercase tracking-wider text-right">Severity Level</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {Object.entries(scan.defect_types).map(([type, count], idx) => {
                                        const percentage = ((count / scan.total_defects) * 100).toFixed(1);
                                        return (
                                            <tr key={idx} className="border-b border-gray-200 hover:bg-gray-50">
                                                <td className="p-3 font-semibold text-gray-900 capitalize">{type}</td>
                                                <td className="p-3 font-mono text-gray-900 text-right">{count}</td>
                                                <td className="p-3 font-mono text-gray-600 text-right">{percentage}%</td>
                                                <td className="p-3 text-right">
                                                    <span className="px-2 py-1 bg-yellow-100 text-yellow-800 text-xs rounded-full uppercase font-bold tracking-wide">
                                                        Standard
                                                    </span>
                                                </td>
                                            </tr>
                                        );
                                    })}
                                    <tr className="bg-gray-50 font-bold border-t-2 border-gray-300">
                                        <td className="p-3 text-gray-900 uppercase tracking-wider">Total Defects</td>
                                        <td className="p-3 font-mono text-gray-900 text-right">{scan.total_defects}</td>
                                        <td className="p-3 font-mono text-gray-900 text-right">100.0%</td>
                                        <td className="p-3"></td>
                                    </tr>
                                </tbody>
                            </table>
                        ) : (
                            <div className="p-6 text-center border border-dashed border-gray-300 rounded bg-gray-50">
                                <p className="text-gray-500 text-sm">No defects recorded.</p>
                            </div>
                        )}
                    </div>

                    {/* Footer / Remarks */}
                    <div className="p-8 mt-auto bg-gray-50 border-t border-gray-200 break-inside-avoid">
                        <h2 className="text-lg font-bold uppercase mb-4 text-gray-800">4. Final Remarks</h2>
                        <div className="border border-gray-300 bg-white p-4 min-h-[80px] mb-8 shadow-inner">
                            <p className="text-sm text-gray-700 font-serif italic">
                                {scan.status === 'pass'
                                    ? " The inspected surface meets all quality assurance standards. No critical defects were identified requiring rework. Examples found are within acceptable tolerance levels."
                                    : "CRITICAL ALERT: Defects detected exceed acceptable quality thresholds. Surface requires immediate rework or defined manual inspection as per standard operating procedures (SOP-QC-2024)."
                                }
                            </p>
                        </div>

                        <div className="grid grid-cols-2 gap-12 pt-4">
                            <div>
                                <p className="text-[10px] text-gray-400 uppercase font-bold tracking-widest mb-6">Generated Automatically By</p>
                                <div className="border-b border-gray-400 pb-2">
                                    <p className="font-bold text-gray-900 text-sm">MECup Auto-System v5.0</p>
                                </div>
                                <p className="text-[10px] text-gray-400 mt-1">System ID: SYS-001</p>
                            </div>
                            <div>
                                <p className="text-[10px] text-gray-400 uppercase font-bold tracking-widest mb-6">Quality Control Approval</p>
                                <div className="border-b border-gray-400 h-8"></div>
                                <p className="text-[10px] text-gray-400 mt-1">Signature / Date</p>
                            </div>
                        </div>
                        <div className="text-center mt-8">
                            <p className="text-[9px] text-gray-400 uppercase tracking-[0.2em]">Page 1 of 1 • Confidental Inspection Record</p>
                        </div>
                    </div>

                </div>
            </div>
        </div>
    );
};

export default ScanReport;

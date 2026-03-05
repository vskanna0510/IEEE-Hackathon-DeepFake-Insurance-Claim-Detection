import React, { useMemo } from "react";

const PIPELINE_MODULES = [
    { key: "metadata", label: "Metadata Forensics", icon: "🔍" },
    { key: "forensics", label: "Error Level Analysis", icon: "🔬" },
    { key: "segmentation", label: "Object Detection + SAM2", icon: "🎯" },
    { key: "aigen", label: "AI-Generation Detection", icon: "🤖" },
    { key: "similarity", label: "Similarity Search", icon: "🧲" },
    { key: "physics", label: "Physics Consistency", icon: "⚡" },
    { key: "context", label: "Context Verification", icon: "🌐" },
    { key: "pattern", label: "Fraud Pattern Analysis", icon: "🕸️" },
    { key: "explainability", "label": "Heatmap Generation", icon: "🗺️" },
    { key: "alert", label: "Alert Assessment", icon: "🚨" },
];

function StepBadge({ status }) {
    if (status === "done" || status === "complete")
        return <span className="text-success text-xs">✓</span>;
    if (status === "error")
        return <span className="text-danger text-xs">✗</span>;
    if (status === "running")
        return (
            <span className="w-3 h-3 border-2 border-accent border-t-transparent rounded-full animate-spin inline-block" />
        );
    return null;
}

export default function AnalysisTimeline({ modules, status, progress }) {
    const isActive = status === "streaming" || status === "done";

    return (
        <div className="panel p-4 space-y-1">
            <div className="flex items-center justify-between mb-3">
                <h2 className="text-sm font-semibold text-textPrimary">Analysis Pipeline</h2>
                {isActive && (
                    <span className="text-[11px] text-textSecondary font-mono">{progress}%</span>
                )}
            </div>

            {/* Progress bar */}
            {isActive && (
                <div className="w-full h-1 bg-border rounded-full overflow-hidden mb-3">
                    <div
                        className="h-full bg-gradient-to-r from-accent to-blue-400 rounded-full transition-all duration-500"
                        style={{ width: `${progress}%` }}
                    />
                </div>
            )}

            <div className="space-y-0.5">
                {PIPELINE_MODULES.map((mod, i) => {
                    const modState = modules[mod.key];
                    const stepStatus = modState?.status || (isActive && !modState ? "pending" : "idle");

                    return (
                        <div
                            key={mod.key}
                            className={`flex items-center gap-3 py-1.5 px-2 rounded-lg transition-all duration-200 ${modState ? "bg-surfaceHover" : ""
                                }`}
                            style={{ animationDelay: `${i * 40}ms` }}
                        >
                            <div
                                className={`w-2 h-2 rounded-full flex-shrink-0 transition-all duration-300 ${modState?.status === "complete" || modState?.status === "done"
                                        ? "bg-success"
                                        : modState?.status === "error"
                                            ? "bg-danger"
                                            : modState
                                                ? "bg-accent animate-pulse"
                                                : "bg-border"
                                    }`}
                            />
                            <span className="text-base leading-none">{mod.icon}</span>
                            <span
                                className={`text-xs flex-1 transition-colors duration-200 ${modState ? "text-textPrimary" : "text-textMuted"
                                    }`}
                            >
                                {mod.label}
                            </span>
                            <StepBadge status={modState?.status} />
                        </div>
                    );
                })}
            </div>

            {status === "done" && (
                <div className="mt-3 pt-3 border-t border-border">
                    <p className="text-xs text-success flex items-center gap-1.5">
                        <span>✓</span> Analysis complete
                    </p>
                </div>
            )}
            {status === "error" && (
                <div className="mt-3 pt-3 border-t border-border">
                    <p className="text-xs text-danger">⚠ Analysis failed</p>
                </div>
            )}
        </div>
    );
}

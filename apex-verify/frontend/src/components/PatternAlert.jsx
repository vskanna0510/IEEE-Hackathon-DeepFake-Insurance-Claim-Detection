import React from "react";

export default function PatternAlert({ pattern }) {
    if (!pattern || !pattern.cluster_match) return null;

    const {
        cluster_size,
        high_risk_similar_count,
        similar_claim_uuids = [],
        pattern_risk_flag,
        pattern_explanation,
    } = pattern;

    return (
        <div
            className={`panel p-4 space-y-3 animate-fade-in ${pattern_risk_flag
                    ? "border-warning/30"
                    : "border-border"
                }`}
            style={
                pattern_risk_flag
                    ? { boxShadow: "0 0 16px rgba(245, 158, 11, 0.1)" }
                    : {}
            }
        >
            <div className="flex items-center gap-2">
                <span className="text-base">🕸️</span>
                <span className="text-sm font-semibold text-textPrimary">
                    Pattern Detection
                </span>
                {pattern_risk_flag && (
                    <span className="ml-auto text-[10px] px-2 py-0.5 rounded-full bg-warning/10 text-warning border border-warning/20 font-semibold">
                        FRAUD RING SUSPECTED
                    </span>
                )}
            </div>

            <p className="text-xs text-textSecondary">{pattern_explanation}</p>

            <div className="grid grid-cols-2 gap-2">
                <div className="bg-surfaceHover rounded-lg px-3 py-2">
                    <p className="text-[10px] text-textMuted mb-0.5">Similar Claims</p>
                    <p className={`text-lg font-bold font-mono ${cluster_size >= 3 ? "text-warning" : "text-textPrimary"}`}>
                        {cluster_size}
                    </p>
                </div>
                <div className="bg-surfaceHover rounded-lg px-3 py-2">
                    <p className="text-[10px] text-textMuted mb-0.5">High-Risk Similar</p>
                    <p className={`text-lg font-bold font-mono ${high_risk_similar_count >= 2 ? "text-danger" : "text-textPrimary"}`}>
                        {high_risk_similar_count}
                    </p>
                </div>
            </div>

            {similar_claim_uuids.length > 0 && (
                <div className="space-y-1 pt-1 border-t border-border">
                    <p className="text-[10px] text-textMuted uppercase tracking-wider">Matched Claim IDs</p>
                    {similar_claim_uuids.slice(0, 3).map((uuid, i) => (
                        <p key={i} className="text-[10px] font-mono text-textSecondary truncate">
                            {uuid}
                        </p>
                    ))}
                    {similar_claim_uuids.length > 3 && (
                        <p className="text-[10px] text-textMuted">+{similar_claim_uuids.length - 3} more</p>
                    )}
                </div>
            )}
        </div>
    );
}

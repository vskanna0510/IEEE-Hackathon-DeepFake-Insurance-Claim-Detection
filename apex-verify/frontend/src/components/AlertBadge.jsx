import React from "react";

function getLevelConfig(level) {
    const configs = {
        LOW: { color: "text-success", bg: "bg-success/10", border: "border-success/20", pulse: false, icon: "✓", label: "Low Risk" },
        MEDIUM: { color: "text-warning", bg: "bg-warning/10", border: "border-warning/20", pulse: false, icon: "⚠", label: "Medium Risk" },
        HIGH: { color: "text-danger", bg: "bg-danger/10", border: "border-danger/20", pulse: false, icon: "⚠", label: "High Risk" },
        CRITICAL: { color: "text-critical", bg: "bg-critical/20", border: "border-critical/30", pulse: true, icon: "🚨", label: "Critical Risk" },
    };
    return configs[level] || configs.LOW;
}

export default function AlertBadge({ alert }) {
    if (!alert) return null;

    const { alert_level, recommended_actions = [], top_fraud_signals = [], authenticity_score, pattern_flag } = alert;
    const cfg = getLevelConfig(alert_level);

    return (
        <div
            className={`panel border ${cfg.border} p-4 space-y-3 animate-fade-in ${cfg.pulse ? "animate-glow-pulse" : ""
                }`}
            style={
                cfg.pulse
                    ? { boxShadow: "0 0 20px rgba(220, 38, 38, 0.2)" }
                    : {}
            }
        >
            {/* Header */}
            <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                    <span className="text-base">{cfg.icon}</span>
                    <span className={`text-sm font-bold ${cfg.color}`}>{cfg.label}</span>
                    {pattern_flag && (
                        <span className="text-[10px] px-2 py-0.5 rounded-full bg-warning/10 text-warning border border-warning/20 font-semibold">
                            FRAUD RING
                        </span>
                    )}
                </div>
                <span className={`font-mono text-lg font-bold ${cfg.color}`}>
                    {typeof authenticity_score === "number" ? `${authenticity_score.toFixed(1)}` : "—"}
                </span>
            </div>

            {/* Fraud signals */}
            {top_fraud_signals.length > 0 && (
                <div className="space-y-1">
                    <p className="text-[10px] uppercase tracking-wider text-textMuted font-medium">
                        Top Signals
                    </p>
                    {top_fraud_signals.map((signal, i) => (
                        <div key={i} className="flex items-start gap-2">
                            <span className={`text-xs mt-0.5 flex-shrink-0 ${cfg.color}`}>•</span>
                            <p className="text-xs text-textSecondary leading-relaxed">{signal}</p>
                        </div>
                    ))}
                </div>
            )}

            {/* Recommended actions */}
            {recommended_actions.length > 0 && (
                <div className="space-y-1 pt-2 border-t border-border">
                    <p className="text-[10px] uppercase tracking-wider text-textMuted font-medium">
                        Recommended Actions
                    </p>
                    {recommended_actions.map((action, i) => (
                        <div key={i} className="flex items-start gap-2">
                            <p className="text-xs text-textSecondary leading-relaxed">{action}</p>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}

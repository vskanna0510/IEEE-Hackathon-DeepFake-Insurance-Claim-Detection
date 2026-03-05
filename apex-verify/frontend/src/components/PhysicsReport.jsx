import React from "react";

export default function PhysicsReport({ physics }) {
    if (!physics) return null;
    const { physics_consistency_score, sub_scores = {}, physics_flags = [] } = physics;
    const score = physics_consistency_score ?? 0.5;
    const pct = Math.round(score * 100);

    const color = score >= 0.7 ? "#22c55e" : score >= 0.45 ? "#f59e0b" : "#ef4444";

    const subItems = [
        { label: "Shadow Direction", key: "shadow_consistency" },
        { label: "Lighting Consistency", key: "lighting_consistency" },
        { label: "Noise Homogeneity", key: "noise_homogeneity" },
        { label: "Specular Highlights", key: "specular_consistency" },
    ];

    return (
        <div className="space-y-3 animate-fade-in">
            {/* Overall score */}
            <div className="flex items-center gap-3">
                <div className="flex-1 h-1.5 bg-border rounded-full overflow-hidden">
                    <div
                        className="h-full rounded-full transition-all duration-700"
                        style={{ width: `${pct}%`, backgroundColor: color }}
                    />
                </div>
                <span className="text-xs font-mono font-semibold" style={{ color }}>
                    {pct}%
                </span>
            </div>

            {/* Sub-scores */}
            <div className="grid grid-cols-2 gap-2">
                {subItems.map(({ label, key }) => {
                    const val = sub_scores[key] ?? 0;
                    const c = val >= 0.7 ? "#22c55e" : val >= 0.45 ? "#f59e0b" : "#ef4444";
                    return (
                        <div key={key} className="bg-surfaceHover rounded-lg px-3 py-2">
                            <p className="text-[10px] text-textMuted mb-1">{label}</p>
                            <p className="text-sm font-semibold font-mono" style={{ color: c }}>
                                {Math.round(val * 100)}%
                            </p>
                        </div>
                    );
                })}
            </div>

            {/* Flags */}
            {physics_flags.length > 0 && (
                <div className="space-y-1 pt-2 border-t border-border">
                    {physics_flags.map((flag, i) => (
                        <div key={i} className="flex items-start gap-2">
                            <span className="text-danger text-xs flex-shrink-0 mt-0.5">⚠</span>
                            <p className="text-xs text-textSecondary">{flag}</p>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}

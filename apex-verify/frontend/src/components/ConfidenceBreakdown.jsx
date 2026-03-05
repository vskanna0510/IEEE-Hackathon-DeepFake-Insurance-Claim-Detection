import React from "react";
import {
    RadarChart,
    Radar,
    PolarGrid,
    PolarAngleAxis,
    ResponsiveContainer,
    Tooltip,
} from "recharts";

const DIMENSIONS = [
    { key: "metadata_score", label: "Metadata", invert: false, description: "EXIF consistency" },
    { key: "tampering_probability", label: "ELA/Tamper", invert: true, description: "Manipulation signals" },
    { key: "ai_generation_probability", label: "AI-Gen Risk", invert: true, description: "Synthetic image probability" },
    { key: "similarity_score", label: "Similarity", invert: true, description: "Duplicate claim risk" },
    { key: "region_consistency_score", label: "Region", invert: false, description: "Regional ELA consistency" },
    { key: "physics_consistency_score", label: "Physics", invert: false, description: "Shadow/lighting coherence" },
    { key: "context_consistency_score", label: "Context", invert: false, description: "Weather/location match" },
];

function ScoreBar({ label, value, inverted, description }) {
    // For inverted signals: high value = bad; for normal: high = good
    const authenticity = inverted ? 1.0 - value : value;
    const color =
        authenticity >= 0.7
            ? "#22c55e"
            : authenticity >= 0.45
                ? "#f59e0b"
                : "#ef4444";

    const percent = Math.round(value * 100);
    const authPercent = Math.round(authenticity * 100);

    return (
        <div className="space-y-1 animate-fade-in">
            <div className="flex items-center justify-between">
                <div>
                    <span className="text-xs font-medium text-textPrimary">{label}</span>
                    <span className="ml-2 text-[10px] text-textMuted">{description}</span>
                </div>
                <span className="text-xs font-mono font-semibold" style={{ color }}>
                    {percent}%
                </span>
            </div>
            <div className="w-full h-1.5 bg-border rounded-full overflow-hidden">
                <div
                    className="h-full rounded-full transition-all duration-700"
                    style={{
                        width: `${percent}%`,
                        backgroundColor: color,
                        boxShadow: `0 0 8px ${color}40`,
                    }}
                />
            </div>
        </div>
    );
}

const CustomTooltip = ({ active, payload }) => {
    if (!active || !payload?.length) return null;
    return (
        <div className="glass px-3 py-2 rounded-lg text-xs">
            <p className="text-textPrimary font-medium">{payload[0]?.payload?.label}</p>
            <p className="text-textSecondary">{Math.round(payload[0]?.value)}%</p>
        </div>
    );
};

export default function ConfidenceBreakdown({ breakdown }) {
    if (!breakdown) {
        return (
            <div className="space-y-3">
                {DIMENSIONS.map((d) => (
                    <div key={d.key} className="space-y-1">
                        <div className="flex justify-between">
                            <span className="text-xs text-textMuted">{d.label}</span>
                            <span className="text-xs text-textMuted">—</span>
                        </div>
                        <div className="w-full h-1.5 bg-border rounded-full shimmer" />
                    </div>
                ))}
            </div>
        );
    }

    const radarData = DIMENSIONS.map((d) => {
        const raw = breakdown[d.key] ?? 0;
        const auth = d.invert ? 1.0 - raw : raw;
        return { label: d.label, value: Math.round(auth * 100) };
    });

    return (
        <div className="space-y-4">
            {/* Radar chart */}
            <div className="h-44">
                <ResponsiveContainer width="100%" height="100%">
                    <RadarChart data={radarData} margin={{ top: 4, right: 16, bottom: 4, left: 16 }}>
                        <PolarGrid stroke="rgba(255,255,255,0.06)" />
                        <PolarAngleAxis
                            dataKey="label"
                            tick={{ fontSize: 9, fill: "#8b949e", fontFamily: "Inter" }}
                        />
                        <Radar
                            name="Authenticity"
                            dataKey="value"
                            stroke="#38bdf8"
                            fill="#38bdf8"
                            fillOpacity={0.12}
                            strokeWidth={1.5}
                        />
                        <Tooltip content={<CustomTooltip />} />
                    </RadarChart>
                </ResponsiveContainer>
            </div>

            {/* Per-dimension bars */}
            <div className="space-y-2.5 pt-1 border-t border-border">
                {DIMENSIONS.map((d) => (
                    <ScoreBar
                        key={d.key}
                        label={d.label}
                        value={breakdown[d.key] ?? 0}
                        inverted={d.invert}
                        description={d.description}
                    />
                ))}
            </div>
        </div>
    );
}

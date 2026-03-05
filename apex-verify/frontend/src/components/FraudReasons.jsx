import React from "react";

const SEVERITY_MAP = {
  "AI-generation": { color: "text-danger", bg: "bg-danger/10", icon: "🤖" },
  "ELA anomalies": { color: "text-warning", bg: "bg-warning/10", icon: "🔥" },
  "Metadata": { color: "text-warning", bg: "bg-warning/10", icon: "🔍" },
  "similar": { color: "text-danger", bg: "bg-danger/10", icon: "📋" },
  "Segmentation": { color: "text-accent", bg: "bg-accent/10", icon: "🎯" },
  "Physical": { color: "text-warning", bg: "bg-warning/10", icon: "⚡" },
  "Context": { color: "text-warning", bg: "bg-warning/10", icon: "🌐" },
  "No significant": { color: "text-success", bg: "bg-success/10", icon: "✓" },
};

function getConfig(reason) {
  for (const [keyword, cfg] of Object.entries(SEVERITY_MAP)) {
    if (reason.toLowerCase().includes(keyword.toLowerCase())) return cfg;
  }
  return { color: "text-textSecondary", bg: "bg-surfaceHover", icon: "•" };
}

export default function FraudReasons({ reasons }) {
  if (!reasons || reasons.length === 0) {
    return <p className="text-xs text-textMuted">Fraud reasons will appear after analysis.</p>;
  }

  return (
    <div className="space-y-2">
      {reasons.map((reason, i) => {
        const cfg = getConfig(reason);
        return (
          <div
            key={i}
            className={`flex items-start gap-2.5 px-3 py-2 rounded-lg ${cfg.bg} animate-fade-in`}
            style={{ animationDelay: `${i * 80}ms` }}
          >
            <span className={`text-sm flex-shrink-0 mt-0.5 ${cfg.color}`}>{cfg.icon}</span>
            <p className={`text-xs leading-relaxed ${cfg.color}`}>{reason}</p>
          </div>
        );
      })}
    </div>
  );
}

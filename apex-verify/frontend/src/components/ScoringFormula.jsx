import React from "react";

const WEIGHTS = [
  { key: "sam2_confidence", label: "Segmentation confidence (SAM2)", weight: 0.20, effect: "higher → more authentic" },
  { key: "ela_score", label: "Global ELA anomalies", weight: 0.17, effect: "higher → more tampering (we invert 1 − ELA)" },
  { key: "region_ela_score", label: "Region ELA anomalies", weight: 0.13, effect: "higher → more local edits (we invert 1 − Region ELA)" },
  { key: "similarity_score", label: "Similarity to past claims", weight: 0.17, effect: "higher → more duplication risk (we invert 1 − Similarity)" },
  { key: "ai_gen_score", label: "AI‑generation probability", weight: 0.13, effect: "higher → more synthetic risk (we invert 1 − AI‑gen)" },
  { key: "metadata_score", label: "Metadata consistency", weight: 0.10, effect: "higher → more authentic" },
  { key: "physics_score", label: "Physics consistency", weight: 0.05, effect: "higher → more authentic" },
  { key: "context_score", label: "Context / weather consistency", weight: 0.05, effect: "higher → more authentic" },
];

export default function ScoringFormula() {
  return (
    <div className="space-y-3 text-[11px] text-textSecondary">
      <p>
        The authenticity score is a{" "}
        <span className="font-semibold text-textPrimary">weighted average of eight signals</span>{" "}
        from the forensics pipeline, scaled to 0–100 after clamping to \[0, 1\].
      </p>

      <div className="font-mono text-[10px] bg-surfaceHover border border-border rounded-lg px-3 py-2 leading-relaxed">
        authenticity = 100 × clamp(
        <br />
        &nbsp;&nbsp;0.20 × SAM2
        <br />
        &nbsp;+ 0.17 × (1 − Global ELA)
        <br />
        &nbsp;+ 0.13 × (1 − Region ELA)
        <br />
        &nbsp;+ 0.17 × (1 − Similarity)
        <br />
        &nbsp;+ 0.13 × (1 − AI‑gen)
        <br />
        &nbsp;+ 0.10 × Metadata
        <br />
        &nbsp;+ 0.05 × Physics
        <br />
        &nbsp;+ 0.05 × Context
        <br />
        )
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
        {WEIGHTS.map((w) => (
          <div key={w.key} className="bg-surfaceHover rounded-lg px-3 py-2 border border-border/60">
            <div className="flex items-center justify-between gap-2">
              <p className="text-[11px] font-medium text-textPrimary">{w.label}</p>
              <span className="text-[11px] font-mono text-accent">
                {(w.weight * 100).toFixed(0)}%
              </span>
            </div>
            <p className="text-[10px] text-textMuted mt-1">{w.effect}</p>
          </div>
        ))}
      </div>

      <p className="text-[10px] text-textMuted">
        Signals that increase with fraud (ELA, similarity, AI‑gen) are inverted so that higher values
        reduce authenticity, while consistency signals (SAM2, metadata, physics, context) directly
        increase authenticity.
      </p>
    </div>
  );
}


import React from "react";

export default function SimilarClaims({ claims }) {
  if (!claims || claims.length === 0) {
    return (
      <p className="text-xs text-textMuted py-2">
        No similar claims found in index.
      </p>
    );
  }

  return (
    <div className="grid grid-cols-1 gap-2">
      {claims.map((claim, i) => {
        const sim = claim.similarity ?? 0;
        const pct = Math.round(sim * 100);
        const color = pct >= 75 ? "#ef4444" : pct >= 50 ? "#f59e0b" : "#22c55e";

        return (
          <div
            key={i}
            className="flex items-center gap-3 bg-surfaceHover rounded-lg px-3 py-2.5 border border-border/50 animate-fade-in hover:border-accent/20 transition-colors duration-150"
            style={{ animationDelay: `${i * 80}ms` }}
          >
            {/* Similarity ring badge */}
            <div className="flex-shrink-0 w-10 h-10 rounded-full border-2 flex items-center justify-center"
              style={{ borderColor: color }}>
              <span className="text-xs font-bold font-mono" style={{ color }}>
                {pct}%
              </span>
            </div>

            <div className="flex-1 min-w-0">
              <p className="text-xs font-medium text-textPrimary truncate">
                {claim.metadata?.claim_id || `Claim #${claim.id}`}
              </p>
              {claim.metadata?.file_name && (
                <p className="text-[10px] text-textMuted truncate">
                  {claim.metadata.file_name}
                </p>
              )}
              {claim.metadata?.description && (
                <p className="text-[10px] text-textSecondary truncate">
                  {claim.metadata.description}
                </p>
              )}
            </div>

            <div className="text-[10px] font-mono text-textMuted flex-shrink-0">
              L2: {claim.distance?.toFixed(3)}
            </div>
          </div>
        );
      })}
    </div>
  );
}

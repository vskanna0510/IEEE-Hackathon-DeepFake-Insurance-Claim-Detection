import React, { useState } from "react";

const MODES = [
  { key: "original", label: "Original", icon: "📷" },
  { key: "ela_heatmap", label: "ELA Map", icon: "🔥" },
  { key: "ela_overlay", label: "ELA Overlay", icon: "🔬" },
  { key: "sam2_overlay", "label": "SAM2 Mask", icon: "🎯" },
];

export default function HeatmapOverlay({ previewUrl, heatmaps }) {
  const [mode, setMode] = useState("original");
  const [imgLoaded, setImgLoaded] = useState(false);

  const b64url = (b64) => (b64 ? `data:image/png;base64,${b64}` : null);

  const urls = {
    original: previewUrl,
    ela_heatmap: b64url(heatmaps?.ela_heatmap_png_base64),
    ela_overlay: b64url(heatmaps?.ela_overlay_png_base64),
    sam2_overlay: b64url(heatmaps?.sam2_overlay_png_base64),
  };

  const displayUrl = urls[mode] || previewUrl;

  const handleModeChange = (key) => {
    if (!urls[key]) return;
    setImgLoaded(false);
    setMode(key);
  };

  return (
    <div className="flex flex-col gap-3 h-full">
      {/* Mode selector pills */}
      <div className="flex flex-wrap gap-1.5">
        {MODES.map(({ key, label, icon }) => {
          const available = !!urls[key];
          return (
            <button
              key={key}
              type="button"
              onClick={() => handleModeChange(key)}
              disabled={!available}
              className={`pill ${mode === key && available
                  ? "pill-active"
                  : available
                    ? "pill-inactive"
                    : "opacity-30 cursor-not-allowed border-border text-textMuted"
                }`}
            >
              <span className="mr-1">{icon}</span>
              {label}
            </button>
          );
        })}
      </div>

      {/* Image display */}
      <div className="flex-1 min-h-[200px] rounded-xl overflow-hidden border border-border bg-black/50 flex items-center justify-center relative">
        {displayUrl ? (
          <>
            {!imgLoaded && (
              <div className="absolute inset-0 shimmer rounded-xl" />
            )}
            <img
              src={displayUrl}
              alt={mode}
              onLoad={() => setImgLoaded(true)}
              className={`max-h-80 w-full object-contain transition-opacity duration-300 ${imgLoaded ? "opacity-100" : "opacity-0"
                }`}
            />
          </>
        ) : (
          <div className="text-center px-6 py-8">
            <div className="text-3xl mb-2 opacity-20">🖼️</div>
            <p className="text-xs text-textMuted">
              {previewUrl
                ? "Run analysis to generate heatmaps."
                : "Upload an image to begin."}
            </p>
          </div>
        )}
      </div>

      {/* Legend */}
      {heatmaps && mode !== "original" && (
        <p className="text-[10px] text-textMuted leading-relaxed">
          {mode === "ela_heatmap" && "ELA heatmap — red regions indicate compression anomalies that may signal tampering."}
          {mode === "ela_overlay" && "ELA overlay — brighter areas over the original image indicate manipulation zones."}
          {mode === "sam2_overlay" && "SAM2 segmentation mask — red overlay highlights the regions used for ensemble scoring."}
        </p>
      )}
    </div>
  );
}

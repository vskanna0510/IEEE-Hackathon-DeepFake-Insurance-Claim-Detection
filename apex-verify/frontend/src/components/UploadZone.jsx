import React, { useState } from "react";

const ALLOWED_TYPES = ["image/jpeg", "image/png", "image/webp", "image/tiff"];

export default function UploadZone({ file, previewUrl, onFileChange, onAnalyze, loading, claimKeywords, onKeywordsChange }) {
  const [dragOver, setDragOver] = useState(false);

  const handleDrop = (e) => {
    e.preventDefault();
    setDragOver(false);
    const dropped = e.dataTransfer.files[0];
    if (dropped && ALLOWED_TYPES.includes(dropped.type)) {
      onFileChange(dropped);
    }
  };

  const handleFileInput = (e) => {
    const f = e.target.files[0];
    if (f) onFileChange(f);
    e.target.value = "";
  };

  return (
    <div className="space-y-3">
      {/* Drop zone */}
      <div
        onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
        onDragLeave={() => setDragOver(false)}
        onDrop={handleDrop}
        className={`relative rounded-xl border-2 border-dashed transition-all duration-200 overflow-hidden cursor-pointer
          ${dragOver
            ? "border-accent bg-accent/5 scale-[1.01]"
            : previewUrl
              ? "border-border"
              : "border-border hover:border-accent/30 hover:bg-surfaceHover"
          }`}
        onClick={() => document.getElementById("file-input").click()}
      >
        <input
          id="file-input"
          type="file"
          accept={ALLOWED_TYPES.join(",")}
          className="sr-only"
          onChange={handleFileInput}
        />

        {previewUrl ? (
          <div className="relative">
            <img
              src={previewUrl}
              alt="Preview"
              className="w-full max-h-52 object-cover"
            />
            <div className="absolute inset-0 bg-gradient-to-t from-background/80 to-transparent" />
            <div className="absolute bottom-2 left-2 right-2">
              <p className="text-xs text-textSecondary truncate">{file?.name}</p>
              <p className="text-[10px] text-textMuted">
                {file ? `${(file.size / 1024).toFixed(1)} KB` : ""}
              </p>
            </div>
            <div className="absolute top-2 right-2">
              <span className="text-[10px] px-2 py-1 bg-surface/80 backdrop-blur rounded-full text-textSecondary border border-border">
                Click to change
              </span>
            </div>
          </div>
        ) : (
          <div className="flex flex-col items-center justify-center py-10 px-4 text-center">
            <div className="w-12 h-12 rounded-xl bg-surfaceHover flex items-center justify-center mb-3 text-2xl border border-border">
              📸
            </div>
            <p className="text-sm font-medium text-textPrimary mb-1">
              Drop image here
            </p>
            <p className="text-xs text-textMuted">
              JPEG, PNG, WEBP, TIFF · Click to browse
            </p>
          </div>
        )}
      </div>

      {/* Claim keywords (for context verification) */}
      <div>
        <label className="text-[10px] uppercase tracking-wider text-textMuted font-medium block mb-1">
          Claim Type Keywords
          <span className="ml-1 text-textMuted normal-case tracking-normal">(optional, comma-separated)</span>
        </label>
        <input
          type="text"
          placeholder="e.g. flood, water damage, storm"
          value={claimKeywords}
          onChange={(e) => onKeywordsChange?.(e.target.value)}
          className="w-full bg-surfaceHover border border-border rounded-lg px-3 py-2 text-xs text-textPrimary placeholder:text-textMuted focus:outline-none focus:border-accent/40 transition-colors duration-150"
        />
      </div>

      {/* Analyze button */}
      <button
        onClick={onAnalyze}
        disabled={!file || loading}
        id="analyze-btn"
        className="btn-primary w-full"
      >
        {loading ? (
          <>
            <span className="w-3.5 h-3.5 border-2 border-current border-t-transparent rounded-full animate-spin" />
            Analyzing…
          </>
        ) : (
          <>
            <span>⚡</span>
            Analyze Claim
          </>
        )}
      </button>
    </div>
  );
}

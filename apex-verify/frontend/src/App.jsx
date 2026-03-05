import React, { useState } from "react";

import UploadZone from "./components/UploadZone";
import ScoreDial from "./components/ScoreDial";
import HeatmapOverlay from "./components/HeatmapOverlay";
import SimilarClaims from "./components/SimilarClaims";
import FraudReasons from "./components/FraudReasons";
import SignalBreakdown from "./components/SignalBreakdown";
import ConfidenceBreakdown from "./components/ConfidenceBreakdown";
import AnalysisTimeline from "./components/AnalysisTimeline";
import AlertBadge from "./components/AlertBadge";
import PhysicsReport from "./components/PhysicsReport";
import ContextReport from "./components/ContextReport";
import PatternAlert from "./components/PatternAlert";
import ScoringFormula from "./components/ScoringFormula";
import { useAnalysisStream } from "./hooks/useAnalysisStream";
import { downloadHtmlReport, openPrintReport } from "./reportExport";

// ─── Collapsible section wrapper ─────────────────────────────────────────────
function Section({ title, icon, children, defaultOpen = true }) {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <div className="panel overflow-hidden">
      <button
        onClick={() => setOpen((o) => !o)}
        className="w-full flex items-center justify-between px-4 py-3 hover:bg-surfaceHover transition-colors duration-150"
      >
        <div className="flex items-center gap-2">
          <span className="text-base">{icon}</span>
          <span className="text-sm font-semibold text-textPrimary">{title}</span>
        </div>
        <span className={`text-textMuted text-xs transition-transform duration-200 ${open ? "" : "-rotate-90"}`}>
          ▼
        </span>
      </button>
      {open && (
        <div className="px-4 pb-4 border-t border-border pt-3 animate-fade-in">
          {children}
        </div>
      )}
    </div>
  );
}

// ─── Tab system ───────────────────────────────────────────────────────────────
const TABS = [
  { key: "overview", label: "Overview", icon: "📊" },
  { key: "forensics", label: "Forensics", icon: "🔬" },
  { key: "context", label: "Context", icon: "🌐" },
  { key: "patterns", label: "Patterns", icon: "🕸️" },
];

export default function App() {
  const [selectedFile, setSelectedFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [claimKeywords, setClaimKeywords] = useState("");
  const [activeTab, setActiveTab] = useState("overview");

  const {
    status, modules, result, progress, error,
    liveScore, liveAlert, run, reset,
  } = useAnalysisStream();

  const isStreaming = status === "streaming";
  const isDone = status === "done";

  const handleFileChange = (file) => {
    setSelectedFile(file);
    reset();
    if (file) {
      setPreviewUrl(URL.createObjectURL(file));
    } else {
      setPreviewUrl(null);
    }
  };

  const handleAnalyze = () => {
    if (!selectedFile || isStreaming) return;
    run(selectedFile, claimKeywords);
  };

  // Data sources: prefer result (final), fall back to liveScore for incremental display
  const displayScore = result?.authenticity_score ?? liveScore?.authenticity_score ?? null;
  const displayRisk = result?.risk_level ?? liveScore?.risk_level ?? null;
  const breakdown = result?.breakdown ?? liveScore?.breakdown ?? null;
  const heatmaps = result?.explainability?.heatmaps ?? null;
  const similarities = result?.similarity?.matches ?? [];
  const fraudReasons = result?.fraud_reasons ?? [];
  const signals = result?.signals ?? [];
  const alert = result?.alert ?? liveAlert ?? null;
  const physics = result?.physics ?? null;
  const context = result?.context ?? null;
  const pattern = result?.pattern ?? null;

  const hasResult = isDone || (isStreaming && liveScore !== null);

  return (
    <div className="min-h-screen bg-background text-textPrimary">
      {/* ── Background grid pattern ── */}
      <div
        className="fixed inset-0 pointer-events-none"
        style={{
          backgroundImage: "linear-gradient(rgba(255,255,255,.025) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,.025) 1px, transparent 1px)",
          backgroundSize: "40px 40px",
        }}
      />
      <div
        className="fixed inset-0 pointer-events-none"
        style={{
          background: "radial-gradient(ellipse at 50% 0%, rgba(56, 189, 248, 0.07) 0%, transparent 55%)",
        }}
      />

      {/* ── Header ── */}
      <header className="relative z-10 glass border-b border-border sticky top-0">
        <div className="max-w-7xl mx-auto px-6 py-3 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-accent to-blue-500 flex items-center justify-center text-background font-bold text-sm shadow-glow">
              ⚡
            </div>
            <div>
              <h1 className="text-sm font-bold text-textPrimary tracking-tight">
                DeepClaim AI
                <span className="ml-2 text-[10px] px-1.5 py-0.5 bg-accent/10 text-accent rounded border border-accent/20 font-medium">
                  v2.0
                </span>
              </h1>
              <p className="text-[10px] text-textMuted">
                AI-Powered Insurance Fraud Detection
              </p>
            </div>
          </div>

          <div className="flex items-center gap-4">
            {isStreaming && (
              <div className="flex items-center gap-2">
                <span className="w-2 h-2 bg-accent rounded-full animate-pulse" />
                <span className="text-xs text-accent font-medium">Live Analysis</span>
              </div>
            )}
            {hasResult && alert && (
              <div
                className={`alert-chip alert-${alert.alert_level}`}
                style={alert.alert_level === "CRITICAL" ? { animation: "none" } : {}}
              >
                <span className="w-1.5 h-1.5 rounded-full bg-current" />
                {alert.alert_level}
              </div>
            )}
            <div className="text-[10px] text-textMuted hidden md:block">
              RT-DETR · SAM2 · CLIP · Open-Meteo
            </div>
          </div>
        </div>
      </header>

      <main className="relative z-10 max-w-7xl mx-auto px-6 py-6 space-y-6">

        {/* ── Top row: Upload + Score + Timeline ── */}
        <div className="grid grid-cols-1 md:grid-cols-12 gap-4">

          {/* Upload + keywords */}
          <div className="md:col-span-3 space-y-4">
            <div className="panel p-4">
              <h2 className="text-xs font-semibold uppercase tracking-wider text-textMuted mb-3">
                Claim Image
              </h2>
              <UploadZone
                file={selectedFile}
                previewUrl={previewUrl}
                onFileChange={handleFileChange}
                onAnalyze={handleAnalyze}
                loading={isStreaming}
                claimKeywords={claimKeywords}
                onKeywordsChange={setClaimKeywords}
              />
              {error && (
                <div className="mt-3 flex items-start gap-2 px-3 py-2 bg-danger/10 border border-danger/20 rounded-lg">
                  <span className="text-danger text-xs mt-0.5">⚠</span>
                  <p className="text-xs text-danger">{error}</p>
                </div>
              )}
            </div>
          </div>

          {/* Score dial */}
          <div className="md:col-span-3">
            <div className="panel p-4 flex flex-col h-full">
              <h2 className="text-xs font-semibold uppercase tracking-wider text-textMuted mb-2">
                Authenticity Score
              </h2>
              <div className="flex-1 flex items-center justify-center">
                <ScoreDial
                  score={displayScore ?? 0}
                  riskLevel={displayRisk}
                  isLive={isStreaming && liveScore !== null}
                />
              </div>
              {hasResult && fraudReasons && fraudReasons.length > 0 && (
                <p className="text-[11px] text-textSecondary text-center mt-3">
                  <span className="font-semibold text-accent">Why this score?</span>{" "}
                  {fraudReasons[0]}
                </p>
              )}
              {!hasResult && !isStreaming && (
                <p className="text-[10px] text-textMuted text-center mt-2">
                  Upload an image and click Analyze
                </p>
              )}
              {hasResult && result && (
                <div className="mt-3 flex flex-wrap gap-2 justify-center">
                  <button
                    type="button"
                    onClick={() => openPrintReport(result)}
                    className="px-3 py-1.5 rounded-lg border border-border bg-surfaceHover text-[11px] text-textSecondary hover:bg-surface focus:outline-none focus:ring-1 focus:ring-accent/40 transition-colors"
                  >
                    Print / Save as PDF
                  </button>
                  <button
                    type="button"
                    onClick={() => downloadHtmlReport(result)}
                    className="px-3 py-1.5 rounded-lg border border-border bg-surfaceHover text-[11px] text-textSecondary hover:bg-surface focus:outline-none focus:ring-1 focus:ring-accent/40 transition-colors"
                  >
                    Download HTML Report
                  </button>
                </div>
              )}
            </div>
          </div>

          {/* Timeline */}
          <div className="md:col-span-3">
            <AnalysisTimeline modules={modules} status={status} progress={progress} />
          </div>

          {/* Alert badge */}
          <div className="md:col-span-3">
            {alert ? (
              <AlertBadge alert={alert} />
            ) : (
              <div className="panel p-4 h-full flex items-center justify-center">
                <p className="text-xs text-textMuted text-center">
                  {isStreaming ? "Evaluating risk…" : "Alert will appear after analysis"}
                </p>
              </div>
            )}
          </div>
        </div>

        {/* ── Tab navigation ── */}
        {(hasResult || isStreaming) && (
          <div className="flex gap-1 border-b border-border pb-0 -mb-1">
            {TABS.map(({ key, label, icon }) => (
              <button
                key={key}
                onClick={() => setActiveTab(key)}
                className={`px-4 py-2.5 text-xs font-medium flex items-center gap-1.5 border-b-2 transition-all duration-150 ${activeTab === key
                    ? "border-accent text-accent"
                    : "border-transparent text-textMuted hover:text-textSecondary"
                  }`}
              >
                <span>{icon}</span>
                {label}
              </button>
            ))}
          </div>
        )}

        {/* ── Tab content ── */}
        {(hasResult || isStreaming) && (
          <>
            {/* OVERVIEW TAB */}
            {activeTab === "overview" && (
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 animate-fade-in">
                {/* Signal chart */}
                <div className="lg:col-span-2">
                  <Section title="Signal Breakdown" icon="📊" defaultOpen>
                    <SignalBreakdown signals={signals} />
                  </Section>
                </div>

                {/* Fraud reasons */}
                <div>
                  <Section title="Fraud Signals" icon="🚩" defaultOpen>
                    <FraudReasons reasons={fraudReasons} />
                  </Section>
                </div>

                {/* Confidence breakdown + heatmaps */}
                <div className="lg:col-span-2">
                  <Section title="Explainability Heatmaps" icon="🗺️" defaultOpen>
                    <HeatmapOverlay previewUrl={previewUrl} heatmaps={heatmaps} />
                  </Section>
                </div>

                <div>
                  <Section title="Fraud Confidence Breakdown" icon="🎯" defaultOpen>
                    <ConfidenceBreakdown breakdown={breakdown} />
                  </Section>
                </div>

                {/* Scoring formula */}
                <div className="lg:col-span-3">
                  <Section title="Scoring Formula" icon="🧮" defaultOpen={false}>
                    <ScoringFormula />
                  </Section>
                </div>
              </div>
            )}

            {/* FORENSICS TAB */}
            {activeTab === "forensics" && (
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 animate-fade-in">
                <Section title="Explainability Heatmaps" icon="🗺️" defaultOpen>
                  <HeatmapOverlay previewUrl={previewUrl} heatmaps={heatmaps} />
                </Section>

                <Section title="Physics Consistency Analysis" icon="⚡" defaultOpen>
                  <PhysicsReport physics={physics} />
                </Section>

                <Section title="ELA Forensics Details" icon="🔬" defaultOpen>
                  {result?.ela ? (
                    <div className="grid grid-cols-2 gap-2">
                      {[
                        { label: "Global ELA Score", val: result.ela.ela_score },
                        { label: "Noise Variance", val: result.ela.noise_variance },
                        { label: "Copy-Move Score", val: result.ela.copy_move_score },
                      ].map(({ label, val }) => (
                        val !== undefined && (
                          <div key={label} className="bg-surfaceHover rounded-lg px-3 py-2">
                            <p className="text-[10px] text-textMuted mb-0.5">{label}</p>
                            <p className="text-sm font-mono font-semibold text-textPrimary">
                              {(val * 100).toFixed(1)}%
                            </p>
                          </div>
                        )
                      ))}
                      <div className="bg-surfaceHover rounded-lg px-3 py-2">
                        <p className="text-[10px] text-textMuted mb-0.5">Region ELA Score</p>
                        <p className="text-sm font-mono font-semibold text-textPrimary">
                          {((result.region_ela?.region_ela_score ?? 0) * 100).toFixed(1)}%
                        </p>
                      </div>
                    </div>
                  ) : (
                    <p className="text-xs text-textMuted">ELA data not yet available.</p>
                  )}
                </Section>

                <Section title="Object Detection" icon="🎯" defaultOpen>
                  {result?.detection ? (
                    <div className="space-y-2">
                      <div className="flex items-center gap-3 bg-surfaceHover rounded-lg px-3 py-2">
                        <span className="text-textMuted text-xs">SAM2 Confidence</span>
                        <span className="ml-auto text-sm font-mono font-semibold text-textPrimary">
                          {((result.detection.sam2_confidence ?? 0) * 100).toFixed(1)}%
                        </span>
                      </div>
                      {result.detection.detections?.length > 0 ? (
                        result.detection.detections.map((d, i) => (
                          <div key={i} className="flex items-center justify-between bg-surfaceHover rounded-lg px-3 py-2">
                            <span className="text-xs text-textPrimary capitalize">{d.label}</span>
                            <span className="text-xs font-mono text-textSecondary">
                              {(d.score * 100).toFixed(1)}%
                            </span>
                          </div>
                        ))
                      ) : (
                        <p className="text-xs text-textMuted">No objects detected above threshold.</p>
                      )}
                    </div>
                  ) : (
                    <p className="text-xs text-textMuted">Detection data not yet available.</p>
                  )}
                </Section>

                <Section title="Similar Claims Gallery" icon="🧲" defaultOpen>
                  <SimilarClaims claims={similarities} />
                </Section>
              </div>
            )}

            {/* CONTEXT TAB */}
            {activeTab === "context" && (
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 animate-fade-in">
                <Section title="Context Verification" icon="🌐" defaultOpen>
                  <ContextReport context={context} />
                </Section>

                <Section title="Metadata (EXIF) Details" icon="🔍" defaultOpen>
                  {result?.ingestion?.exif && Object.keys(result.ingestion.exif).length > 0 ? (
                    <div className="space-y-2 max-h-72 overflow-y-auto pr-1">
                      {Object.entries(result.ingestion.exif).map(([section, fields]) => (
                        <div key={section} className="space-y-1">
                          <p className="text-[10px] uppercase tracking-wider text-textMuted font-medium pt-1">
                            {section}
                          </p>
                          {typeof fields === "object" && !Array.isArray(fields) ? (
                            Object.entries(fields).slice(0, 8).map(([k, v]) => (
                              <div key={k} className="flex items-start gap-2 px-2 py-1 bg-surfaceHover rounded text-xs">
                                <span className="text-textMuted min-w-[100px] flex-shrink-0">{k}</span>
                                <span className="text-textSecondary truncate font-mono text-[10px]">
                                  {String(v).slice(0, 60)}
                                </span>
                              </div>
                            ))
                          ) : null}
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-xs text-textMuted">
                      {result ? "No EXIF metadata found in image." : "Waiting for analysis…"}
                    </p>
                  )}
                </Section>

                <div className="lg:col-span-2">
                  <Section title="AI-Generation Analysis" icon="🤖" defaultOpen>
                    {result?.ai_generation ? (
                      <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                        <div className="bg-surfaceHover rounded-lg px-4 py-3">
                          <p className="text-[10px] text-textMuted mb-1">Synthetic Probability</p>
                          <p className={`text-2xl font-bold font-mono ${(result.ai_generation.ai_gen_score ?? 0) >= 0.6 ? "text-danger" : "text-success"
                            }`}>
                            {Math.round((result.ai_generation.ai_gen_score ?? 0) * 100)}%
                          </p>
                        </div>
                        {result.ai_generation.raw_logits?.length === 2 && (
                          <>
                            <div className="bg-surfaceHover rounded-lg px-4 py-3">
                              <p className="text-[10px] text-textMuted mb-1">Real Logit</p>
                              <p className="text-sm font-mono text-textPrimary">
                                {result.ai_generation.raw_logits[0].toFixed(4)}
                              </p>
                            </div>
                            <div className="bg-surfaceHover rounded-lg px-4 py-3">
                              <p className="text-[10px] text-textMuted mb-1">Fake Logit</p>
                              <p className="text-sm font-mono text-textPrimary">
                                {result.ai_generation.raw_logits[1].toFixed(4)}
                              </p>
                            </div>
                          </>
                        )}
                      </div>
                    ) : (
                      <p className="text-xs text-textMuted">Waiting for analysis…</p>
                    )}
                  </Section>
                </div>
              </div>
            )}

            {/* PATTERNS TAB */}
            {activeTab === "patterns" && (
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 animate-fade-in">
                <div className="lg:col-span-2">
                  <PatternAlert pattern={pattern} />
                </div>

                <Section title="Similar Claims Gallery" icon="🧲" defaultOpen>
                  <SimilarClaims claims={similarities} />
                </Section>

                <Section title="Confidence Breakdown" icon="🎯" defaultOpen>
                  <ConfidenceBreakdown breakdown={breakdown} />
                </Section>
              </div>
            )}
          </>
        )}

        {/* ── Empty state ── */}
        {status === "idle" && !hasResult && (
          <div className="text-center py-20 animate-fade-in">
            <div className="w-20 h-20 rounded-2xl bg-surfaceHover border border-border flex items-center justify-center text-4xl mx-auto mb-4">
              🛡️
            </div>
            <h2 className="text-lg font-bold text-textPrimary mb-2">
              DeepClaim AI — Fraud Detection Platform
            </h2>
            <p className="text-sm text-textSecondary max-w-md mx-auto">
              Upload an insurance claim image to run a comprehensive multi-module AI forensics analysis in real time.
            </p>
            <div className="mt-6 flex flex-wrap justify-center gap-2">
              {[
                "Metadata Forensics",
                "ELA + Copy-Move",
                "SAM2 Segmentation",
                "AI-Gen Detection",
                "CLIP Similarity",
                "Physics Consistency",
                "Weather Verification",
                "Pattern Analysis",
              ].map((tag) => (
                <span key={tag} className="text-[11px] px-3 py-1 rounded-full bg-surfaceHover border border-border text-textMuted">
                  {tag}
                </span>
              ))}
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

import React, { useEffect, useRef, useState } from "react";

const RADIUS = 72;
const STROKE = 10;
const CIRCUMFERENCE = Math.PI * RADIUS; // semicircle

function getScoreColor(score) {
  if (score >= 75) return "#22c55e";
  if (score >= 45) return "#f59e0b";
  if (score >= 20) return "#ef4444";
  return "#dc2626";
}

function getRiskLabel(level) {
  const map = {
    LOW: { label: "Low Risk", color: "text-success" },
    MEDIUM: { label: "Medium Risk", color: "text-warning" },
    HIGH: { label: "High Risk", color: "text-danger" },
    CRITICAL: { label: "Critical Risk", color: "text-critical" },
  };
  return map[level] || { label: level, color: "text-textSecondary" };
}

export default function ScoreDial({ score, riskLevel, isLive = false }) {
  const [displayScore, setDisplayScore] = useState(0);
  const animRef = useRef(null);
  const prevScore = useRef(0);

  useEffect(() => {
    const target = Math.max(0, Math.min(100, score || 0));
    const start = prevScore.current;
    const duration = 1200;
    const startTime = performance.now();

    if (animRef.current) cancelAnimationFrame(animRef.current);

    const animate = (now) => {
      const elapsed = now - startTime;
      const t = Math.min(elapsed / duration, 1);
      // Ease out cubic
      const eased = 1 - Math.pow(1 - t, 3);
      setDisplayScore(start + (target - start) * eased);
      if (t < 1) animRef.current = requestAnimationFrame(animate);
      else prevScore.current = target;
    };

    animRef.current = requestAnimationFrame(animate);
    return () => cancelAnimationFrame(animRef.current);
  }, [score]);

  const clampedScore = Math.max(0, Math.min(100, displayScore));
  const color = getScoreColor(clampedScore);
  const riskInfo = getRiskLabel(riskLevel);

  // SVG gauge arc
  const offset = CIRCUMFERENCE - (clampedScore / 100) * CIRCUMFERENCE;

  const cx = RADIUS + STROKE;
  const cy = RADIUS + STROKE;
  const r = RADIUS;

  return (
    <div className="flex flex-col items-center justify-center gap-1 py-2">
      {isLive && (
        <div className="flex items-center gap-1.5 mb-1">
          <span className="w-1.5 h-1.5 bg-accent rounded-full animate-pulse" />
          <span className="text-[10px] text-accent uppercase tracking-widest font-medium">Live</span>
        </div>
      )}

      <svg
        width={cx * 2}
        height={cy + STROKE + 8}
        viewBox={`0 0 ${cx * 2} ${cy + STROKE + 8}`}
        overflow="visible"
      >
        <defs>
          <linearGradient id="dialGradient" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="#dc2626" />
            <stop offset="50%" stopColor="#f59e0b" />
            <stop offset="100%" stopColor="#22c55e" />
          </linearGradient>
          <filter id="dialGlow">
            <feGaussianBlur in="SourceGraphic" stdDeviation="2" result="blur" />
            <feMerge>
              <feMergeNode in="blur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
        </defs>

        {/* Track */}
        <path
          d={`M ${STROKE} ${cy} A ${r} ${r} 0 0 1 ${cx * 2 - STROKE} ${cy}`}
          fill="none"
          stroke="rgba(255,255,255,0.06)"
          strokeWidth={STROKE}
          strokeLinecap="round"
        />

        {/* Active arc */}
        <path
          d={`M ${STROKE} ${cy} A ${r} ${r} 0 0 1 ${cx * 2 - STROKE} ${cy}`}
          fill="none"
          stroke={`url(#dialGradient)`}
          strokeWidth={STROKE}
          strokeLinecap="round"
          strokeDasharray={CIRCUMFERENCE}
          strokeDashoffset={CIRCUMFERENCE - (clampedScore / 100) * CIRCUMFERENCE}
          style={{ transition: "stroke-dashoffset 1.2s cubic-bezier(0.34, 1.56, 0.64, 1)" }}
          filter="url(#dialGlow)"
        />

        {/* Score text */}
        <text
          x={cx}
          y={cy - 6}
          textAnchor="middle"
          dominantBaseline="auto"
          fontSize="26"
          fontWeight="700"
          fontFamily="Inter, sans-serif"
          fill={color}
          style={{ transition: "fill 0.6s ease" }}
        >
          {Math.round(clampedScore)}
        </text>
      </svg>

      <p className="text-[11px] uppercase tracking-widest text-textMuted mt-0.5">
        Authenticity Score
      </p>
      {riskLevel && (
        <span
          className={`text-xs font-semibold mt-0.5 transition-all duration-300 ${riskInfo.color}`}
        >
          {riskInfo.label}
        </span>
      )}
    </div>
  );
}

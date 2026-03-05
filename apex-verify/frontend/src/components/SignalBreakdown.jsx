import React from "react";
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell, ReferenceLine
} from "recharts";

const SIGNAL_COLORS = {
  "SAM2 confidence": "#a78bfa",
  "Global ELA": "#f97316",
  "Region ELA": "#fb923c",
  "Similarity": "#e879f9",
  "AI-gen": "#f43f5e",
  "Metadata": "#38bdf8",
  "Physics": "#34d399",
  "Context": "#fbbf24",
};

const CustomTooltip = ({ active, payload }) => {
  if (!active || !payload?.length) return null;
  const { signal, score } = payload[0].payload;
  return (
    <div className="glass px-3 py-2 rounded-lg text-xs">
      <p className="font-medium text-textPrimary">{signal}</p>
      <p className="text-textSecondary">{score.toFixed(1)}%</p>
    </div>
  );
};

export default function SignalBreakdown({ signals }) {
  if (!signals || signals.length === 0) {
    return (
      <div className="space-y-2">
        {[...Array(6)].map((_, i) => (
          <div key={i} className="h-3 rounded-full shimmer" style={{ width: `${60 + i * 5}%` }} />
        ))}
      </div>
    );
  }

  const data = signals.map((s) => ({
    signal: s.signal,
    score: parseFloat(s.score.toFixed(1)),
  }));

  return (
    <div className="h-48">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} margin={{ top: 8, right: 8, bottom: 0, left: -16 }} barSize={18}>
          <XAxis
            dataKey="signal"
            tick={{ fontSize: 9, fill: "#8b949e", fontFamily: "Inter" }}
            tickLine={false}
            axisLine={false}
          />
          <YAxis
            tick={{ fontSize: 9, fill: "#8b949e", fontFamily: "Inter" }}
            tickLine={false}
            axisLine={false}
            domain={[0, 100]}
          />
          <Tooltip content={<CustomTooltip />} cursor={{ fill: "rgba(255,255,255,0.03)" }} />
          <ReferenceLine y={50} stroke="rgba(255,255,255,0.08)" strokeDasharray="4 4" />
          {data.map((entry, index) => (
            <Cell
              key={`cell-${index}`}
              fill={SIGNAL_COLORS[entry.signal] || "#38bdf8"}
            />
          ))}
          <Bar dataKey="score" radius={[4, 4, 0, 0]}>
            {data.map((entry, index) => (
              <Cell
                key={`cell-${index}`}
                fill={SIGNAL_COLORS[entry.signal] || "#38bdf8"}
                fillOpacity={0.85}
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

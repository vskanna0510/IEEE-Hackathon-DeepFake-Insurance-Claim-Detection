import React from "react";

export default function ContextReport({ context }) {
    if (!context) return null;

    const {
        context_consistency_score,
        gps_found,
        timestamp_found,
        gps_coordinates,
        capture_datetime,
        weather_data,
        explanation,
    } = context;

    const score = context_consistency_score ?? 0.5;
    const pct = Math.round(score * 100);
    const color = score >= 0.7 ? "#22c55e" : score >= 0.45 ? "#f59e0b" : "#ef4444";

    function wmoDescription(code) {
        const map = {
            0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
            45: "Foggy", 48: "Icy fog", 51: "Light drizzle", 53: "Moderate drizzle",
            55: "Dense drizzle", 61: "Slight rain", 63: "Moderate rain", 65: "Heavy rain",
            71: "Slight snow", 73: "Moderate snow", 75: "Heavy snow",
            80: "Slight showers", 81: "Moderate showers", 82: "Violent showers",
            95: "Thunderstorm", 96: "Thunderstorm w/ hail", 99: "Heavy thunderstorm w/ hail",
        };
        return map[code] ?? `Code ${code}`;
    }

    return (
        <div className="space-y-3 animate-fade-in">
            {/* Score bar */}
            <div className="flex items-center gap-3">
                <div className="flex-1 h-1.5 bg-border rounded-full overflow-hidden">
                    <div
                        className="h-full rounded-full transition-all duration-700"
                        style={{ width: `${pct}%`, backgroundColor: color }}
                    />
                </div>
                <span className="text-xs font-mono font-semibold" style={{ color }}>{pct}%</span>
            </div>

            {/* Metadata availability */}
            <div className="grid grid-cols-2 gap-2">
                <div className={`bg-surfaceHover rounded-lg px-3 py-2 flex items-center gap-2`}>
                    <span className={gps_found ? "text-success" : "text-textMuted"}>📍</span>
                    <span className="text-xs text-textSecondary">GPS {gps_found ? "found" : "missing"}</span>
                </div>
                <div className={`bg-surfaceHover rounded-lg px-3 py-2 flex items-center gap-2`}>
                    <span className={timestamp_found ? "text-success" : "text-textMuted"}>🕒</span>
                    <span className="text-xs text-textSecondary">
                        Timestamp {timestamp_found ? "found" : "missing"}
                    </span>
                </div>
            </div>

            {/* GPS + datetime */}
            {gps_coordinates && (
                <div className="bg-surfaceHover rounded-lg px-3 py-2 font-mono">
                    <p className="text-[10px] text-textMuted mb-0.5">Location</p>
                    <p className="text-xs text-textPrimary">
                        {gps_coordinates.lat.toFixed(4)}, {gps_coordinates.lon.toFixed(4)}
                    </p>
                </div>
            )}
            {capture_datetime && (
                <div className="bg-surfaceHover rounded-lg px-3 py-2 font-mono">
                    <p className="text-[10px] text-textMuted mb-0.5">Capture Time</p>
                    <p className="text-xs text-textPrimary">{capture_datetime.replace("T", " ")}</p>
                </div>
            )}

            {/* Weather data */}
            {weather_data && (
                <div className="bg-surfaceHover rounded-lg px-3 py-2 space-y-1">
                    <p className="text-[10px] text-textMuted uppercase tracking-wider">Weather on Claim Date</p>
                    <div className="grid grid-cols-3 gap-2 pt-1">
                        <div>
                            <p className="text-[10px] text-textMuted">Condition</p>
                            <p className="text-xs text-textPrimary">{wmoDescription(weather_data.weather_code)}</p>
                        </div>
                        <div>
                            <p className="text-[10px] text-textMuted">Rain</p>
                            <p className="text-xs text-textPrimary">{weather_data.precipitation_mm ?? "—"}mm</p>
                        </div>
                        <div>
                            <p className="text-[10px] text-textMuted">Wind</p>
                            <p className="text-xs text-textPrimary">{weather_data.wind_speed_kmh ?? "—"}km/h</p>
                        </div>
                    </div>
                </div>
            )}

            {/* Explanation */}
            {explanation && (
                <p className="text-xs text-textSecondary leading-relaxed border-t border-border pt-2">
                    {explanation}
                </p>
            )}
        </div>
    );
}

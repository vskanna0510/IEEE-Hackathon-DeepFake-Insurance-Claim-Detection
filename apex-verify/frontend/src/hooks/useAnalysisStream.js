import React, { useState, useRef, useEffect } from "react";

const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000";

// ─── Analysis pipeline modules in order ───────────────────────────────────────
const PIPELINE_MODULES = [
    { key: "metadata", label: "Metadata Forensics", icon: "🔍" },
    { key: "forensics", label: "Error Level Analysis", icon: "🔬" },
    { key: "segmentation", label: "Object Detection + SAM2", icon: "🎯" },
    { key: "aigen", label: "AI-Generation Detection", icon: "🤖" },
    { key: "similarity", label: "Similarity Search (CLIP)", icon: "🧲" },
    { key: "physics", label: "Physics Consistency", icon: "⚡" },
    { key: "context", label: "Context Verification", icon: "🌐" },
    { key: "pattern", label: "Fraud Pattern Analysis", icon: "🕸️" },
    { key: "explainability", "label": "Heatmap Generation", icon: "🗺️" },
    { key: "alert", label: "Alert Assessment", icon: "🚨" },
];

export function useAnalysisStream() {
    const [status, setStatus] = useState("idle"); // idle | streaming | done | error
    const [modules, setModules] = useState({});
    const [result, setResult] = useState(null);
    const [progress, setProgress] = useState(0);
    const [error, setError] = useState(null);
    const [liveScore, setLiveScore] = useState(null);
    const [liveAlert, setLiveAlert] = useState(null);
    const evsRef = useRef(null);

    const reset = () => {
        setStatus("idle");
        setModules({});
        setResult(null);
        setProgress(0);
        setError(null);
        setLiveScore(null);
        setLiveAlert(null);
        if (evsRef.current) {
            evsRef.current.abort?.();
            evsRef.current = null;
        }
    };

    const run = async (file, claimKeywords = "") => {
        reset();
        setStatus("streaming");

        const formData = new FormData();
        formData.append("file", file);
        formData.append("claim_keywords", claimKeywords);

        const controller = new AbortController();
        evsRef.current = controller;

        try {
            const response = await fetch(`${API_BASE}/analyze/stream`, {
                method: "POST",
                body: formData,
                signal: controller.signal,
            });

            if (!response.ok) {
                const err = await response.json().catch(() => ({ detail: "Request failed" }));
                throw new Error(err.detail || `HTTP ${response.status}`);
            }

            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let buffer = "";

            while (true) {
                const { value, done } = await reader.read();
                if (done) break;
                buffer += decoder.decode(value, { stream: true });

                // Parse SSE events from buffer
                const parts = buffer.split("\n\n");
                buffer = parts.pop(); // keep incomplete chunk

                for (const part of parts) {
                    const lines = part.trim().split("\n");
                    let eventType = "message";
                    let dataStr = "";
                    for (const line of lines) {
                        if (line.startsWith("event: ")) eventType = line.slice(7).trim();
                        if (line.startsWith("data: ")) dataStr = line.slice(6).trim();
                    }
                    if (!dataStr) continue;

                    const data = JSON.parse(dataStr);
                    _handleEvent(eventType, data);
                }
            }

            setStatus("done");
        } catch (err) {
            if (err.name !== "AbortError") {
                setError(err.message || "Analysis failed");
                setStatus("error");
            }
        }
    };

    function _handleEvent(type, data) {
        const moduleKeys = PIPELINE_MODULES.map((m) => m.key);

        if (type === "started") return;

        if (moduleKeys.includes(type)) {
            setModules((prev) => ({ ...prev, [type]: { status: data.status, data } }));
            const doneCount = Object.keys({ ...moduleKeys.reduce((a, k) => ({ ...a, [k]: false }), {}), [type]: true }).filter(Boolean).length;
            setProgress((prev) => Math.min(99, prev + Math.round(100 / moduleKeys.length)));
        }

        if (type === "score_update") {
            setLiveScore({
                authenticity_score: data.authenticity_score,
                risk_level: data.risk_level,
                breakdown: data.breakdown,
            });
        }

        if (type === "alert") {
            setLiveAlert(data);
        }

        if (type === "complete") {
            setResult(data);
            setProgress(100);
            setLiveScore({
                authenticity_score: data.authenticity_score,
                risk_level: data.risk_level,
                breakdown: data.breakdown,
            });
        }
    }

    return { status, modules, result, progress, error, liveScore, liveAlert, run, reset };
}

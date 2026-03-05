// Utility to export the current DeepClaim analysis result
// as a standalone HTML report and trigger browser print / PDF.

function formatPercent(value) {
  if (typeof value !== "number" || isNaN(value)) return "—";
  return `${value.toFixed(1)}%`;
}

function escapeHtml(str) {
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

function buildReportHtml(result) {
  if (!result) {
    return "<!doctype html><html><body><p>No result available.</p></body></html>";
  }

  const {
    claim_uuid,
    authenticity_score,
    risk_level,
    fraud_reasons = [],
    signals = [],
    alert,
  } = result;

  const now = new Date();
  const generatedAt = now.toISOString().replace("T", " ").split(".")[0];

  const topFraudSignals =
    (alert && Array.isArray(alert.top_fraud_signals) && alert.top_fraud_signals.length
      ? alert.top_fraud_signals
      : fraud_reasons.slice(0, 3)) || [];

  const recommendedActions =
    (alert && Array.isArray(alert.recommended_actions) && alert.recommended_actions) || [];

  const breakdownSignals = Array.isArray(signals)
    ? signals
    : [];

  const topFraudSignalsHtml =
    topFraudSignals.length === 0
      ? "<li>No significant fraud indicators detected</li>"
      : topFraudSignals
          .map((reason) => `<li>${escapeHtml(reason)}</li>`)
          .join("");

  const recommendedActionsHtml =
    recommendedActions.length === 0
      ? "<li>No special actions recommended.</li>"
      : recommendedActions
          .map(
            (action, idx) =>
              `<li><span class="index">${idx + 1}.</span> <span>${escapeHtml(action)}</span></li>`,
          )
          .join("");

  const signalRowsHtml =
    breakdownSignals.length === 0
      ? `<tr><td colspan="2" class="empty">No signal breakdown available.</td></tr>`
      : breakdownSignals
          .map(
            (s) => `
          <tr>
            <td>${escapeHtml(s.signal ?? "Signal")}</td>
            <td>${formatPercent(typeof s.score === "number" ? s.score : 0)}</td>
          </tr>
        `,
          )
          .join("");

  const whyReason =
    fraud_reasons && fraud_reasons.length > 0
      ? escapeHtml(fraud_reasons[0])
      : "No major fraud factors detected.";

  const title = "DeepClaim AI — Fraud Assessment Report";

  return `<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <title>${title}</title>
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <style>
    :root {
      color-scheme: dark;
      --bg: #050712;
      --surface: #0d101b;
      --surface-alt: #151827;
      --border: #262a3d;
      --text-primary: #f9fafb;
      --text-secondary: #d1d5db;
      --text-muted: #9ca3af;
      --accent: #38bdf8;
      --danger: #f97373;
      --success: #4ade80;
      --warning: #facc15;
    }
    * {
      box-sizing: border-box;
      -webkit-print-color-adjust: exact;
      print-color-adjust: exact;
    }
    body {
      margin: 0;
      padding: 24px;
      font-family: system-ui, -apple-system, BlinkMacSystemFont, "SF Pro Text", sans-serif;
      background: radial-gradient(circle at top, #0f172a 0, #020617 55%);
      color: var(--text-primary);
    }
    .report {
      max-width: 900px;
      margin: 0 auto;
      background: linear-gradient(145deg, rgba(15,23,42,0.98), rgba(15,23,42,0.95));
      border-radius: 16px;
      border: 1px solid rgba(31,41,55,0.9);
      box-shadow:
        0 24px 60px rgba(15,23,42,0.85),
        0 0 0 1px rgba(15,23,42,0.9);
      padding: 28px 32px 32px;
    }
    .header {
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      gap: 16px;
      margin-bottom: 20px;
    }
    .title-block h1 {
      margin: 0 0 4px;
      font-size: 22px;
      letter-spacing: 0.03em;
      text-transform: uppercase;
    }
    .subtitle {
      margin: 0;
      font-size: 11px;
      color: var(--text-muted);
    }
    .badge {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      border-radius: 9999px;
      padding: 4px 10px;
      font-size: 10px;
      text-transform: uppercase;
      letter-spacing: 0.06em;
      border: 1px solid rgba(55,65,81,0.9);
      color: var(--text-secondary);
      background: radial-gradient(circle at top left, rgba(56,189,248,0.16), transparent 55%);
    }
    .badge-dot {
      width: 6px;
      height: 6px;
      border-radius: 9999px;
      background: var(--accent);
      box-shadow: 0 0 12px rgba(56,189,248,0.9);
    }
    .meta {
      margin-top: 8px;
      font-size: 11px;
      color: var(--text-muted);
    }
    .meta span {
      display: inline-block;
      margin-right: 12px;
    }
    .score-card {
      margin: 20px 0;
      padding: 20px 20px 16px;
      border-radius: 14px;
      background: radial-gradient(circle at top, rgba(30,64,175,0.8), rgba(15,23,42,0.95));
      border: 1px solid rgba(37,99,235,0.8);
    }
    .score-label {
      font-size: 11px;
      text-transform: uppercase;
      letter-spacing: 0.12em;
      color: var(--text-muted);
      margin-bottom: 4px;
    }
    .score-value {
      font-size: 40px;
      font-weight: 700;
      letter-spacing: 0.04em;
      margin: 0;
    }
    .score-meta {
      display: flex;
      justify-content: space-between;
      align-items: baseline;
      margin-top: 6px;
      font-size: 11px;
      color: var(--text-secondary);
    }
    .risk-level {
      font-weight: 600;
      letter-spacing: 0.14em;
      text-transform: uppercase;
    }
    .risk-chip {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      padding: 2px 8px;
      border-radius: 9999px;
      font-size: 10px;
      border: 1px solid rgba(148,163,184,0.7);
      background: rgba(15,23,42,0.8);
      margin-left: 8px;
    }
    .section {
      margin-top: 18px;
    }
    .section-title {
      font-size: 11px;
      text-transform: uppercase;
      letter-spacing: 0.12em;
      color: var(--text-muted);
      margin-bottom: 6px;
    }
    .section-body {
      font-size: 12px;
      color: var(--text-secondary);
    }
    .section-body ul {
      padding-left: 18px;
      margin: 4px 0 0;
    }
    .section-body li {
      margin-bottom: 3px;
    }
    .section-body .index {
      font-weight: 600;
      margin-right: 4px;
      color: var(--accent);
    }
    .signal-table {
      width: 100%;
      border-collapse: collapse;
      margin-top: 6px;
      font-size: 12px;
    }
    .signal-table thead {
      background: rgba(15,23,42,0.98);
    }
    .signal-table th,
    .signal-table td {
      padding: 6px 10px;
      border-bottom: 1px solid rgba(31,41,55,0.95);
    }
    .signal-table th {
      text-align: left;
      font-size: 11px;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      color: var(--text-muted);
    }
    .signal-table td:nth-child(2) {
      text-align: right;
      font-variant-numeric: tabular-nums;
      color: var(--text-primary);
    }
    .signal-table .empty {
      text-align: center;
      color: var(--text-muted);
      font-style: italic;
    }
    .footer {
      margin-top: 20px;
      padding-top: 10px;
      border-top: 1px solid rgba(31,41,55,0.9);
      font-size: 10px;
      color: var(--text-muted);
      display: flex;
      justify-content: space-between;
      gap: 6px;
      flex-wrap: wrap;
    }
    .footer span {
      white-space: nowrap;
    }
    .why {
      margin-top: 10px;
      font-size: 11px;
      color: var(--text-secondary);
    }
    .why strong {
      color: var(--accent);
      font-weight: 600;
    }
    @media print {
      body {
        background: #020617;
        padding: 0;
      }
      .report {
        border-radius: 0;
        box-shadow: none;
        border: none;
        max-width: 100%;
      }
    }
  </style>
</head>
<body>
  <div class="report">
    <header class="header">
      <div class="title-block">
        <h1>${title}</h1>
        <p class="subtitle">AI-Powered Insurance Fraud Detection</p>
        <div class="meta">
          <span><strong>Claim ID:</strong> ${escapeHtml(claim_uuid || "N/A")}</span>
          <span><strong>Generated:</strong> ${escapeHtml(generatedAt)}</span>
        </div>
      </div>
      <div>
        <div class="badge">
          <span class="badge-dot"></span>
          <span>DeepClaim AI &middot; v2.0</span>
        </div>
      </div>
    </header>

    <section class="score-card">
      <div class="score-label">Authenticity Score</div>
      <p class="score-value">${typeof authenticity_score === "number" ? authenticity_score.toFixed(1) : "—"}</p>
      <div class="score-meta">
        <div>
          <span class="risk-level">Risk Level: ${escapeHtml(risk_level || "N/A")}</span>
        </div>
        <div class="risk-chip">
          RT-DETR &middot; SAM2 &middot; CLIP &middot; Context
        </div>
      </div>
      <div class="why">
        <strong>Why this score?</strong>
        ${whyReason}
      </div>
    </section>

    <section class="section">
      <div class="section-title">Top Fraud Signals</div>
      <div class="section-body">
        <ul>${topFraudSignalsHtml}</ul>
      </div>
    </section>

    <section class="section">
      <div class="section-title">Recommended Actions</div>
      <div class="section-body">
        <ol>${recommendedActionsHtml}</ol>
      </div>
    </section>

    <section class="section">
      <div class="section-title">Signal Breakdown</div>
      <table class="signal-table">
        <thead>
          <tr><th>Signal</th><th>Score</th></tr>
        </thead>
        <tbody>
          ${signalRowsHtml}
        </tbody>
      </table>
    </section>

    <footer class="footer">
      <span>DeepClaim AI v2.0 — AI-Powered Insurance Fraud Detection</span>
      <span>Report generated by apex-verify backend</span>
    </footer>
  </div>
  <script>
    // Automatically open print dialog when opened in a new tab/window
    try {
      window.focus();
      setTimeout(() => { window.print && window.print(); }, 400);
    } catch (e) {}
  </script>
</body>
</html>`;
}

export function downloadHtmlReport(result) {
  const html = buildReportHtml(result);
  const blob = new Blob([html], { type: "text/html" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  const claimId = result && result.claim_uuid ? result.claim_uuid : Date.now();
  a.href = url;
  a.download = `deepclaim-report-${claimId}.html`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

export function openPrintReport(result) {
  const html = buildReportHtml(result);
  const win = window.open("", "_blank");
  if (!win) {
    // Fallback: direct download if popup blocked
    downloadHtmlReport(result);
    return;
  }
  win.document.open();
  win.document.write(html);
  win.document.close();
}


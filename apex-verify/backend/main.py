"""
apex-verify — DeepClaim AI Backend
FastAPI server with SSE real-time pipeline + service architecture.

Endpoints:
  POST /analyze/stream  → SSE stream of per-module events
  POST /analyze         → Legacy blocking endpoint (kept for compatibility)
  GET  /alerts          → Recent fraud alerts
  GET  /health          → Health check
"""
from __future__ import annotations

import asyncio
import json
import uuid
from typing import Any, AsyncIterator, Dict, Optional

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from PIL import Image

from ingestion import load_image
from explainability import build_explainability_payload
from ensemble import compute_ensemble_score, aggregate_signals_payload

# Service imports — direct module imports avoid circular __init__ issues
import services.metadata_service as metadata_service
import services.forensics_service as forensics_service
import services.segmentation_service as segmentation_service
import services.similarity_service as similarity_service
import services.scoring_service as scoring_service
import services.context_service as context_service
import services.physics_service as physics_service
import services.pattern_service as pattern_service
import services.alert_service as alert_service

app = FastAPI(title="DeepClaim AI — apex-verify", version="2.0.0")

origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# SSE Helpers
# ---------------------------------------------------------------------------

def _sse_event(event_type: str, data: Any) -> str:
    """Format a single SSE event."""
    payload = json.dumps(data, default=str)
    return f"event: {event_type}\ndata: {payload}\n\n"


async def _analysis_stream(
    file_bytes: bytes,
    image: Image.Image,
    claim_uuid: str,
    claim_keywords: list[str],
) -> AsyncIterator[str]:
    """
    Async generator that yields SSE events as each analysis module completes.

    Event types emitted (in order):
      started         → analysis begun
      metadata        → EXIF + metadata score
      forensics       → ELA + region ELA results  [runs concurrently with segmentation]
      segmentation    → RT-DETR + SAM2 results    [runs concurrently with forensics]
      aigen           → AI-generation score        [depends on nothing]
      similarity      → CLIP similarity results
      physics         → physics consistency score
      context         → weather/GPS context score
      score_update    → intermediate score as modules finish
      pattern         → cross-claim pattern analysis
      explainability  → heatmap images (base64)
      alert           → final alert with recommended actions
      complete        → final full payload
    """
    yield _sse_event("started", {"claim_uuid": claim_uuid, "status": "Analysis started"})

    # ── Stage 1: Metadata (fast, I/O-bound EXIF parse) ──
    try:
        meta_res = await metadata_service.run(file_bytes)
        yield _sse_event("metadata", {
            "status": "complete",
            "metadata_score": meta_res["metadata_score"],
            "details": meta_res["metadata_details"],
            "exif_fields": list(meta_res["exif"].keys()),
        })
    except Exception as exc:
        meta_res = {"metadata_score": 0.4, "metadata_details": {}, "exif": {}}
        yield _sse_event("metadata", {"status": "error", "error": str(exc)})

    # ── Stage 2: Forensics + Segmentation + AIGen + Similarity — concurrent ──
    from aigen import get_ai_detector

    async def _forensics():
        return await forensics_service.run(image)

    async def _segmentation():
        return await segmentation_service.run(image)

    async def _aigen():
        loop = asyncio.get_event_loop()
        detector = get_ai_detector()
        return await loop.run_in_executor(None, detector.predict, image)

    async def _similarity():
        return await similarity_service.run(image)

    forensics_task = asyncio.create_task(_forensics())
    seg_task = asyncio.create_task(_segmentation())
    aigen_task = asyncio.create_task(_aigen())
    sim_task = asyncio.create_task(_similarity())

    forensics_res = seg_res = aigen_res = sim_res = None

    # Emit results as tasks complete via as_completed pattern
    pending = {
        forensics_task: "forensics",
        seg_task: "segmentation",
        aigen_task: "aigen",
        sim_task: "similarity",
    }

    completed: Dict[str, Any] = {}

    while pending:
        done, _ = await asyncio.wait(list(pending.keys()), return_when=asyncio.FIRST_COMPLETED)
        for task in done:
            event_name = pending.pop(task)
            try:
                result = task.result()
                completed[event_name] = result

                if event_name == "forensics":
                    yield _sse_event("forensics", {
                        "status": "complete",
                        "ela_score": result["ela_score"],
                        "region_ela_score": result["region_ela_score"],
                        "copy_move_score": result["ela"].get("copy_move_score"),
                        "noise_variance": result["ela"].get("noise_variance"),
                    })

                elif event_name == "segmentation":
                    yield _sse_event("segmentation", {
                        "status": "complete",
                        "sam2_confidence": result["sam2_confidence"],
                        "detection_count": len(result.get("detections", [])),
                        "detections": result.get("detections", []),
                    })

                elif event_name == "aigen":
                    yield _sse_event("aigen", {
                        "status": "complete",
                        "ai_generation_probability": result.get("ai_gen_score", 0.0),
                    })

                elif event_name == "similarity":
                    yield _sse_event("similarity", {
                        "status": "complete",
                        "similarity_score": result.get("similarity_score", 0.5),
                        "match_count": len(result.get("matches", [])),
                        "matches": result.get("matches", []),
                        "index_ready": result.get("index_ready", False),
                    })

            except Exception as exc:
                completed[event_name] = {}
                yield _sse_event(event_name, {"status": "error", "error": str(exc)})

    forensics_res = completed.get("forensics", {})
    seg_res = completed.get("segmentation", {})
    aigen_res = completed.get("aigen", {})
    sim_res = completed.get("similarity", {})

    mask = seg_res.get("combined_mask")

    # ── Stage 3: Physics + Context — concurrent ──
    async def _physics():
        return await physics_service.run(image)

    async def _context():
        return await context_service.run(meta_res.get("exif", {}), claim_keywords)

    phys_task = asyncio.create_task(_physics())
    ctx_task = asyncio.create_task(_context())

    phys_res = ctx_res = {}
    for task, name in [(phys_task, "physics"), (ctx_task, "context")]:
        try:
            r = await task
            if name == "physics":
                phys_res = r
                yield _sse_event("physics", {
                    "status": "complete",
                    "physics_consistency_score": r.get("physics_consistency_score", 0.5),
                    "sub_scores": r.get("sub_scores", {}),
                    "flags": r.get("physics_flags", []),
                })
            else:
                ctx_res = r
                yield _sse_event("context", {
                    "status": "complete",
                    "context_consistency_score": r.get("context_consistency_score", 0.5),
                    "gps_found": r.get("gps_found", False),
                    "timestamp_found": r.get("timestamp_found", False),
                    "weather_data": r.get("weather_data"),
                    "explanation": r.get("explanation", ""),
                })
        except Exception as exc:
            yield _sse_event(name, {"status": "error", "error": str(exc)})

    # ── Stage 4: Scoring ──
    breakdown = scoring_service.compute_confidence_breakdown(
        sam2_confidence=float(seg_res.get("sam2_confidence", 0.0)),
        ela_score=float(forensics_res.get("ela_score", 0.0)),
        region_ela_score=float(forensics_res.get("region_ela_score", 0.0)),
        similarity_score=float(sim_res.get("similarity_score", 0.5)),
        ai_gen_score=float(aigen_res.get("ai_gen_score", 0.0)),
        metadata_score=float(meta_res.get("metadata_score", 0.4)),
        physics_score=float(phys_res.get("physics_consistency_score", 0.5)),
        context_score=float(ctx_res.get("context_consistency_score", 0.5)),
    )

    authenticity_score = breakdown["authenticity_score"]
    risk_level = breakdown["risk_level"]

    yield _sse_event("score_update", {
        "authenticity_score": authenticity_score,
        "risk_level": risk_level,
        "breakdown": breakdown["breakdown"],
    })

    # ── Stage 5: Pattern Analysis ──
    try:
        from similarity import get_similarity_search as _get_ss
        _ss = _get_ss()
        loop = asyncio.get_event_loop()
        curr_emb = await loop.run_in_executor(None, _ss._embed_image, image) if _ss.index is not None else None

        pattern_res = await loop.run_in_executor(
            None, pattern_service.analyze_patterns, curr_emb
        )
        yield _sse_event("pattern", {
            "status": "complete",
            **pattern_res,
        })

        # Store this claim in the background
        loop.run_in_executor(
            None,
            pattern_service.store_claim,
            claim_uuid,
            authenticity_score,
            risk_level,
            curr_emb,
            {"file_name": claim_uuid},
        )
    except Exception as exc:
        pattern_res = pattern_service._default_pattern_result()
        yield _sse_event("pattern", {"status": "error", "error": str(exc)})

    # ── Stage 6: Explainability Heatmaps ──
    try:
        loop = asyncio.get_event_loop()
        explain_payload = await loop.run_in_executor(
            None,
            build_explainability_payload,
            image,
            mask,
            breakdown["fraud_reasons"],
        )
        yield _sse_event("explainability", {
            "status": "complete",
            "heatmaps": explain_payload["heatmaps"],
        })
    except Exception as exc:
        explain_payload = {"heatmaps": {}, "fraud_reasons": breakdown["fraud_reasons"]}
        yield _sse_event("explainability", {"status": "error", "error": str(exc)})

    # ── Stage 7: Alert ──
    alert = alert_service.evaluate_alert(
        claim_uuid=claim_uuid,
        authenticity_score=authenticity_score,
        breakdown=breakdown["breakdown"],
        fraud_reasons=breakdown["fraud_reasons"],
        pattern_result=pattern_res,
    )
    yield _sse_event("alert", alert)

    # ── Stage 8: Complete payload ──
    signals = [
        {"signal": "SAM2 confidence", "score": float(seg_res.get("sam2_confidence", 0.0)) * 100},
        {"signal": "Global ELA", "score": float(forensics_res.get("ela_score", 0.0)) * 100},
        {"signal": "Region ELA", "score": float(forensics_res.get("region_ela_score", 0.0)) * 100},
        {"signal": "Similarity", "score": float(sim_res.get("similarity_score", 0.5)) * 100},
        {"signal": "AI-gen", "score": float(aigen_res.get("ai_gen_score", 0.0)) * 100},
        {"signal": "Metadata", "score": float(meta_res.get("metadata_score", 0.4)) * 100},
        {"signal": "Physics", "score": float(phys_res.get("physics_consistency_score", 0.5)) * 100},
        {"signal": "Context", "score": float(ctx_res.get("context_consistency_score", 0.5)) * 100},
    ]

    complete_payload = {
        "claim_uuid": claim_uuid,
        "authenticity_score": authenticity_score,
        "risk_level": risk_level,
        "breakdown": breakdown["breakdown"],
        "fraud_reasons": breakdown["fraud_reasons"],
        "signals": signals,
        "ingestion": {
            "metadata_score": meta_res.get("metadata_score"),
            "metadata_details": meta_res.get("metadata_details"),
            "exif": meta_res.get("exif"),
        },
        "ela": forensics_res.get("ela", {}),
        "region_ela": forensics_res.get("region_ela", {}),
        "detection": {
            "sam2_confidence": seg_res.get("sam2_confidence"),
            "detections": seg_res.get("detections", []),
        },
        "ai_generation": aigen_res,
        "similarity": sim_res,
        "physics": phys_res,
        "context": ctx_res,
        "pattern": pattern_res,
        "explainability": explain_payload,
        "alert": alert,
    }

    yield _sse_event("complete", complete_payload)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.post("/analyze/stream")
async def analyze_stream(
    file: UploadFile = File(...),
    claim_keywords: str = Form(default=""),
):
    """
    Real-time SSE analysis endpoint.
    Emits one SSE event per analysis module as it completes.
    Optional form field `claim_keywords`: comma-separated keywords for context verification.
    E.g. "flood,water damage"
    """
    try:
        file_bytes = await file.read()
        if not file_bytes:
            raise HTTPException(status_code=400, detail="Empty file uploaded")
        image = load_image(file_bytes)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Failed to read image: {exc}") from exc

    claim_uuid = str(uuid.uuid4())
    keywords = [k.strip() for k in claim_keywords.split(",") if k.strip()]

    return StreamingResponse(
        _analysis_stream(file_bytes, image, claim_uuid, keywords),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


@app.post("/analyze")
async def analyze_image(file: UploadFile = File(...)):
    """
    Legacy blocking endpoint — kept for backwards compatibility.
    For real-time updates, use POST /analyze/stream instead.
    """
    try:
        file_bytes = await file.read()
        if not file_bytes:
            raise HTTPException(status_code=400, detail="Empty file uploaded")
        image = load_image(file_bytes)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Failed to read image: {exc}") from exc

    claim_uuid = str(uuid.uuid4())

    meta_res, forensics_res, seg_res, aigen_res, sim_res = await asyncio.gather(
        metadata_service.run(file_bytes),
        forensics_service.run(image),
        segmentation_service.run(image),
        asyncio.get_event_loop().run_in_executor(None, lambda: __import__("aigen").get_ai_detector().predict(image)),
        similarity_service.run(image),
    )

    phys_res, ctx_res = await asyncio.gather(
        physics_service.run(image),
        context_service.run(meta_res.get("exif", {}), []),
    )

    mask = seg_res.get("combined_mask")
    breakdown = scoring_service.compute_confidence_breakdown(
        sam2_confidence=float(seg_res.get("sam2_confidence", 0.0)),
        ela_score=float(forensics_res.get("ela_score", 0.0)),
        region_ela_score=float(forensics_res.get("region_ela_score", 0.0)),
        similarity_score=float(sim_res.get("similarity_score", 0.5)),
        ai_gen_score=float(aigen_res.get("ai_gen_score", 0.0)),
        metadata_score=float(meta_res.get("metadata_score", 0.4)),
        physics_score=float(phys_res.get("physics_consistency_score", 0.5)),
        context_score=float(ctx_res.get("context_consistency_score", 0.5)),
    )

    explain_payload = build_explainability_payload(
        original=image,
        sam2_mask=mask,
        fraud_reasons=breakdown["fraud_reasons"],
    )

    alert = alert_service.evaluate_alert(
        claim_uuid=claim_uuid,
        authenticity_score=breakdown["authenticity_score"],
        breakdown=breakdown["breakdown"],
        fraud_reasons=breakdown["fraud_reasons"],
    )

    signals = [
        {"signal": "SAM2 confidence", "score": float(seg_res.get("sam2_confidence", 0.0)) * 100},
        {"signal": "Global ELA", "score": float(forensics_res.get("ela_score", 0.0)) * 100},
        {"signal": "Region ELA", "score": float(forensics_res.get("region_ela_score", 0.0)) * 100},
        {"signal": "Similarity", "score": float(sim_res.get("similarity_score", 0.5)) * 100},
        {"signal": "AI-gen", "score": float(aigen_res.get("ai_gen_score", 0.0)) * 100},
        {"signal": "Metadata", "score": float(meta_res.get("metadata_score", 0.4)) * 100},
        {"signal": "Physics", "score": float(phys_res.get("physics_consistency_score", 0.5)) * 100},
        {"signal": "Context", "score": float(ctx_res.get("context_consistency_score", 0.5)) * 100},
    ]

    return JSONResponse(content={
        "claim_uuid": claim_uuid,
        "score": breakdown["authenticity_score"],
        "authenticity_score": breakdown["authenticity_score"],
        "risk_level": breakdown["risk_level"],
        "breakdown": breakdown["breakdown"],
        "fraud_reasons": breakdown["fraud_reasons"],
        "signals": signals,
        "ingestion": {"metadata_score": meta_res["metadata_score"], "metadata_details": meta_res["metadata_details"]},
        "ela": forensics_res.get("ela", {}),
        "region_ela": forensics_res.get("region_ela", {}),
        "detection": {"sam2_confidence": seg_res.get("sam2_confidence"), "detections": seg_res.get("detections", [])},
        "ai_generation": aigen_res,
        "similarity": sim_res,
        "physics": phys_res,
        "context": ctx_res,
        "explainability": explain_payload,
        "alert": alert,
    })


@app.get("/alerts")
async def get_alerts(limit: int = 20):
    """Return recent fraud alerts from the in-memory alert log."""
    return JSONResponse(content={"alerts": alert_service.get_recent_alerts(limit)})


@app.get("/health")
async def health() -> Dict[str, str]:
    return {"status": "ok", "version": "2.0.0"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

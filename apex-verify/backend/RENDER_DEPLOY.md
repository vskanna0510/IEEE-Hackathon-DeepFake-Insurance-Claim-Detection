# Deploy DeepClaim AI backend to Render

This guide deploys the **FastAPI backend** (`apex-verify/backend`) as a **Web Service** on [Render](https://render.com). The frontend (Vercel) will call this service using `VITE_API_BASE`.

---

## Important: resource requirements

The backend uses **PyTorch, SAM2, transformers, and other heavy ML libraries**. On Render:

- **Free tier** (512 MB RAM) will usually **run out of memory** during build or at runtime. Expect build timeouts or crashes.
- Use at least a **Starter paid instance** (512 MB–2 GB RAM) or **Standard** (2 GB RAM) for a chance to run. For full ML models (SAM2, CLIP, etc.), **2 GB+ RAM** is recommended.
- **Build time** can be **10–20+ minutes** because of `pip install torch` and large dependencies. Render allows long builds on paid plans.

If you only need a quick demo without heavy models, consider a lighter `requirements.txt` or a different backend (e.g. serverless that pulls models from external storage). This guide assumes the full stack.

---

## Option A: Deploy with Render Dashboard (recommended)

### 1. Push code to GitHub

Ensure your repo (e.g. `proto_v_Anti` or `apex-verify`) is on GitHub and includes the `apex-verify/backend` folder with `main.py`, `requirements.txt`, and `runtime.txt`.

### 2. Create a Web Service on Render

1. Go to [dashboard.render.com](https://dashboard.render.com) and sign in (or sign up with GitHub).
2. Click **New +** → **Web Service**.
3. **Connect the repository** that contains `apex-verify` (e.g. your `proto_v_Anti` repo). Authorize Render if needed.
4. Use these settings:

   | Field | Value |
   |-------|--------|
   | **Name** | `apex-verify-backend` (or any name) |
   | **Region** | Choose closest to your users |
   | **Root Directory** | `apex-verify/backend` |
   | **Runtime** | **Python 3** |
   | **Build Command** | `pip install -r requirements.txt` |
   | **Start Command** | `uvicorn main:app --host 0.0.0.0 --port $PORT` |

5. **Instance type**
   - Free: may build but often OOM at runtime.
   - **Starter ($7/mo)** or **Standard**: 2 GB RAM recommended for full ML stack.

6. Click **Create Web Service**. Render will clone the repo, run the build in the **Root Directory**, then start the app. The first deploy can take 15+ minutes.

### 3. Get the backend URL

After the first successful deploy, Render shows a URL like:

- `https://apex-verify-backend.onrender.com`

Use this as your **backend API URL**.

### 4. Set frontend env var (Vercel)

In your **Vercel** project (frontend):

1. **Settings** → **Environment Variables**.
2. Add: **Name** `VITE_API_BASE`, **Value** `https://apex-verify-backend.onrender.com` (your Render URL).
3. Redeploy the frontend so the new value is baked into the build.

Your app will then call the Render backend from the Vercel frontend.

### 5. (Optional) Environment variables on Render

If the backend needs API keys (e.g. Open-Meteo, Hugging Face), add them in Render:

- **Environment** tab for the Web Service → **Add Environment Variable** (e.g. `OPEN_METEO_API_KEY`, `HF_TOKEN`). No need to change code if you already use `os.environ` or `python-dotenv`.

---

## Option B: Deploy with Blueprint (`render.yaml`)

You can define the service in a **Blueprint** so it’s recreated from config.

1. In the **repo root** (e.g. `proto_v_Anti`), create `render.yaml` with the content below (or use the one in `apex-verify/backend/render.yaml` and set Render’s **Root Directory** to the backend when adding the Blueprint).

2. On Render: **New +** → **Blueprint** → connect the repo. Render will read `render.yaml` and create the Web Service. Adjust **Root Directory** in the Blueprint so the service points at `apex-verify/backend`, or put `render.yaml` in the repo root and set `rootDir` inside it (see below).

Example **repo-root** `render.yaml` (so one file in the root of the repo):

```yaml
services:
  - type: web
    name: apex-verify-backend
    runtime: python
    rootDir: apex-verify/backend
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn main:app --host 0.0.0.0 --port $PORT
    plan: starter   # or free; starter recommended for ML
```

If the file lives under `apex-verify/backend/render.yaml`, then in Render when you add a Blueprint, set the **Root Directory** of the Blueprint to `apex-verify/backend` so that `rootDir` in the yaml is relative to that (or omit `rootDir`).

---

## Verify deployment

1. **Health check:** open `https://<your-render-url>.onrender.com/health`. You should see `{"status":"ok","version":"2.0.0"}`.
2. **Docs:** open `https://<your-render-url>.onrender.com/docs` to see FastAPI Swagger UI.
3. From the Vercel frontend, run an analysis; it should call `/analyze/stream` on the Render URL (check browser Network tab).

---

## CORS

The backend already allows:

- `http://localhost:5173`, `http://127.0.0.1:5173`, `http://localhost:3000`
- Any `https://*.vercel.app` origin (so your Vercel frontend is allowed).

No extra CORS config is needed for the Vercel → Render setup.

---

## Troubleshooting

| Issue | What to try |
|-------|---------------------|
| Build timeout | Use a paid plan; ensure **Root Directory** is `apex-verify/backend`. |
| Out of memory (OOM) | Increase to 2 GB RAM (Starter/Standard). |
| 503 / App not starting | Check **Logs** for Python errors; ensure **Start Command** is exactly `uvicorn main:app --host 0.0.0.0 --port $PORT` and that you’re in `apex-verify/backend` (so `main.py` is there). |
| CORS errors from frontend | Confirm backend has `allow_origin_regex` for `https://*.vercel.app` (already in `main.py`). |
| Cold start slow | Render free/starter instances spin down after inactivity; first request can take 30–60 s. Use **Always On** on paid plan to reduce cold starts. |

---

## Summary

- **Build:** `pip install -r requirements.txt` in `apex-verify/backend`.
- **Start:** `uvicorn main:app --host 0.0.0.0 --port $PORT`.
- **Root Directory** in Render: `apex-verify/backend`.
- Set **VITE_API_BASE** in Vercel to your Render Web Service URL and redeploy the frontend.

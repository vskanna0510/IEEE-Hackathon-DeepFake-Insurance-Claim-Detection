# Deploy DeepClaim AI frontend to Vercel

Deploy **only the frontend** to Vercel. The Python backend (FastAPI + ML models) must be hosted elsewhere (e.g. Railway, Render) and then wired via `VITE_API_BASE`.

---

## 1. Prerequisites

- GitHub (or GitLab/Bitbucket) repo with your code pushed.
- [Vercel account](https://vercel.com/signup).

---

## 2. Deploy frontend on Vercel

1. Go to [vercel.com](https://vercel.com) → **Add New** → **Project**.
2. **Import** your Git repository (`proto_v_Anti` or the repo that contains `apex-verify/`).
3. **Configure:**
   - **Root Directory:** Click **Edit** and set to `apex-verify/frontend` (so Vercel builds the React app, not the repo root).
   - **Framework Preset:** Vite (auto-detected).
   - **Build Command:** `npm run build` (default).
   - **Output Directory:** `dist` (default).
4. **Environment variables** (important for production):
   - Name: `VITE_API_BASE`  
   - Value: your **backend API URL**, e.g. `https://your-backend.up.railway.app` or `https://your-app.onrender.com`  
   - Add it for **Production**, and optionally Preview/Development.
5. Click **Deploy**. Vercel will run `npm install` and `npm run build` and serve the `dist/` output.

After deploy, the app will be at `https://your-project.vercel.app`. The frontend will call the URL you set in `VITE_API_BASE` for the `/analyze/stream` and other API endpoints.

---

## 3. Host the backend elsewhere

The backend is too large for Vercel serverless (PyTorch, SAM2, etc.). Use one of:

- **Railway:** Connect the same repo, set root to `apex-verify/backend`, add a start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`. Railway provides a public URL; put that URL in `VITE_API_BASE`.
- **Render:** New Web Service, connect repo, root `apex-verify/backend`, build: `pip install -r requirements.txt`, start: `uvicorn main:app --host 0.0.0.0 --port $PORT`. Use the Render URL as `VITE_API_BASE`.
- **Fly.io / AWS / GCP / VPS:** Deploy the FastAPI app and expose a URL; set that as `VITE_API_BASE`.

Then in Vercel, set **Environment Variable** `VITE_API_BASE` = that backend URL and redeploy the frontend so the build picks it up.

---

## 4. CORS on the backend

Your FastAPI app already allows `http://localhost:5173`. For the Vercel domain, add it to `origins` in `backend/main.py`, e.g.:

```python
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "https://your-project.vercel.app",  # add your Vercel URL
]
```

Redeploy the backend after changing CORS.

---

## 5. .gitignore

The repo `.gitignore` is fine for Vercel. Do **not** remove:

- `node_modules/` — Vercel installs dependencies during build.
- `dist/` — Vercel creates a fresh build.
- `.env` / `.env.local` — Keep ignored; use Vercel’s **Environment Variables** in the dashboard instead of committing secrets.

No changes to `.gitignore` are required for Vercel deployment.

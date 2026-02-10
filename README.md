# Asset Metadata Studio

Generate bilingual (English + Arabic) asset names and tags for slides, images, icons, and PPT files using GPT-5-mini. The app processes each asset individually and exports results to Excel.

## Features
- Upload up to 100 files per batch.
- Editable prompt (defaults to the provided metadata prompt).
- Parallel processing with a safe default of 6 concurrent requests.
- Excel export with uploaded filename, English name, Arabic name, and tags.

## Requirements
- Python 3.10+
- Node.js 18+
- LibreOffice (soffice must be on PATH)
- Google Gemini API key (get from https://aistudio.google.com/app/apikey)

## Setup
1. Copy the env example and add your API key:
   - `backend\.env.example` -> `backend\.env`
   - Set `GOOGLE_API_KEY` and (optionally) `GOOGLE_MODEL`
   - Get your API key from: https://aistudio.google.com/app/apikey
2. Copy the frontend env example for local dev:
   - `frontend\.env.example` -> `frontend\.env`
   - Keep `VITE_API_BASE_URL=http://localhost:8000`
3. Install LibreOffice if not already installed and ensure `soffice` is available in your PATH.
4. Optional performance tuning in `backend\.env`:
   - `MAX_CONCURRENCY` (higher = faster, more API pressure)
   - `IMAGE_MAX_SIDE` (lower = faster, less detail)
   - `IMAGE_JPEG_QUALITY` (lower = faster, more compression)

## Run
- Double-click `run.bat` to launch backend + frontend.
- The UI will open at `http://localhost:5173`.

## Usage
1. Upload up to 30 files (PNG/JPG/SVG/GIF/PPT/PPTX).
2. Review or edit the prompt.
3. Click **Generate metadata**.
4. Download the Excel file when processing completes.

## Notes
- Each slide is processed independently to avoid mixed tags/names.
- If a PPT contains many slides, the number of assets may exceed the initial file count.

## Troubleshooting
- LibreOffice errors: confirm `soffice` runs from a terminal.
- Google API errors: confirm `GOOGLE_API_KEY` is set in `backend\.env`. Check your API key at https://aistudio.google.com/app/apikey
- CORS issues: frontend uses `http://localhost:5173` by default; update `frontend\.env.example` if needed.
- PPT/PPTX conversion errors on Windows: set `SOFFICE_PATH` in `backend\.env`, for example `C:\Program Files\LibreOffice\program\soffice.exe`.

## Railway (Docker)
This repo includes a `Dockerfile` that builds the frontend and serves it from FastAPI, with LibreOffice preinstalled for PPT conversion.

1. Deploy to Railway using the Dockerfile (Railway auto-detects it).
2. Set environment variables in Railway:
   - `GOOGLE_API_KEY` (required) - Get from https://aistudio.google.com/app/apikey
   - `GOOGLE_MODEL` (optional, default: `gemini-2.5-flash-lite`)
   - `MAX_CONCURRENCY` (optional)
   - `MAX_FILES` (optional)
   - `CORS_ORIGINS` (optional, set to your Railway domain or `*`)
3. Railway supplies `PORT` automatically.

The UI is served at the root URL (`/`), and the API lives under `/api`.

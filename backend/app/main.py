from __future__ import annotations

import uuid
from pathlib import Path
from typing import List

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .config import (
    DATA_DIR,
    DEFAULT_PROMPT,
    ENFORCEMENT_APPENDIX,
    SETTINGS,
    STATIC_DIR,
)
from .dedup import apply_duplicate_suffixes
from .excel import write_excel
from .file_utils import (
    convert_ppt_to_images,
    is_image,
    is_presentation,
    prepare_image,
    save_upload_file,
)
from .models import AssetTask
from .processors import process_assets

app = FastAPI(title="Asset Metadata Generator")

app.add_middleware(
    CORSMiddleware,
    allow_origins=SETTINGS.cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

DOWNLOADS: dict[str, Path] = {}


@app.get("/api/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/process")
async def process_files(
    files: List[UploadFile] = File(...),
    prompt: str | None = Form(default=None),
) -> dict:
    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded.")
    if len(files) > SETTINGS.max_files:
        raise HTTPException(
            status_code=400,
            detail=f"Upload limit exceeded. Max is {SETTINGS.max_files} files.",
        )

    job_id = uuid.uuid4().hex
    job_dir = DATA_DIR / job_id
    uploads_dir = job_dir / "uploads"
    slides_dir = job_dir / "slides"
    prepared_dir = job_dir / "prepared"
    outputs_dir = job_dir / "outputs"
    outputs_dir.mkdir(parents=True, exist_ok=True)

    base_prompt = (prompt or "").strip() or DEFAULT_PROMPT
    prompt_text = f"{base_prompt}\n\n{ENFORCEMENT_APPENDIX}"

    tasks: list[AssetTask] = []
    for upload in files:
        saved_path = await save_upload_file(upload, uploads_dir)
        try:
            if is_presentation(saved_path):
                slide_out_dir = slides_dir / saved_path.stem
                slide_images = convert_ppt_to_images(
                    saved_path,
                    slide_out_dir,
                    SETTINGS.soffice_path,
                )
                for index, slide_path in enumerate(slide_images, start=1):
                    prepared = prepare_image(
                        slide_path,
                        prepared_dir,
                        SETTINGS.image_max_side,
                        SETTINGS.image_jpeg_quality,
                    )
                    tasks.append(
                        AssetTask(
                            task_id=uuid.uuid4().hex,
                            source_name=saved_path.name,
                            display_name=f"{saved_path.name} (slide {index})",
                            image_path=prepared,
                        )
                    )
            elif is_image(saved_path):
                prepared = prepare_image(
                    saved_path,
                    prepared_dir,
                    SETTINGS.image_max_side,
                    SETTINGS.image_jpeg_quality,
                )
                tasks.append(
                    AssetTask(
                        task_id=uuid.uuid4().hex,
                        source_name=saved_path.name,
                        display_name=saved_path.name,
                        image_path=prepared,
                    )
                )
            else:
                raise HTTPException(
                    status_code=400,
                    detail=f"Unsupported file type: {saved_path.name}",
                )
        except (RuntimeError, ValueError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    if not tasks:
        raise HTTPException(status_code=400, detail="No assets were detected.")

    try:
        results = await process_assets(
            tasks,
            prompt_text,
            SETTINGS.google_api_key,
            SETTINGS.google_model,
            SETTINGS.max_concurrency,
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    results = apply_duplicate_suffixes(results)

    output_path = outputs_dir / f"asset_metadata_{job_id}.xlsx"
    write_excel(results, output_path)
    DOWNLOADS[job_id] = output_path

    response_results = [
        {
            "uploaded": result.display_name,
            "english": result.english_name,
            "arabic": result.arabic_name,
            "tags": result.tags,
        }
        for result in results
    ]

    return {
        "job_id": job_id,
        "total": len(response_results),
        "download_url": f"/api/download/{job_id}",
        "results": response_results,
        "prompt_used": prompt_text,
    }


@app.get("/api/download/{job_id}")
def download_excel(job_id: str) -> FileResponse:
    path = DOWNLOADS.get(job_id)
    if not path or not path.exists():
        raise HTTPException(status_code=404, detail="File not found.")

    return FileResponse(
        path,
        media_type=(
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        ),
        filename=path.name,
    )


if (STATIC_DIR / "index.html").exists():
    app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")

from __future__ import annotations

import re
import shutil
import subprocess
import uuid
from pathlib import Path
from typing import List

from cairosvg import svg2png
from fastapi import UploadFile
from PIL import Image

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".svg"}
PRESENTATION_EXTENSIONS = {".ppt", ".pptx"}
DEFAULT_SOFFICE_PATHS = [
    Path("C:/Program Files/LibreOffice/program/soffice.exe"),
    Path("C:/Program Files (x86)/LibreOffice/program/soffice.exe"),
]


def sanitize_filename(filename: str) -> str:
    return Path(filename).name


async def save_upload_file(upload: UploadFile, dest_dir: Path) -> Path:
    dest_dir.mkdir(parents=True, exist_ok=True)
    safe_name = sanitize_filename(upload.filename or f"upload_{uuid.uuid4().hex}")
    dest_path = dest_dir / safe_name
    content = await upload.read()
    dest_path.write_bytes(content)
    await upload.close()
    return dest_path


def is_presentation(path: Path) -> bool:
    return path.suffix.lower() in PRESENTATION_EXTENSIONS


def is_image(path: Path) -> bool:
    return path.suffix.lower() in IMAGE_EXTENSIONS


def natural_sort_key(path: Path) -> List[object]:
    parts = re.split(r"(\d+)", path.stem)
    key: List[object] = []
    for part in parts:
        if part.isdigit():
            key.append(int(part))
        else:
            key.append(part.lower())
    return key


def _resolve_soffice(override: str | None) -> str:
    if override:
        candidate = Path(override)
        if candidate.exists():
            return str(candidate)
        found = shutil.which(override)
        if found:
            return found
        raise RuntimeError(
            "LibreOffice was not found at SOFFICE_PATH. "
            "Set SOFFICE_PATH to the full path or ensure soffice is on PATH."
        )

    found = shutil.which("soffice")
    if found:
        return found

    for path in DEFAULT_SOFFICE_PATHS:
        if path.exists():
            return str(path)

    raise RuntimeError(
        "LibreOffice (soffice) was not found. Install LibreOffice or set "
        "SOFFICE_PATH to the full path of soffice.exe."
    )


def convert_ppt_to_images(
    ppt_path: Path,
    out_dir: Path,
    soffice_path: str | None = None,
) -> List[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    soffice = _resolve_soffice(soffice_path)
    command = [
        soffice,
        "--headless",
        "--convert-to",
        "png",
        "--outdir",
        str(out_dir),
        str(ppt_path),
    ]
    result = subprocess.run(command, check=False, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(
            f"LibreOffice conversion failed for {ppt_path.name}: {result.stderr.strip()}"
        )
    png_files = sorted(out_dir.glob("*.png"), key=natural_sort_key)
    if not png_files:
        raise RuntimeError(f"No slides were exported for {ppt_path.name}.")
    return png_files


def _has_alpha(image: Image.Image) -> bool:
    if image.mode in {"RGBA", "LA"}:
        return True
    return image.mode == "P" and "transparency" in image.info


def _clamp_jpeg_quality(value: int) -> int:
    return max(40, min(value, 95))


def optimize_image(
    path: Path,
    out_dir: Path,
    max_side: int,
    jpeg_quality: int,
) -> Path:
    if max_side <= 0:
        return path

    with Image.open(path) as img:
        width, height = img.size
        if max(width, height) <= max_side:
            return path

        has_alpha = _has_alpha(img)
        img = img.convert("RGBA" if has_alpha else "RGB")
        img.thumbnail((max_side, max_side), Image.Resampling.LANCZOS)

        out_dir.mkdir(parents=True, exist_ok=True)
        suffix = ".png" if has_alpha else ".jpg"
        output_path = out_dir / f"{path.stem}_{uuid.uuid4().hex}{suffix}"

        if has_alpha:
            img.save(output_path, format="PNG", optimize=True)
        else:
            quality = _clamp_jpeg_quality(jpeg_quality)
            img.save(
                output_path,
                format="JPEG",
                quality=quality,
                optimize=True,
                progressive=True,
            )

        return output_path


def prepare_image(
    path: Path,
    out_dir: Path,
    max_side: int,
    jpeg_quality: int,
) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    ext = path.suffix.lower()
    if ext in {".png", ".jpg", ".jpeg"}:
        return optimize_image(path, out_dir, max_side, jpeg_quality)

    output_path = out_dir / f"{path.stem}_{uuid.uuid4().hex}.png"

    if ext == ".gif":
        with Image.open(path) as img:
            img.seek(0)
            frame = img.convert("RGBA")
            frame.save(output_path, format="PNG")
        return optimize_image(output_path, out_dir, max_side, jpeg_quality)

    if ext == ".svg":
        svg2png(url=str(path), write_to=str(output_path))
        return optimize_image(output_path, out_dir, max_side, jpeg_quality)

    raise ValueError(f"Unsupported image format: {ext}")

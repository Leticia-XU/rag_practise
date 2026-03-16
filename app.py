import io
import os
import threading
from typing import Any, List

import numpy as np
from fastapi import FastAPI, File, Form, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from paddleocr import PaddleOCR
from PIL import Image

try:
    from pdf2image import convert_from_bytes
    PDF2IMAGE_OK = True
except Exception:
    PDF2IMAGE_OK = False

app = FastAPI(title="PaddleOCR API", version="1.0")

MAX_CONCURRENCY = int(os.getenv("OCR_MAX_CONCURRENCY", "1"))
_sem = threading.Semaphore(MAX_CONCURRENCY)

OCR_LANG = os.getenv("OCR_LANG", "ch")
USE_ANGLE_CLS = os.getenv("OCR_USE_ANGLE_CLS", "true").lower() == "true"
USE_GPU = os.getenv("OCR_USE_GPU", "true").lower() == "true"

ocr = PaddleOCR(use_gpu=USE_GPU, lang=OCR_LANG, use_angle_cls=USE_ANGLE_CLS)

def _img_from_bytes(file_bytes: bytes) -> np.ndarray:
    try:
        img = Image.open(io.BytesIO(file_bytes)).convert("RGB")
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid image.")
    # PaddleOCR accepts ndarray (H,W,3) RGB as well; if you prefer BGR you can swap channels.
    return np.array(img)

def _run_ocr_on_img(img: np.ndarray) -> Any:
    return ocr.ocr(img)

@app.get("/health")
def health():
    return {"status": "ok", "gpu": USE_GPU, "lang": OCR_LANG, "max_concurrency": MAX_CONCURRENCY}

@app.post("/ocr/image")
async def ocr_image(image: UploadFile = File(...)):
    data = await image.read()

    if not _sem.acquire(timeout=300):
        raise HTTPException(status_code=429, detail="OCR busy, try later.")
    try:
        img = Image.open(io.BytesIO(data)).convert("RGB")
        arr = np.array(img)
        res = _run_ocr_on_img(arr)
        return JSONResponse(content={"result": res})
    finally:
        _sem.release()

@app.post("/ocr/pdf")
async def ocr_pdf(
    pdf: UploadFile = File(...),
    dpi: int = Form(200),
    max_pages: int = Form(50),
):
    if not PDF2IMAGE_OK:
        raise HTTPException(status_code=500, detail="PDF support not enabled (pdf2image/poppler missing).")

    pdf_bytes = await pdf.read()

    if not _sem.acquire(timeout=300):
        raise HTTPException(status_code=429, detail="OCR busy, try later.")
    try:
        images = convert_from_bytes(pdf_bytes, dpi=dpi)[:max_pages]
        out: List[Any] = []
        for pil_img in images:
            arr = np.array(pil_img.convert("RGB"))
            out.append(_run_ocr_on_img(arr))
        return JSONResponse(content={"pages": len(out), "result": out})
    finally:
        _sem.release()


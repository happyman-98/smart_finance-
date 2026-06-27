from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from sqlalchemy.orm import Session
from models.database import get_db
from models.schemas import Transaction, User
from services.ocr_scanner import GeminiEngine, OllamaVisionEngine, TesseractEngine
from services.auth_service import get_current_user as get_current_user_import
from datetime import datetime
import shutil, os, uuid, logging, time

logger = logging.getLogger(__name__)

router = APIRouter()

UPLOAD_DIR = "temp_uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

ENGINES = {
    "gemini":    GeminiEngine,
    "ollama":    OllamaVisionEngine,
    "tesseract": TesseractEngine,
}

MAX_RETRIES   = 3
RETRY_DELAYS  = [2, 5, 10]   # seconds between each attempt


def is_retryable(exc: Exception) -> bool:
    msg = str(exc).lower()
    return any(k in msg for k in ("503", "unavailable", "rate", "quota", "resource exhausted", "timeout"))


def run_ocr_with_retry(engine_cls, temp_path: str):
    last_exc = None
    for attempt in range(MAX_RETRIES):
        try:
            ocr = engine_cls()
            return ocr.extract(temp_path)
        except Exception as e:
            last_exc = e
            if is_retryable(e) and attempt < MAX_RETRIES - 1:
                wait = RETRY_DELAYS[attempt]
                logger.warning(
                    f"OCR attempt {attempt + 1} failed (retryable): {e}. "
                    f"Retrying in {wait}s…"
                )
                time.sleep(wait)
            else:
                raise
    raise last_exc


@router.post("/upload-receipt")
async def upload_receipt(
    file:         UploadFile = File(...),
    engine:       str        = Form("tesseract"),
    db:           Session    = Depends(get_db),
    current_user: User       = Depends(get_current_user_import),
):
    ext       = os.path.splitext(file.filename)[1] or ".jpg"
    temp_path = f"{UPLOAD_DIR}/{uuid.uuid4()}{ext}"

    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        engine_cls = ENGINES.get(engine, GeminiEngine)
        logger.info(f"OCR: engine={engine_cls.name}, file={file.filename}, user={current_user.id}")

        try:
            ex = run_ocr_with_retry(engine_cls, temp_path)
        except Exception as e:
            msg = str(e)
            if "503" in msg or "unavailable" in msg.lower():
                raise HTTPException(
                    status_code=503,
                    detail=(
                        "Gemini is currently overloaded. "
                        "Please try again in a minute, or switch to Tesseract engine."
                    ),
                )
            if "quota" in msg.lower() or "rate" in msg.lower():
                raise HTTPException(
                    status_code=429,
                    detail=(
                        "API rate limit reached. "
                        "Wait a moment and try again, or switch to Tesseract engine."
                    ),
                )
            raise HTTPException(status_code=500, detail=f"OCR failed: {msg}")

        logger.info(
            f"OCR done: confidence={ex.overall_confidence:.2f}, "
            f"merchant={ex.merchant.value}, total={ex.total.value}, date={ex.date.value}"
        )

        return {
            "status":     "needs_review",
            "confidence": ex.overall_confidence,
            "engine":     ex.engine,
            "extracted": {
                "merchant": ex.merchant.value,
                "total":    ex.total.value,
                "date":     ex.date.value,
                "currency": ex.currency.value,
            },
            "line_items": [item.dict() for item in ex.line_items],
            "taxes":      [tax.dict()  for tax  in ex.taxes],
            "tax_total":  ex.tax_total(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("OCR failed")
        raise HTTPException(status_code=500, detail=f"OCR failed: {str(e)}")

    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


@router.post("/upload-receipt/confirm")
async def confirm_receipt(
    merchant:     str,
    amount:       float,
    date:         str,
    db:           Session = Depends(get_db),
    current_user: User    = Depends(get_current_user_import),
):
    try:
        parsed_date = datetime.fromisoformat(date)
    except Exception:
        parsed_date = datetime.utcnow()

    transaction = Transaction(
        user_id     = current_user.id,
        amount      = amount,
        category    = "Uncategorized",
        merchant    = merchant,
        date        = parsed_date,
        type        = "expense",
        description = "Scanned receipt",
    )
    db.add(transaction)
    db.commit()
    db.refresh(transaction)

    logger.info(f"Receipt confirmed: user={current_user.id}, merchant={merchant}, amount={amount}")
    return {"status": "saved", "transaction_id": transaction.id}
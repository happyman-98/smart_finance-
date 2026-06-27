from __future__ import annotations

import os
import re
import pytesseract
import requests  
import base64
import mimetypes
from google import genai          
from google.genai import types
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from PIL import Image, ImageOps

load_dotenv()

# ── API KEY ───────────────────────────────────────────────
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    raise EnvironmentError(
        "GOOGLE_API_KEY is not set. Add it to your .env file as:\n"
        "GOOGLE_API_KEY=your_key_here"
    )


class Conf(BaseModel):
    value: float | str | int | None = None
    confidence: float = 0.0  # 0..1


class LineItem(BaseModel):
    name: str | None = None
    hsn_sac: str | None = None
    qty: float | None = None
    rate: float | None = None
    taxable_value: float | None = None


class TaxLine(BaseModel):
    kind: str | None = None       
    rate_pct: float | None = None
    amount: float | None = None


class Extraction(BaseModel):
    merchant: Conf = Conf()
    invoice_no: Conf = Conf()
    date: Conf = Conf()        
    currency: Conf = Conf()
    subtotal: Conf = Conf()     
    total: Conf = Conf()         
    line_items: list[LineItem] = Field(default_factory=list)
    taxes: list[TaxLine] = Field(default_factory=list)
    overall_confidence: float = 0.0
    engine: str = ""

    def tax_total(self) -> float:
        return round(sum(t.amount or 0.0 for t in self.taxes), 2)

_PROMPT = (
    "Extract this invoice/receipt as JSON matching the schema. Use the GRAND "
    "TOTAL (including tax) for `total`, not subtotal or tendered. Split each tax "
    "line (IGST/CGST/SGST/VAT) into the taxes array. Dates as ISO 8601. Numbers "
    "as plain floats, no thousands separators, no currency symbol. If a field is "
    "absent, set value null and confidence 0. Reply with JSON only, no prose."
)

class TesseractEngine:
    name = "tesseract"

    def extract(self, image_path: str) -> Extraction:

        img = ImageOps.grayscale(Image.open(image_path))
        if max(img.size) < 2000:                     
            scale = 2000 / max(img.size)
            img = img.resize((int(img.width * scale), int(img.height * scale)))
        img = img.point(lambda p: 255 if p > 160 else 0) 

        text = pytesseract.image_to_string(img)

        amounts = [float(a.replace(",", "")) for a in
                   re.findall(r"\d[\d,]*\.\d{2}", text)]
        total_guess = max(amounts) if amounts else None 
        merchant_guess = next((l.strip() for l in text.splitlines() if l.strip()), None)

        return Extraction(
            merchant=Conf(value=merchant_guess, confidence=0.4),
            total=Conf(value=total_guess, confidence=0.35 if total_guess else 0.0),
            currency=Conf(value="INR" if "\u20b9" in text or "RUPEES" in text.upper() else None,
                          confidence=0.5),
            taxes=[],                   
            overall_confidence=0.35,  
            engine=self.name,
        )

class OllamaVisionEngine:
    name = "ollama"

    def __init__(self, model: str = "qwen2.5vl:7b", host: str = "http://127.0.0.1:11434"):
        self.model = model
        self.host = host

    def extract(self, image_path: str) -> Extraction:   

        with open(image_path, "rb") as f:
            b64 = base64.standard_b64encode(f.read()).decode()

        r = requests.post(
            f"{self.host}/api/chat",
            json={
                "model": self.model,
                "stream": False,
                "options": {"num_ctx": 8192},
                "messages": [{
                    "role": "user",
                    "content": _PROMPT,
                    "images": [b64],
                }],
            },
            timeout=300,
        )
        r.raise_for_status()
        content = r.json()["message"]["content"]
        ex = Extraction.model_validate_json(content)
        ex.engine = self.name
        return ex

class GeminiEngine:
    name = "gemini"

    def __init__(self, model: str = "gemini-2.0-flash"):   #gemini-2.0-flash
        self.model = model
        # Explicitly pass the API key so it works regardless of
        # whether the environment variable is auto-detected
        self.client = genai.Client(api_key=GOOGLE_API_KEY)

    def extract(self, image_path: str) -> Extraction:

        media_type = mimetypes.guess_type(image_path)[0] or "image/jpeg"
        with open(image_path, "rb") as f:
            img_bytes = f.read()

        resp = self.client.models.generate_content(
            model=self.model,
            contents=[
                types.Part.from_bytes(data=img_bytes, mime_type=media_type),
                _PROMPT,
            ],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=Extraction,
            ),
        )
        if getattr(resp, "parsed", None) is not None:
            ex = resp.parsed if isinstance(resp.parsed, Extraction) \
                 else Extraction.model_validate(resp.parsed)
        else:
            ex = Extraction.model_validate_json(resp.text)
        ex.engine = self.name
        return ex
    
class VisionLLMEngine:
    name = "vision-llm"

    def __init__(self, model: str = "qwen2.5vl:7b", host: str = "http://127.0.0.1:11434"):
        self._backend = OllamaVisionEngine(model=model, host=host)

    def extract(self, image_path: str) -> Extraction:
        ex = self._backend.extract(image_path)
        ex.engine = self.name      
        return ex
    
AUTO_SAVE_THRESHOLD = 0.85

def decide(ex: Extraction) -> str:
    has_core = ex.merchant.value and ex.total.value is not None
    if ex.overall_confidence >= AUTO_SAVE_THRESHOLD and has_core:
        return "saved"         
    return "needs_review"     


ENGINES = {
    "tesseract": TesseractEngine,
    "ollama": OllamaVisionEngine,
    "gemini": GeminiEngine,
    "vision": VisionLLMEngine,
}

if __name__ == "__main__":
    import sys
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    flags = [a[2:] for a in sys.argv[1:] if a.startswith("--")]

    path = args[0] if args else "together.jpg"
    engine_name = next((f for f in flags if f in ENGINES), "vision")
    engine = ENGINES[engine_name]()

    ex = engine.extract(path)
    print(ex.model_dump_json(indent=2))
    print("decision:", decide(ex), "| tax_total:", ex.tax_total())
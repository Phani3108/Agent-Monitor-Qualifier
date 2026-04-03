from __future__ import annotations
from langdetect import detect, DetectorFactory
from typing import Optional

DetectorFactory.seed = 42  # stable predictions

LANG_MAP = {
    "en": "en", "hi": "hi", "fr": "fr", "de": "de", "es": "es", "it": "it", "pt": "pt",
    "zh-cn": "zh", "zh-tw": "zh", "ja": "ja", "ko": "ko"
}

def detect_lang(text: str) -> Optional[str]:
    t = (text or "").strip()
    if not t:
        return None
    try:
        code = detect(t)
        return LANG_MAP.get(code.lower(), code.lower())
    except Exception:
        return None

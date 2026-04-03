from __future__ import annotations
import re
from typing import Dict

# very lightweight detectors
RE_SSN = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")
RE_DATE = re.compile(r"\b(19|20)\d{2}[-/](0?[1-9]|1[0-2])[-/](0?[1-9]|[12]\d|3[01])\b")
RE_PAN_CHUNK = re.compile(r"(?:\d[ -]?){13,19}")

def luhn_ok(s: str) -> bool:
    digits = [int(c) for c in s if c.isdigit()]
    if len(digits) < 13 or len(digits) > 19: return False
    checksum = 0
    parity = (len(digits) - 2) % 2
    for i, d in enumerate(digits[:-1]):
        if i % 2 == parity:
            d *= 2
            if d > 9: d -= 9
        checksum += d
    return (checksum + digits[-1]) % 10 == 0

def detect_pii(text: str) -> Dict[str, bool]:
    text = text.strip()
    has_ssn = bool(RE_SSN.search(text))
    has_date = bool(RE_DATE.search(text))
    has_pan = False
    for m in RE_PAN_CHUNK.finditer(text):
        chunk = re.sub(r"[ -]", "", m.group(0))
        if luhn_ok(chunk):
            has_pan = True
            break
    return {"pan": has_pan, "ssn": has_ssn, "date": has_date}

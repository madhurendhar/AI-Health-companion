"""Fail CI if likely secrets are committed."""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
SKIP = {".git", ".venv", "venv", "__pycache__", ".pio", "node_modules"}
PATTERNS = [
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"(?i)aws_secret_access_key\s*=\s*['\"]?[A-Za-z0-9/+=]{20,}"),
    re.compile(r"BEGIN (RSA |OPENSSH )?PRIVATE KEY"),
]


def test_no_secrets():
    hits = []
    for p in ROOT.rglob("*"):
        if any(part in SKIP for part in p.parts):
            continue
        if p.suffix in {".png", ".jpg", ".bin", ".pyc", ".joblib"}:
            continue
        if not p.is_file():
            continue
        try:
            text = p.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for pat in PATTERNS:
            if pat.search(text):
                hits.append(f"{p}: {pat.pattern}")
    assert hits == [], hits

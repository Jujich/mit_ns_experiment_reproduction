"""PDF table extraction helpers (local pdftotext + optional LLM structuring)."""

from __future__ import annotations

import json
import os
import re
import subprocess
from pathlib import Path

from mit_ns import ROOT

PDF_PATH = ROOT / "22549470-MIT.pdf"


KNOWN_EXTRACTIONS = {
    "table_9_1": {
        "pages": (340, 340),
        "description": "Design Value components Original vs Modular SH II",
        "expected_keys": ["MOM", "MAV", "PPRV", "CVV", "MFV"],
    },
    "table_9_2": {
        "pages": (345, 345),
        "description": "Cost estimate comparison for DV components",
        "expected_keys": ["MOM", "PPRV", "CVV"],
    },
    "table_6_2": {
        "pages": (206, 206),
        "description": "25 RAB systems for matrix analysis",
        "expected_keys": ["RCS", "SIS", "RHR"],
    },
}


def extract_pages_text(pdf: Path = PDF_PATH, first: int = 1, last: int | None = None) -> str:
    if last is None:
        last = first
    cmd = ["pdftotext", "-f", str(first), "-l", str(last), "-layout", str(pdf), "-"]
    result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        raise RuntimeError(result.stderr or "pdftotext failed")
    return result.stdout


def extract_numbers(text: str) -> list[float]:
    return [float(x.replace(",", "")) for x in re.findall(r"\d{1,3}(?:,\d{3})+|\d+(?:\.\d+)?", text)]


def extract_known_table(name: str) -> dict:
    meta = KNOWN_EXTRACTIONS[name]
    first, last = meta["pages"]
    text = extract_pages_text(first=first, last=last)
    return {
        "name": name,
        "description": meta["description"],
        "pages": meta["pages"],
        "raw_text": text,
        "numbers_found": extract_numbers(text)[:40],
        "expected_keys": meta["expected_keys"],
    }


def optional_llm_structure(raw_text: str, schema_hint: str) -> dict | None:
    """If OPENAI_API_KEY is set, ask the model to structure the table as JSON.

    Otherwise return None (offline-safe path).
    """
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        return None
    try:
        from urllib import request

        payload = {
            "model": os.environ.get("OPENAI_MODEL", "gpt-4o-mini"),
            "messages": [
                {
                    "role": "system",
                    "content": "Extract tables from thesis OCR text into compact JSON only.",
                },
                {
                    "role": "user",
                    "content": f"Schema hint: {schema_hint}\n\nText:\n{raw_text[:12000]}",
                },
            ],
            "temperature": 0,
        }
        req = request.Request(
            "https://api.openai.com/v1/chat/completions",
            data=json.dumps(payload).encode(),
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        with request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read().decode())
        content = data["choices"][0]["message"]["content"]
        # try parse JSON object from response
        match = re.search(r"\{.*\}", content, flags=re.S)
        if match:
            return json.loads(match.group(0))
        return {"raw": content}
    except Exception as exc:  # noqa: BLE001
        return {"error": str(exc)}


def extract_all_known(use_llm: bool = False) -> dict:
    out = {}
    for name in KNOWN_EXTRACTIONS:
        item = extract_known_table(name)
        if use_llm:
            item["llm_structured"] = optional_llm_structure(
                item["raw_text"], f"Extract {name}: {item['description']}"
            )
        out[name] = item
    return out

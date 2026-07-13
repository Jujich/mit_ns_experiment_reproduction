#!/usr/bin/env python3
"""Extract known thesis tables via pdftotext (+ optional LLM structuring)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from mit_ns import OUTPUT_DIR
from mit_ns.pdf_extract import extract_all_known, extract_known_table


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--table", choices=["table_9_1", "table_9_2", "table_6_2", "all"], default="all")
    parser.add_argument("--llm", action="store_true", help="Try OpenAI structuring if API key set")
    args = parser.parse_args()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    if args.table == "all":
        data = extract_all_known(use_llm=args.llm)
    else:
        item = extract_known_table(args.table)
        if args.llm:
            from mit_ns.pdf_extract import optional_llm_structure

            item["llm_structured"] = optional_llm_structure(item["raw_text"], item["description"])
        data = {args.table: item}

    # strip huge raw text from summary print, keep in file
    path = OUTPUT_DIR / "pdf_extractions.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    for name, item in data.items():
        print(f"{name}: pages={item['pages']} numbers_sample={item['numbers_found'][:12]}")
    print(f"Wrote {path}")


if __name__ == "__main__":
    main()

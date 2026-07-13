#!/usr/bin/env python3
"""CLI navigator for Lapp Ch.5 Steps 1–12 (LLM-ready context pack)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from mit_ns import OUTPUT_DIR
from mit_ns.methodology import (
    STEPS,
    build_context_pack,
    methodology_overview,
    render_step_markdown,
)


def maybe_ask_llm(prompt: str) -> str | None:
    import os

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        return None
    try:
        from urllib import request

        context = build_context_pack()
        payload = {
            "model": os.environ.get("OPENAI_MODEL", "gpt-4o-mini"),
            "messages": [
                {"role": "system", "content": context["agent_instructions"]},
                {
                    "role": "user",
                    "content": (
                        "Context JSON (truncated):\n"
                        + json.dumps(
                            {
                                "steps": context["steps"],
                                "constraints": context["constraints"],
                                "table_9_1": context["table_9_1_dv_components"],
                            },
                            ensure_ascii=False,
                        )[:14000]
                        + f"\n\nUser question:\n{prompt}"
                    ),
                },
            ],
            "temperature": 0.2,
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
        with request.urlopen(req, timeout=90) as resp:
            data = json.loads(resp.read().decode())
        return data["choices"][0]["message"]["content"]
    except Exception as exc:  # noqa: BLE001
        return f"[LLM error] {exc}"


def main() -> None:
    parser = argparse.ArgumentParser(description="MIT modular design methodology navigator")
    parser.add_argument("--step", type=int, help="Show a single step 1–12")
    parser.add_argument("--list", action="store_true", help="List all steps")
    parser.add_argument("--export-context", action="store_true", help="Write LLM context pack JSON")
    parser.add_argument("--ask", type=str, help="Optional LLM question (needs OPENAI_API_KEY)")
    args = parser.parse_args()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    if args.list or (not args.step and not args.export_context and not args.ask):
        for s in STEPS:
            print(f"{s.number:2d}. {s.title}  [{s.status_in_repo}]")

    if args.step:
        print(render_step_markdown(args.step))

    if args.export_context:
        pack = build_context_pack()
        path = OUTPUT_DIR / "methodology_context_pack.json"
        with open(path, "w", encoding="utf-8") as f:
            json.dump(pack, f, ensure_ascii=False, indent=2)
        print(f"Wrote {path}")

    if args.ask:
        answer = maybe_ask_llm(args.ask)
        if answer is None:
            # offline deterministic answer from local steps
            overview = methodology_overview()
            done = [s for s in overview if "DONE" in s["status_in_repo"]]
            pending = [s for s in overview if "DONE" not in s["status_in_repo"]]
            print("OPENAI_API_KEY not set — offline summary:\n")
            print("Done steps:", ", ".join(f"{s['number']}" for s in done) or "none")
            print("Open steps:", ", ".join(f"{s['number']}:{s['title']}" for s in pending))
            print("\nQuestion was:", args.ask)
            print("Export --export-context and attach to your LLM of choice.")
        else:
            print(answer)


if __name__ == "__main__":
    main()

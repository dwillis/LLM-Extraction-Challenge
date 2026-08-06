#!/usr/bin/env python3
"""Generate smevals task YAMLs from ../training.csv.

The prompt template below is a verbatim copy of the "prompt2" f-string in
../email_llm.py (lines 26-31). Keep the two in sync -- if they diverge,
scores from this eval stop being comparable to the *_prompt2.json rows in
the leaderboard.
"""
import argparse
import csv
import sys
from pathlib import Path

import yaml

# Email bodies can exceed the stdlib csv module's default field size limit.
csv.field_size_limit(10**9)

PROMPT_TEMPLATE = """Extract the following information from this email:
1. 'committee': The name of the committee in the disclaimer that begins with "Paid for by" but do not include the "Paid for by" text itself. If no committee is present, use null.
2. 'sender': The name of the person, if any, mentioned as the author of the email. If there is no person named, use null.

Email body:
{body}"""

HERE = Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--csv", type=Path, default=HERE.parent / "training.csv",
        help="Path to the ground-truth CSV (default: ../training.csv)",
    )
    parser.add_argument(
        "--out", type=Path, default=HERE / "tasks",
        help="Directory to write task YAMLs into (default: ./tasks)",
    )
    parser.add_argument(
        "--limit", type=int, default=None,
        help="Only generate the first N tasks (for smoke testing)",
    )
    args = parser.parse_args()

    args.out.mkdir(parents=True, exist_ok=True)

    # Clear stale generated tasks so a --limit run doesn't mix with a prior
    # full run (or vice versa).
    for stale in args.out.glob("email-*.yaml"):
        stale.unlink()

    with open(args.csv, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    if args.limit is not None:
        rows = rows[: args.limit]

    for i, row in enumerate(rows):
        task = {
            "name": f"email-{i:04d}",
            "prompt": PROMPT_TEMPLATE.format(body=row["body"]),
            "committee": row["committee"],
            "sender": row["name"],
            "subject": row["subject"],
        }
        out_path = args.out / f"email-{i:04d}.yaml"
        with open(out_path, "w", encoding="utf-8") as f:
            yaml.safe_dump(
                task, f, sort_keys=False, allow_unicode=True, width=1_000_000
            )

    print(f"Wrote {len(rows)} task(s) to {args.out}")


if __name__ == "__main__":
    main()

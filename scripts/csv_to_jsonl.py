#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: 2026 - William Jose Moreno Reyes (CP/MBA)

import sys
from pathlib import Path

from dataset_amplification import load_and_amplify, write_full_jsonl

# ----------------------------
# DEFAULT PATHS (PROJECT ROOT)
# ----------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = PROJECT_ROOT / "data" / "raw" / "personal_finance_dataset.csv"
DEFAULT_SEED = PROJECT_ROOT / "data" / "raw" / "data_sed.csv"
DEFAULT_OUTPUT = (
    PROJECT_ROOT / "data" / "processed" / "personal_finance_chatml_full.jsonl"
)


def _regenerate_pair_ids(rows: list[dict], start_number: int = 1) -> None:
    """Assign pair_id sequentially from start_number, grouping bilingual rows."""
    next_pair_number = start_number
    current_pair_id = f"{next_pair_number:06d}"
    seen_languages: set[str] = set()

    for row in rows:
        language = (row.get("language") or "").strip().lower()

        if not seen_languages:
            seen_languages.add(language)
            row["pair_id"] = current_pair_id
            continue

        if language in seen_languages:
            next_pair_number += 1
            current_pair_id = f"{next_pair_number:06d}"
            seen_languages = {language}
            row["pair_id"] = current_pair_id
            continue

        seen_languages.add(language)
        row["pair_id"] = current_pair_id

        if {"es", "en"}.issubset(seen_languages):
            next_pair_number += 1
            current_pair_id = f"{next_pair_number:06d}"
            seen_languages.clear()


def csv_to_jsonl(
    input_path: Path,
    output_path: Path,
    seed_path: Path,
) -> None:
    rows, added_pairs = load_and_amplify(input_path, seed_path)
    _regenerate_pair_ids(rows, start_number=1)
    write_full_jsonl(output_path, rows)
    print(f"Amplification completed. Added bilingual pairs: {added_pairs}")
    print("pair_id generated dynamically from 000001")
    print(f"Base CSV unchanged: {input_path}")
    print(f"Successfully generated: {output_path}")


if __name__ == "__main__":
    if len(sys.argv) == 3:
        input_csv = Path(sys.argv[1])
        output_jsonl = Path(sys.argv[2])
        seed_csv = DEFAULT_SEED
    elif len(sys.argv) == 4:
        input_csv = Path(sys.argv[1])
        output_jsonl = Path(sys.argv[2])
        seed_csv = Path(sys.argv[3])
    else:
        input_csv = DEFAULT_INPUT
        output_jsonl = DEFAULT_OUTPUT
        seed_csv = DEFAULT_SEED

    print(f"Input CSV: {input_csv}")
    print(f"Seed CSV: {seed_csv}")
    print(f"Output JSONL: {output_jsonl}")

    try:
        csv_to_jsonl(input_csv, output_jsonl, seed_csv)
    except (FileNotFoundError, ValueError) as error:
        print(f"Error: {error}")
        sys.exit(1)

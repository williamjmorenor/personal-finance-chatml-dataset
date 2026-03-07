#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: 2026 - William Jose Moreno Reyes (CP/MBA)

import csv
import json
import sys
from pathlib import Path


# ----------------------------
# DEFAULT PATHS (PROJECT ROOT)
# ----------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = PROJECT_ROOT / "data" / "raw" / "personal_finance_dataset.csv"
DEFAULT_OUTPUT = (
    PROJECT_ROOT / "data" / "processed" / "personal_finance_chatml_full.jsonl"
)


# ----------------------------
# VALIDATION CONFIG
# ----------------------------

REQUIRED_COLUMNS = {
    "pair_id",
    "system",
    "user",
    "assistant",
    "language",
    "topic",
    "level",
    "domain",
}
VALID_LANGUAGES = {"en", "es"}
VALID_LEVELS = {"basic", "intermediate", "advanced"}


def _norm(row: dict) -> dict:
    """
    Normalize values to reduce accidental inconsistencies.
    """
    normalized = dict(row)
    normalized["pair_id"] = (row.get("pair_id") or "").strip()
    normalized["language"] = (row.get("language") or "").strip().lower()
    normalized["level"] = (row.get("level") or "").strip().lower()
    normalized["domain"] = (row.get("domain") or "").strip().lower()
    normalized["topic"] = (row.get("topic") or "").strip().lower()
    normalized["system"] = (row.get("system") or "").strip()
    normalized["user"] = (row.get("user") or "").strip()
    normalized["assistant"] = (row.get("assistant") or "").strip()
    return normalized


def validate_row(row: dict, row_number: int) -> None:
    """
    Validate a single CSV row.
    Raises ValueError if validation fails.
    """
    for col in REQUIRED_COLUMNS:
        if not row.get(col) or not str(row[col]).strip():
            raise ValueError(f"Row {row_number}: Missing or empty field '{col}'.")

    if row["language"] not in VALID_LANGUAGES:
        raise ValueError(
            f"Row {row_number}: Invalid language '{row['language']}'. "
            f"Must be one of {sorted(VALID_LANGUAGES)}."
        )

    if row["level"] not in VALID_LEVELS:
        raise ValueError(
            f"Row {row_number}: Invalid level '{row['level']}'. "
            f"Must be one of {sorted(VALID_LEVELS)}."
        )

    if len(row["user"]) < 5:
        raise ValueError(f"Row {row_number}: 'user' is too short (< 5 chars).")

    if len(row["assistant"]) < 10:
        raise ValueError(f"Row {row_number}: 'assistant' is too short (< 10 chars).")


def csv_to_jsonl(input_path: Path, output_path: Path) -> None:
    """
    Converts CSV into ChatML JSONL format with flat fields and pair_id.
    """
    if not input_path.exists():
        print(f"Error: Input file '{input_path}' does not exist.")
        sys.exit(1)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    errors = []

    with input_path.open(
        mode="r", encoding="utf-8", newline=""
    ) as csv_file, output_path.open(mode="w", encoding="utf-8") as jsonl_file:
        reader = csv.DictReader(csv_file)

        header_columns = set(reader.fieldnames or [])
        missing_columns = REQUIRED_COLUMNS - header_columns
        if missing_columns:
            print(f"Error: Missing required columns: {sorted(missing_columns)}")
            sys.exit(1)

        for row_number, raw_row in enumerate(reader, start=2):
            try:
                row = _norm(raw_row)
                validate_row(row, row_number)

                record = {
                    "pair_id": row["pair_id"],
                    "language": row["language"],
                    "domain": row["domain"],
                    "topic": row["topic"],
                    "level": row["level"],
                    "system": row["system"],
                    "question": row["user"],
                    "answer": row["assistant"],
                    "messages": [
                        {"role": "system", "content": row["system"]},
                        {"role": "user", "content": row["user"]},
                        {"role": "assistant", "content": row["assistant"]},
                    ],
                }
                jsonl_file.write(json.dumps(record, ensure_ascii=False) + "\n")
            except ValueError as error:
                errors.append(str(error))

    if errors:
        print("Validation errors found:")
        for message in errors[:50]:
            print(f"- {message}")
        if len(errors) > 50:
            print(f"... plus {len(errors) - 50} more.")
        sys.exit(1)

    print(f"Successfully generated: {output_path}")


if __name__ == "__main__":
    if len(sys.argv) == 3:
        input_csv = Path(sys.argv[1])
        output_jsonl = Path(sys.argv[2])
    else:
        input_csv = DEFAULT_INPUT
        output_jsonl = DEFAULT_OUTPUT

    print(f"Input CSV: {input_csv}")
    print(f"Output JSONL: {output_jsonl}")

    csv_to_jsonl(input_csv, output_jsonl)

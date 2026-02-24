#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: 2026 - William José Moreno Reyes (CP/MBA)

import csv
import json
import sys
from pathlib import Path


# ----------------------------
# DEFAULT PATHS (PROJECT ROOT)
# ----------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[1]

DEFAULT_INPUT = PROJECT_ROOT / "data" / "raw" / "personal_finance_dataset.csv"
DEFAULT_OUTPUT = PROJECT_ROOT / "data" / "processed" / "personal_finance_chatml.jsonl"


# ----------------------------
# VALIDATION CONFIG
# ----------------------------

REQUIRED_COLUMNS = {"system", "user", "assistant", "language", "topic", "level"}
VALID_LANGUAGES = {"en", "es"}
VALID_LEVELS = {"basic", "intermediate", "advanced"}


def validate_row(row, row_number):
    """
    Validates a single CSV row.
    Raises ValueError if validation fails.
    """

    for col in REQUIRED_COLUMNS:
        if not row.get(col) or not row[col].strip():
            raise ValueError(f"Row {row_number}: Missing or empty field '{col}'.")

    if row["language"].strip() not in VALID_LANGUAGES:
        raise ValueError(
            f"Row {row_number}: Invalid language '{row['language']}'. "
            f"Must be one of {VALID_LANGUAGES}."
        )

    if row["level"].strip() not in VALID_LEVELS:
        raise ValueError(
            f"Row {row_number}: Invalid level '{row['level']}'. "
            f"Must be one of {VALID_LEVELS}."
        )


def csv_to_jsonl(input_path: Path, output_path: Path):
    """
    Converts CSV into ChatML JSONL format.
    """

    if not input_path.exists():
        print(f"Error: Input file '{input_path}' does not exist.")
        sys.exit(1)

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with input_path.open(mode="r", encoding="utf-8") as csv_file, \
         output_path.open(mode="w", encoding="utf-8") as jsonl_file:

        reader = csv.DictReader(csv_file)

        # Validate header
        header_columns = set(reader.fieldnames or [])
        missing_columns = REQUIRED_COLUMNS - header_columns
        if missing_columns:
            print(f"Error: Missing required columns: {missing_columns}")
            sys.exit(1)

        for row_number, row in enumerate(reader, start=2):
            try:
                validate_row(row, row_number)

                record = {
                    "messages": [
                        {"role": "system", "content": row["system"].strip()},
                        {"role": "user", "content": row["user"].strip()},
                        {"role": "assistant", "content": row["assistant"].strip()}
                    ],
                    "language": row["language"].strip(),
                    "topic": row["topic"].strip(),
                    "level": row["level"].strip()
                }

                jsonl_file.write(
                    json.dumps(record, ensure_ascii=False) + "\n"
                )

            except ValueError as e:
                print(f"Validation error: {e}")
                sys.exit(1)

    print(f"Successfully generated: {output_path}")


if __name__ == "__main__":

    # If user provides custom paths → use them
    if len(sys.argv) == 3:
        input_csv = Path(sys.argv[1])
        output_jsonl = Path(sys.argv[2])
    else:
        # Otherwise use defaults
        input_csv = DEFAULT_INPUT
        output_jsonl = DEFAULT_OUTPUT

    print(f"Input CSV: {input_csv}")
    print(f"Output JSONL: {output_jsonl}")

    csv_to_jsonl(input_csv, output_jsonl)

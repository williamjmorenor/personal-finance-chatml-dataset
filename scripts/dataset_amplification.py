#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: 2026 - William Jose Moreno Reyes (CP/MBA)

import csv
import json
import re
from pathlib import Path

CSV_COLUMNS = [
    "pair_id",
    "system",
    "user",
    "assistant",
    "language",
    "topic",
    "level",
    "domain",
]

REQUIRED_BASE_COLUMNS = set(CSV_COLUMNS)
REQUIRED_SEED_COLUMNS = {
    "concept_es",
    "definition_es",
    "variants_es",
    "examples_es",
    "concept_en",
    "definition_en",
    "variants_en",
    "examples_en",
}

VALID_LANGUAGES = {"es", "en"}
VALID_LEVELS = {"basic", "intermediate", "advanced"}

SYSTEM_ES = (
    "Eres un experto en finanzas personales explicando clara y amigablemente "
    "conceptos basicos de finanzas personales"
)
SYSTEM_EN = (
    "You are an expert in personal finance explaining clearly and amicably "
    "basic concepts of personal finance"
)

# "templates" combines concept + definition.
TEMPLATES = {
    "ES": [
        "Cual es el concepto de {concept_es}?",
        "Podrias definir {concept_es} de forma sencilla?",
        "Como se define {concept_es} en finanzas personales?",
        "Que significa {concept_es} de manera practica?",
        "En terminos simples, que es {concept_es}?",
        "Me explicas {concept_es} como si fuera principiante?",
        "q es {concept_es}?",
        "qeu es el consecto de {concept_es}?",
        "q s {concept_es}?",
        "La neta no le entiendo a {concept_es}, me lo puedes explicar?",
        "Que onda vos, como va eso de {concept_es}?",
        "Parcero, me explica que es {concept_es}?",
    ],
    "EN": [
        "What is the concept of {concept_en}?",
        "Could you define {concept_en} in simple terms?",
        "How is {concept_en} defined in personal finance?",
        "What does {concept_en} mean in practical terms?",
        "In simple terms, what is {concept_en}?",
        "Can you explain {concept_en} like I am a beginner?",
        "wht is {concept_en}?",
        "what is teh concept of {concept_en}?",
        "what s {concept_en}?",
        "I honestly do not get {concept_en}, can you explain it?",
        "Hey, could you break down {concept_en} for me?",
        "Could you explain what {concept_en} is, please?",
    ],
}

# "variance" combines concept + variants.
VARIANCE = {
    "ES": [
        "Cual es la importancia de {concept_es}?",
        "Por que es importante {concept_es} en finanzas personales?",
        "Que papel cumple {concept_es} en una buena salud financiera?",
        "Para que sirve entender {concept_es}?",
        "Como ayuda {concept_es} a tomar mejores decisiones financieras?",
        "Por que conviene prestar atencion a {concept_es}?",
        "q tan importante es {concept_es}?",
        "xq es importante {concept_es}?",
        "Mae, por que importa {concept_es} en la vida real?",
    ],
    "EN": [
        "What is the importance of {concept_en}?",
        "Why is {concept_en} important in personal finance?",
        "What role does {concept_en} play in good financial health?",
        "Why is understanding {concept_en} useful?",
        "How does {concept_en} help with better financial decisions?",
        "Why should someone pay attention to {concept_en}?",
        "how important is {concept_en}?",
        "y is {concept_en} important?",
        "Why does {concept_en} matter in real life?",
    ],
}

# "examples" combines concept + examples.
EXAMPLES = {
    "ES": [
        "Cuales son algunos ejemplos de {concept_es}?",
        "Puedes darme ejemplos practicos de {concept_es}?",
        "Que casos reales ilustran {concept_es}?",
        "Como se ve {concept_es} en la vida diaria?",
        "Dame varios ejemplos claros de {concept_es}.",
        "q ejemplos hay de {concept_es}?",
        "me das ejemlos de {concept_es}?",
        "Causa, pasame ejemplos de {concept_es} en corto.",
    ],
    "EN": [
        "Which are some examples of {concept_en}?",
        "Can you share practical examples of {concept_en}?",
        "What real-world cases illustrate {concept_en}?",
        "How does {concept_en} appear in daily life?",
        "Give me several clear examples of {concept_en}.",
        "what examples of {concept_en} are there?",
        "giv me examples of {concept_en}",
        "Share short real examples of {concept_en}.",
    ],
}


def _normalize_base_row(raw_row: dict) -> dict:
    row = {k: (raw_row.get(k) or "").strip() for k in CSV_COLUMNS}
    row["language"] = row["language"].lower()
    row["topic"] = row["topic"].lower()
    row["level"] = row["level"].lower()
    row["domain"] = row["domain"].lower()
    return row


def _normalize_seed_row(raw_row: dict) -> dict:
    return {k: (raw_row.get(k) or "").strip() for k in REQUIRED_SEED_COLUMNS}


def _is_blank_base_row(row: dict) -> bool:
    return not any((row.get(col) or "").strip() for col in CSV_COLUMNS)


def validate_base_row(row: dict, row_number: int) -> None:
    for col in REQUIRED_BASE_COLUMNS:
        if not row.get(col):
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


def validate_seed_row(seed_row: dict, row_number: int) -> None:
    for col in REQUIRED_SEED_COLUMNS:
        if not seed_row.get(col):
            raise ValueError(f"Seed row {row_number}: Missing or empty field '{col}'.")


def read_base_dataset(base_csv_path: Path) -> list[dict]:
    if not base_csv_path.exists():
        raise FileNotFoundError(f"Input file '{base_csv_path}' does not exist.")

    rows: list[dict] = []
    with base_csv_path.open("r", encoding="utf-8", newline="") as csv_file:
        reader = csv.DictReader(csv_file)
        header_columns = set(reader.fieldnames or [])
        missing = REQUIRED_BASE_COLUMNS - header_columns
        if missing:
            raise ValueError(f"Missing required base columns: {sorted(missing)}")

        for row_number, raw_row in enumerate(reader, start=2):
            row = _normalize_base_row(raw_row)
            if _is_blank_base_row(row):
                continue
            validate_base_row(row, row_number)
            rows.append(row)

    return rows


def read_seed_dataset(seed_csv_path: Path) -> list[dict]:
    if not seed_csv_path.exists():
        raise FileNotFoundError(f"Seed file '{seed_csv_path}' does not exist.")

    rows: list[dict] = []
    with seed_csv_path.open("r", encoding="utf-8", newline="") as csv_file:
        reader = csv.DictReader(csv_file)
        header_columns = set(reader.fieldnames or [])
        missing = REQUIRED_SEED_COLUMNS - header_columns
        if missing:
            raise ValueError(f"Missing required seed columns: {sorted(missing)}")

        for row_number, raw_row in enumerate(reader, start=2):
            row = _normalize_seed_row(raw_row)
            validate_seed_row(row, row_number)
            rows.append(row)

    return rows


def _parse_pair_id(pair_id: str) -> int:
    clean = (pair_id or "").strip()
    return int(clean) if clean.isdigit() else 0


def _slugify_topic(text: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")
    return slug or "personal_finance"


def _signature(row: dict) -> tuple[str, str, str]:
    return (row["language"], row["user"], row["assistant"])


def _build_row(
    pair_id: str,
    language: str,
    topic: str,
    level: str,
    user: str,
    assistant: str,
) -> dict:
    return {
        "pair_id": pair_id,
        "system": SYSTEM_ES if language == "es" else SYSTEM_EN,
        "user": user.strip(),
        "assistant": assistant.strip(),
        "language": language,
        "topic": topic,
        "level": level,
        "domain": "personal_finance",
    }


def _append_semantic_pairs(
    dataset_rows: list[dict],
    seed_rows: list[dict],
    question_dict: dict,
    es_answer_field: str,
    en_answer_field: str,
    next_pair_number: int,
) -> tuple[int, int]:
    signatures = {_signature(row) for row in dataset_rows}
    added_pairs = 0

    for seed in seed_rows:
        topic = _slugify_topic(seed["concept_en"])
        level = "basic"

        for es_template, en_template in zip(question_dict["ES"], question_dict["EN"]):
            es_user = es_template.format(**seed)
            en_user = en_template.format(**seed)
            es_assistant = seed[es_answer_field]
            en_assistant = seed[en_answer_field]

            es_key = ("es", es_user, es_assistant)
            en_key = ("en", en_user, en_assistant)

            if es_key in signatures or en_key in signatures:
                continue

            next_pair_number += 1
            pair_id = f"{next_pair_number:06d}"

            es_row = _build_row(pair_id, "es", topic, level, es_user, es_assistant)
            en_row = _build_row(pair_id, "en", topic, level, en_user, en_assistant)

            dataset_rows.append(es_row)
            dataset_rows.append(en_row)
            signatures.add(es_key)
            signatures.add(en_key)
            added_pairs += 1

    return next_pair_number, added_pairs


def amplify_dataset(
    base_rows: list[dict], seed_rows: list[dict]
) -> tuple[list[dict], int]:
    dataset_rows = list(base_rows)
    next_pair_number = max(
        (_parse_pair_id(row["pair_id"]) for row in dataset_rows), default=0
    )
    total_added_pairs = 0

    next_pair_number, added = _append_semantic_pairs(
        dataset_rows,
        seed_rows,
        TEMPLATES,
        "definition_es",
        "definition_en",
        next_pair_number,
    )
    total_added_pairs += added

    next_pair_number, added = _append_semantic_pairs(
        dataset_rows,
        seed_rows,
        VARIANCE,
        "variants_es",
        "variants_en",
        next_pair_number,
    )
    total_added_pairs += added

    next_pair_number, added = _append_semantic_pairs(
        dataset_rows,
        seed_rows,
        EXAMPLES,
        "examples_es",
        "examples_en",
        next_pair_number,
    )
    total_added_pairs += added

    return dataset_rows, total_added_pairs


def write_full_jsonl(output_path: Path, rows: list[dict]) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as jsonl_file:
        for row in rows:
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


def write_messages_jsonl(output_path: Path, rows: list[dict]) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as jsonl_file:
        for row in rows:
            record = {
                "messages": [
                    {"role": "system", "content": row["system"]},
                    {"role": "user", "content": row["user"]},
                    {"role": "assistant", "content": row["assistant"]},
                ]
            }
            jsonl_file.write(json.dumps(record, ensure_ascii=False) + "\n")


def load_and_amplify(
    base_csv_path: Path, seed_csv_path: Path
) -> tuple[list[dict], int]:
    base_rows = read_base_dataset(base_csv_path)
    seed_rows = read_seed_dataset(seed_csv_path)
    return amplify_dataset(base_rows, seed_rows)

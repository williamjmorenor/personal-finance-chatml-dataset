#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: 2026 - William Jose Moreno Reyes (CP/MBA)

import csv
import json
import random
import re
from pathlib import Path
from typing import TypedDict

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

REQUIRED_BASE_COLUMNS = {
    "system",
    "user",
    "assistant",
    "language",
    "topic",
    "level",
    "domain",
}
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


class ResponsePatternConfig(TypedDict):
    original: str
    variants: list[str]


RESPONSE_PATTERN_BY_LANGUAGE: dict[str, ResponsePatternConfig] = {
    "es": {
        "original": "se define como",
        "variants": ["se refiere a", "puede describirse como"],
    },
    "en": {
        "original": "is defined as",
        "variants": ["refers to", "can be described as"],
    },
}

SYSTEM_ES = (
    "Eres un experto en finanzas personales explicando clara y amigablemente "
    "conceptos basicos de finanzas personales"
)
SYSTEM_EN = (
    "You are an expert in personal finance explaining clearly and amicably "
    "basic concepts of personal finance"
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
TEMPLATES_DIR = PROJECT_ROOT / "data" / "amplification_templates"

SEED_TEMPLATE_FILES = [
    TEMPLATES_DIR / "seed_definition_templates.json",
    TEMPLATES_DIR / "seed_variants_templates.json",
    TEMPLATES_DIR / "seed_examples_templates.json",
]

BASE_TEMPLATE_FILES = [
    TEMPLATES_DIR / "base_rephrase_templates.json",
    TEMPLATES_DIR / "base_noisy_templates.json",
]


def _load_json_template(template_path: Path) -> dict:
    if not template_path.exists():
        raise FileNotFoundError(f"Template file '{template_path}' does not exist.")

    with template_path.open("r", encoding="utf-8") as template_file:
        return json.load(template_file)


def _validate_seed_template(template: dict, template_path: Path) -> None:
    for language in ("es", "en"):
        section = template.get(language)
        if not isinstance(section, dict):
            raise ValueError(
                f"Template '{template_path}': Missing '{language}' section."
            )

        for field in ("campo_semilla", "campo_respuesta", "cadena_original"):
            value = section.get(field)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(
                    f"Template '{template_path}': Invalid '{language}.{field}'."
                )

        amplified = section.get("cadenas_amplificadas")
        if not isinstance(amplified, list) or not amplified:
            raise ValueError(
                f"Template '{template_path}': '{language}.cadenas_amplificadas' "
                "must be a non-empty list."
            )


def _validate_base_template(template: dict, template_path: Path) -> None:
    patterns = template.get("patrones_pareados")
    if not isinstance(patterns, list) or not patterns:
        raise ValueError(
            f"Template '{template_path}': 'patrones_pareados' must be a non-empty list."
        )

    for idx, pattern in enumerate(patterns, start=1):
        for language in ("es", "en"):
            section = (pattern or {}).get(language)
            if not isinstance(section, dict):
                raise ValueError(
                    f"Template '{template_path}': Pattern {idx} missing '{language}'."
                )

            for field in ("cadena_original", "regex_cadena_original"):
                value = section.get(field)
                if not isinstance(value, str) or not value.strip():
                    raise ValueError(
                        f"Template '{template_path}': Invalid '{language}.{field}' "
                        f"in pattern {idx}."
                    )

            amplified = section.get("cadenas_amplificadas")
            if not isinstance(amplified, list) or not amplified:
                raise ValueError(
                    f"Template '{template_path}': '{language}.cadenas_amplificadas' "
                    f"must be non-empty in pattern {idx}."
                )


def _load_seed_templates() -> list[dict]:
    templates: list[dict] = []
    for template_path in SEED_TEMPLATE_FILES:
        template = _load_json_template(template_path)
        _validate_seed_template(template, template_path)
        templates.append(template)
    return templates


def _load_base_templates() -> list[dict]:
    templates: list[dict] = []
    for template_path in BASE_TEMPLATE_FILES:
        template = _load_json_template(template_path)
        _validate_base_template(template, template_path)
        templates.append(template)
    return templates


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
    return not any((row.get(col) or "").strip() for col in REQUIRED_BASE_COLUMNS)


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


def _extract_question_concept(question: str, original_regex: str) -> str | None:
    question_clean = (question or "").strip()
    if not question_clean:
        return None

    matcher = re.compile(original_regex, re.IGNORECASE)
    match = matcher.match(question_clean)
    if not match:
        return None

    concept = (match.group("concept") or "").strip()
    return concept or None


def _collect_bilingual_pairs(rows: list[dict]) -> list[tuple[dict, dict]]:
    """Collect adjacent ES/EN rows that represent the same data pair."""
    pairs: list[tuple[dict, dict]] = []
    idx = 0

    while idx < len(rows) - 1:
        first = rows[idx]
        second = rows[idx + 1]

        same_group = (
            first["topic"] == second["topic"]
            and first["level"] == second["level"]
            and first["domain"] == second["domain"]
        )
        bilingual = {first["language"], second["language"]} == {"es", "en"}

        if same_group and bilingual:
            if first["language"] == "es":
                pairs.append((first, second))
            else:
                pairs.append((second, first))
            idx += 2
            continue

        idx += 1

    return pairs


def _append_seed_semantic_pairs(
    dataset_rows: list[dict],
    seed_rows: list[dict],
    template: dict,
    next_pair_number: int,
) -> tuple[int, int]:
    signatures = {_signature(row) for row in dataset_rows}
    added_pairs = 0

    es_section = template["es"]
    en_section = template["en"]
    es_templates = es_section["cadenas_amplificadas"]
    en_templates = en_section["cadenas_amplificadas"]

    if len(es_templates) != len(en_templates):
        template_name = template.get("nombre", "seed_template")
        raise ValueError(
            f"Template '{template_name}' has different ES/EN template counts."
        )

    es_answer_field = es_section["campo_respuesta"]
    en_answer_field = en_section["campo_respuesta"]

    for seed in seed_rows:
        topic = _slugify_topic(seed["concept_en"])
        level = "basic"

        for es_template, en_template in zip(es_templates, en_templates):
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


def _append_base_pattern_pairs(
    dataset_rows: list[dict],
    source_pairs: list[tuple[dict, dict]],
    template: dict,
    next_pair_number: int,
) -> tuple[int, int]:
    signatures = {_signature(row) for row in dataset_rows}
    added_pairs = 0

    for pattern in template["patrones_pareados"]:
        es_pattern = pattern["es"]
        en_pattern = pattern["en"]

        es_templates = es_pattern["cadenas_amplificadas"]
        en_templates = en_pattern["cadenas_amplificadas"]

        if len(es_templates) != len(en_templates):
            template_name = template.get("nombre", "base_template")
            raise ValueError(
                f"Template '{template_name}' has different ES/EN template counts."
            )

        es_regex = es_pattern["regex_cadena_original"]
        en_regex = en_pattern["regex_cadena_original"]

        for es_row, en_row in source_pairs:
            es_concept = _extract_question_concept(es_row["user"], es_regex)
            en_concept = _extract_question_concept(en_row["user"], en_regex)

            if not es_concept or not en_concept:
                continue

            for es_template, en_template in zip(es_templates, en_templates):
                es_user = es_template.format(concept=es_concept)
                en_user = en_template.format(concept=en_concept)
                es_assistant = es_row["assistant"]
                en_assistant = en_row["assistant"]

                es_key = ("es", es_user, es_assistant)
                en_key = ("en", en_user, en_assistant)

                if es_key in signatures or en_key in signatures:
                    continue

                next_pair_number += 1
                pair_id = f"{next_pair_number:06d}"

                new_es_row = _build_row(
                    pair_id,
                    "es",
                    es_row["topic"],
                    es_row["level"],
                    es_user,
                    es_assistant,
                )
                new_en_row = _build_row(
                    pair_id,
                    "en",
                    en_row["topic"],
                    en_row["level"],
                    en_user,
                    en_assistant,
                )

                # Preserve original metadata context from the base dataset pair.
                new_es_row["system"] = es_row["system"]
                new_en_row["system"] = en_row["system"]
                new_es_row["domain"] = es_row["domain"]
                new_en_row["domain"] = en_row["domain"]

                dataset_rows.append(new_es_row)
                dataset_rows.append(new_en_row)
                signatures.add(es_key)
                signatures.add(en_key)
                added_pairs += 1

    return next_pair_number, added_pairs


def _append_response_pattern_variants(dataset_rows: list[dict]) -> int:
    signatures = {_signature(row) for row in dataset_rows}
    source_rows = list(dataset_rows)
    added_rows = 0

    for row in source_rows:
        language = row["language"]
        language_pattern = RESPONSE_PATTERN_BY_LANGUAGE.get(language)
        if not language_pattern:
            continue

        original_pattern = language_pattern["original"]
        pattern_regex = re.compile(re.escape(original_pattern), re.IGNORECASE)
        assistant_text = row["assistant"]

        if not pattern_regex.search(assistant_text):
            continue

        for variant in language_pattern["variants"]:
            if random.choice([0, 1]) == 0:
                continue

            new_assistant = pattern_regex.sub(variant, assistant_text, count=1).strip()
            new_key = (language, row["user"], new_assistant)

            if new_key in signatures:
                continue

            # Keep all metadata equal to the source row; only assistant changes.
            new_row = dict(row)
            new_row["assistant"] = new_assistant

            dataset_rows.append(new_row)
            signatures.add(new_key)
            added_rows += 1

    return added_rows


def _deduplicate_rows(rows: list[dict]) -> list[dict]:
    deduped: list[dict] = []
    seen: set[tuple[str, str, str]] = set()

    for row in rows:
        row_key = _signature(row)
        if row_key in seen:
            continue
        seen.add(row_key)
        deduped.append(row)

    return deduped


def amplify_dataset(
    base_rows: list[dict], seed_rows: list[dict]
) -> tuple[list[dict], int]:
    dataset_rows = list(base_rows)
    source_pairs = _collect_bilingual_pairs(base_rows)
    seed_templates = _load_seed_templates()
    base_templates = _load_base_templates()

    next_pair_number = max(
        (_parse_pair_id(row["pair_id"]) for row in dataset_rows), default=0
    )
    total_added_pairs = 0

    for seed_template in seed_templates:
        next_pair_number, added = _append_seed_semantic_pairs(
            dataset_rows,
            seed_rows,
            seed_template,
            next_pair_number,
        )
        total_added_pairs += added

    for base_template in base_templates:
        next_pair_number, added = _append_base_pattern_pairs(
            dataset_rows,
            source_pairs,
            base_template,
            next_pair_number,
        )
        total_added_pairs += added

    # Response pattern amplification (assistant-side variants).
    total_added_pairs += _append_response_pattern_variants(dataset_rows)

    # Final dataset deduplication by (language, user, assistant).
    dataset_rows = _deduplicate_rows(dataset_rows)

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

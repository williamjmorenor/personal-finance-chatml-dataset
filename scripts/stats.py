#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: 2026 - William José Moreno Reyes (CP/MBA)

import csv
import json
import sys
from collections import Counter
from pathlib import Path
from statistics import mean, median


# ----------------------------
# DEFAULT PATHS (PROJECT ROOT)
# ----------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[1]

DEFAULT_CSV = PROJECT_ROOT / "data" / "raw" / "personal_finance_dataset.csv"
DEFAULT_JSONL = PROJECT_ROOT / "data" / "processed" / "personal_finance_chatml.jsonl"


# ----------------------------
# CONFIG
# ----------------------------

REQUIRED_COLUMNS = {"system", "user", "assistant", "language", "topic", "level"}
VALID_LANGUAGES = {"en", "es"}
VALID_LEVELS = {"basic", "intermediate", "advanced"}

# Very lightweight language sanity check (heuristic, not perfect)
EN_COMMON = {"the", "and", "is", "are", "to", "of", "in", "for", "with", "you", "your"}
ES_COMMON = {"el", "la", "y", "es", "son", "de", "en", "para", "con", "tu", "tus", "que"}


def percentile(values, p):
    """Compute percentile p (0-100) with linear interpolation."""
    if not values:
        return None
    xs = sorted(values)
    if len(xs) == 1:
        return xs[0]
    k = (len(xs) - 1) * (p / 100.0)
    f = int(k)
    c = min(f + 1, len(xs) - 1)
    if f == c:
        return xs[f]
    return xs[f] + (xs[c] - xs[f]) * (k - f)


def text_len(s: str) -> int:
    return len((s or "").strip())


def tokenize_lower(s: str):
    # simple tokenization: split on whitespace and strip punctuation-ish
    tokens = []
    for t in (s or "").lower().split():
        t = t.strip(".,;:!?()[]{}\"'“”‘’/\\|+-=*<>")
        if t:
            tokens.append(t)
    return tokens


def language_suspicion(language: str, text: str) -> bool:
    """
    Return True if text looks more like the other language than the declared one.
    Heuristic: count overlap with tiny stopword sets.
    """
    tokens = set(tokenize_lower(text))
    en_hits = len(tokens & EN_COMMON)
    es_hits = len(tokens & ES_COMMON)

    if language == "en":
        return es_hits > en_hits and (es_hits >= 2)
    if language == "es":
        return en_hits > es_hits and (en_hits >= 2)
    return False


def validate_csv_row(row, row_number):
    for col in REQUIRED_COLUMNS:
        if not row.get(col) or not row[col].strip():
            return f"Row {row_number}: Missing or empty '{col}'"

    if row["language"].strip() not in VALID_LANGUAGES:
        return f"Row {row_number}: Invalid language '{row['language']}'"

    if row["level"].strip() not in VALID_LEVELS:
        return f"Row {row_number}: Invalid level '{row['level']}'"

    return None


def print_counter(title, counter: Counter, top_n=20):
    print(f"\n{title}")
    print("-" * len(title))
    total = sum(counter.values()) or 1
    for key, count in counter.most_common(top_n):
        pct = (count / total) * 100
        print(f"{key:30} {count:8}  ({pct:5.1f}%)")
    if len(counter) > top_n:
        print(f"... ({len(counter) - top_n} more)")


def summarize_lengths(name, lengths):
    if not lengths:
        print(f"\n{name}: no data")
        return
    print(f"\n{name} length (characters)")
    print("-" * (len(name) + 22))
    print(f"count:   {len(lengths)}")
    print(f"mean:    {mean(lengths):.1f}")
    print(f"median:  {median(lengths):.1f}")
    p95 = percentile(lengths, 95)
    p99 = percentile(lengths, 99)
    print(f"p95:     {p95:.1f}")
    print(f"p99:     {p99:.1f}")
    print(f"min/max: {min(lengths)} / {max(lengths)}")


def stats_from_csv(csv_path: Path):
    if not csv_path.exists():
        print(f"Error: CSV not found at '{csv_path}'")
        sys.exit(1)

    total_rows = 0
    valid_rows = 0
    errors = []
    lang_counts = Counter()
    topic_counts = Counter()
    level_counts = Counter()

    system_lens = []
    user_lens = []
    assistant_lens = []

    suspicious_rows = []

    with csv_path.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        header = set(reader.fieldnames or [])
        missing = REQUIRED_COLUMNS - header
        if missing:
            print(f"Error: CSV missing required columns: {missing}")
            sys.exit(1)

        for row_number, row in enumerate(reader, start=2):
            total_rows += 1
            err = validate_csv_row(row, row_number)
            if err:
                errors.append(err)
                continue

            valid_rows += 1
            lang = row["language"].strip()
            topic = row["topic"].strip()
            level = row["level"].strip()

            lang_counts[lang] += 1
            topic_counts[topic] += 1
            level_counts[level] += 1

            system_lens.append(text_len(row["system"]))
            user_lens.append(text_len(row["user"]))
            assistant_lens.append(text_len(row["assistant"]))

            combined = f"{row['system']} {row['user']} {row['assistant']}"
            if language_suspicion(lang, combined):
                suspicious_rows.append((row_number, lang, topic, level))

    return {
        "total_rows": total_rows,
        "valid_rows": valid_rows,
        "errors": errors,
        "lang_counts": lang_counts,
        "topic_counts": topic_counts,
        "level_counts": level_counts,
        "system_lens": system_lens,
        "user_lens": user_lens,
        "assistant_lens": assistant_lens,
        "suspicious_rows": suspicious_rows,
    }


def stats_from_jsonl(jsonl_path: Path):
    if not jsonl_path.exists():
        return None

    total = 0
    parse_errors = []
    schema_errors = 0

    lang_counts = Counter()
    topic_counts = Counter()
    level_counts = Counter()

    assistant_lens = []

    with jsonl_path.open("r", encoding="utf-8") as f:
        for line_number, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            total += 1
            try:
                obj = json.loads(line)
            except Exception as e:
                parse_errors.append(f"Line {line_number}: JSON parse error: {e}")
                continue

            # Basic schema checks
            if "messages" not in obj or not isinstance(obj["messages"], list):
                schema_errors += 1
                continue
            if not all(isinstance(m, dict) and "role" in m and "content" in m for m in obj["messages"]):
                schema_errors += 1
                continue

            lang = (obj.get("language") or "").strip()
            topic = (obj.get("topic") or "").strip()
            level = (obj.get("level") or "").strip()

            if lang:
                lang_counts[lang] += 1
            if topic:
                topic_counts[topic] += 1
            if level:
                level_counts[level] += 1

            # measure assistant content length for quick sanity
            for m in obj["messages"]:
                if m.get("role") == "assistant":
                    assistant_lens.append(text_len(m.get("content", "")))
                    break

    return {
        "total_lines": total,
        "parse_errors": parse_errors,
        "schema_errors": schema_errors,
        "lang_counts": lang_counts,
        "topic_counts": topic_counts,
        "level_counts": level_counts,
        "assistant_lens": assistant_lens,
    }


def main():
    # Optional args:
    #   python scripts/stats.py
    #   python scripts/stats.py path/to.csv
    #   python scripts/stats.py path/to.csv path/to.jsonl
    csv_path = Path(sys.argv[1]) if len(sys.argv) >= 2 else DEFAULT_CSV
    jsonl_path = Path(sys.argv[2]) if len(sys.argv) >= 3 else DEFAULT_JSONL

    print("Dataset statistics")
    print("==================")
    print(f"CSV:   {csv_path}")
    print(f"JSONL: {jsonl_path} (if exists)")

    csv_stats = stats_from_csv(csv_path)

    print("\nCSV summary")
    print("----------")
    print(f"total rows: {csv_stats['total_rows']}")
    print(f"valid rows: {csv_stats['valid_rows']}")
    print(f"errors:     {len(csv_stats['errors'])}")

    if csv_stats["errors"]:
        print("\nFirst 10 CSV errors")
        print("-------------------")
        for e in csv_stats["errors"][:10]:
            print(e)
        if len(csv_stats["errors"]) > 10:
            print(f"... ({len(csv_stats['errors']) - 10} more)")

    print_counter("Language distribution (CSV)", csv_stats["lang_counts"], top_n=10)
    print_counter("Level distribution (CSV)", csv_stats["level_counts"], top_n=10)
    print_counter("Top topics (CSV)", csv_stats["topic_counts"], top_n=20)

    summarize_lengths("System", csv_stats["system_lens"])
    summarize_lengths("User", csv_stats["user_lens"])
    summarize_lengths("Assistant", csv_stats["assistant_lens"])

    print(f"\nLanguage suspicion flags (heuristic): {len(csv_stats['suspicious_rows'])}")
    if csv_stats["suspicious_rows"]:
        print("First 10 flagged rows: (row_number, language, topic, level)")
        for item in csv_stats["suspicious_rows"][:10]:
            print(item)
        if len(csv_stats["suspicious_rows"]) > 10:
            print(f"... ({len(csv_stats['suspicious_rows']) - 10} more)")

    jsonl_stats = stats_from_jsonl(jsonl_path)
    if jsonl_stats is None:
        print("\nJSONL summary")
        print("------------")
        print("JSONL file not found (run csv_to_jsonl.py first).")
        return

    print("\nJSONL summary")
    print("------------")
    print(f"total lines:    {jsonl_stats['total_lines']}")
    print(f"parse errors:   {len(jsonl_stats['parse_errors'])}")
    print(f"schema errors:  {jsonl_stats['schema_errors']}")

    if jsonl_stats["parse_errors"]:
        print("\nFirst 5 JSONL parse errors")
        print("-------------------------")
        for e in jsonl_stats["parse_errors"][:5]:
            print(e)

    print_counter("Language distribution (JSONL)", jsonl_stats["lang_counts"], top_n=10)
    print_counter("Level distribution (JSONL)", jsonl_stats["level_counts"], top_n=10)
    print_counter("Top topics (JSONL)", jsonl_stats["topic_counts"], top_n=20)

    summarize_lengths("Assistant (JSONL)", jsonl_stats["assistant_lens"])


if __name__ == "__main__":
    main()

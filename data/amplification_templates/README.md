# Amplification Templates Guide

This folder contains all editable semantic amplification templates used by `scripts/dataset_amplification.py`.

## Current Template Files
- `seed_definition_templates.json`
- `seed_variants_templates.json`
- `seed_examples_templates.json`
- `base_rephrase_templates.json`
- `base_noisy_templates.json`

## How Amplification Works
1. Seed amplification (`data/raw/data_sed.csv`):
- Reads 3 JSON template files (definition, variants, examples).
- For each seed row, creates bilingual ES/EN pairs from `cadenas_amplificadas`.

2. Base amplification (`data/raw/personal_finance_dataset.csv`):
- Reads 2 JSON template files (rephrase + noisy).
- For each ES/EN pair in the base CSV, detects if `user` matches `regex_cadena_original`.
- If matched, extracts `{concept}` and generates bilingual amplified prompts.

## Preferred JSON Structure

### Seed template structure
```json
{
  "nombre": "seed_definition_templates",
  "origen_csv": "data/raw/data_sed.csv",
  "es": {
    "campo_semilla": "concept_es",
    "campo_respuesta": "definition_es",
    "cadena_original": "Que es {concept_es}?",
    "cadenas_amplificadas": ["..."]
  },
  "en": {
    "campo_semilla": "concept_en",
    "campo_respuesta": "definition_en",
    "cadena_original": "What is {concept_en}?",
    "cadenas_amplificadas": ["..."]
  }
}
```

### Base template structure
```json
{
  "nombre": "base_rephrase_templates",
  "origen_csv": "data/raw/personal_finance_dataset.csv",
  "patrones_pareados": [
    {
      "es": {
        "cadena_original": "Que es {concept}?",
        "regex_cadena_original": "^\\s*[¿]?\\s*que\\s+(?:es|son)\\s+(?P<concept>.+?)\\?\\s*$",
        "cadenas_amplificadas": ["..."]
      },
      "en": {
        "cadena_original": "What is {concept}?",
        "regex_cadena_original": "^\\s*what\\s+(?:is|are)\\s+(?P<concept>.+?)\\?\\s*$",
        "cadenas_amplificadas": ["..."]
      }
    }
  ]
}
```

## Rules To Increase Amplification Effect Safely
- Keep ES and EN list lengths equal inside each template block.
- Add diverse phrasings (formal, colloquial, short, noisy) but keep intent equivalent.
- Keep placeholders consistent (`{concept_es}`, `{concept_en}`, `{concept}`).
- Do not mix answer fields. Use `definition_*` for concept-definition prompts.
- Do not mix answer fields. Use `variants_*` for importance/usefulness prompts.
- Do not mix answer fields. Use `examples_*` for example-seeking prompts.
- For base noisy templates, keep user text realistic but still understandable.
- Add new patterns as additional objects inside `patrones_pareados`.

## Suggested Strategy To Grow Amplification
1. Expand each existing `cadenas_amplificadas` list by +3 to +10 high-quality variants.
2. Add 1 to 3 new `patrones_pareados` for base CSV, for example: definition-like prompts, compare/contrast prompts, and typo/abbreviation prompts.
3. Keep pair balance: every ES new string should have one EN counterpart.
4. Regenerate datasets and validate line count growth.

## Validation Command
```bash
C:/code/personal-finance-chatml-dataset/.venv/Scripts/python.exe scripts/csv_to_jsonl.py data/raw/personal_finance_dataset.csv data/processed/personal_finance_chatml_full.jsonl
C:/code/personal-finance-chatml-dataset/.venv/Scripts/python.exe scripts/csv_to_messages.py data/raw/personal_finance_dataset.csv data/processed/personal_finance_chatml_messages.jsonl
```

## Quality Checklist Before Commit
- JSON is valid.
- ES and EN amplified list sizes match.
- Regex includes named group `(?P<concept>...)` for base templates.
- Generated `full` and `messages` outputs both updated correctly.
- No duplicated low-value variants added repeatedly.

# Raw Data Authoring Guide

This guide explains the preferred format for adding new rows so they benefit from semantic amplification.

## 1) `data_sed.csv` (seed source)

Required columns:
- `concept_es`
- `definition_es`
- `variants_es`
- `examples_es`
- `concept_en`
- `definition_en`
- `variants_en`
- `examples_en`

Preferred authoring rules:
- Add one bilingual concept per row.
- Keep ES and EN concepts equivalent in meaning.
- Write concise but complete definitions.
- Keep `variants_*` focused on importance/usefulness intent.
- Keep `examples_*` focused on concrete examples intent.

Example row:
```csv
concept_es,definition_es,variants_es,examples_es,concept_en,definition_en,variants_en,examples_en
fondo indexado,Un fondo indexado replica un indice de mercado para invertir con bajo costo.,Es util porque diversifica y reduce costos de gestion.,Ejemplo: un fondo que replica el S&P 500.,index fund,An index fund tracks a market index to invest at low cost.,It is useful because it diversifies and lowers management fees.,Example: a fund tracking the S&P 500.
```

How amplification uses this row:
- `seed_definition_templates.json` -> uses `definition_*`
- `seed_variants_templates.json` -> uses `variants_*`
- `seed_examples_templates.json` -> uses `examples_*`

## 2) `personal_finance_dataset.csv` (base source)

Required columns used by the pipeline:
- `system`
- `user`
- `assistant`
- `language`
- `topic`
- `level`
- `domain`

Important pairing rule:
- Add rows in adjacent bilingual pairs: ES row first, EN row second.
- Both rows should share same `topic`, `level`, and `domain`.
- Both rows should represent the same intent and concept.

Preferred `user` pattern to maximize amplification:
- ES: `Que es ...?` / `Que son ...?`
- EN: `What is ...?` / `What are ...?`

This is important because base amplification extracts `{concept}` from regex patterns in:
- `data/amplification_templates/base_rephrase_templates.json`
- `data/amplification_templates/base_noisy_templates.json`

Example pair:
```csv
,system,user,assistant,language,topic,level,domain,
,Eres un experto en finanzas personales explicando clara y amigablemente conceptos basicos de finanzas personales,Que es el interes compuesto?,Es el interes que se calcula sobre el capital inicial y sobre intereses acumulados.,es,interest,basic,personal_finance,
,You are an expert in personal finance explaining clearly and amicably basic concepts of personal finance,What is compound interest?,It is interest calculated on the initial principal and on accumulated interest.,en,interest,basic,personal_finance,
```

## Recommended Workflow For New Data
1. Add rows to `data/raw/data_sed.csv` and/or `data/raw/personal_finance_dataset.csv`.
2. If needed, add more amplification patterns in `data/amplification_templates/*.json`.
3. Regenerate processed outputs.
4. Validate size and sample records in both JSONL files.

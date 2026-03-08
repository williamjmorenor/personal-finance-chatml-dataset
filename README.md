# Bilingual Personal Finance ChatML Dataset (EN/ES)

## Overview
A professionally curated dataset for fine-tuning LLMs in personal finance.

## Structure
- ChatML format
- Fields: messages, language, topic, level

## Languages
- English
- Spanish

## Topics
- budgeting
- time_value_of_money
- rollforward
- debt_management
- investments
- etc.

## Format
Each row follows ChatML:

{
  "messages": [...],
  "language": "en|es",
  "topic": "...",
  "level": "basic|intermediate|advanced"
}

## Intended Use
- Supervised Fine-Tuning (SFT)
- Instruction tuning
- Financial domain adaptation

## Data Authoring And Amplification
- Raw data authoring guide: `data/raw/README.md`
- Amplification template guide: `data/amplification_templates/README.md`

These guides explain:
- how to add new rows to `data/raw/data_sed.csv` and `data/raw/personal_finance_dataset.csv`,
- how to increase semantic amplification effect,
- and how to keep bilingual ES/EN pairing compatible with the current pipeline.

## License
MIT

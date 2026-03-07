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

## License
MIT

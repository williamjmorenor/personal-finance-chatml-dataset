---
language:
- en
- es
license: mit
multilinguality: bilingual
size_categories:
- 1K<n<10K
task_categories:
- text-generation
- question-answering
task_ids:
- instruction-tuning
pretty_name: Bilingual Personal Finance ChatML Dataset (EN/ES)
---

# Bilingual Personal Finance ChatML Dataset (EN/ES)

## Dataset Description

This dataset is a professionally curated bilingual (English/Spanish) instruction dataset designed for fine-tuning large language models (LLMs) in the domain of personal finance.

It is structured in ChatML format and intended for supervised fine-tuning (SFT), domain adaptation, and financial instruction modeling.

The dataset is created and reviewed from an accounting perspective, ensuring conceptual precision and terminological consistency.

---

## Supported Languages

- English (`en`)
- Spanish (`es`)

Each record includes a `language` field for filtering and evaluation.

---

## Dataset Structure

Each entry follows the ChatML structure:

```json
{
  "messages": [
    {"role": "system", "content": "..."},
    {"role": "user", "content": "..."},
    {"role": "assistant", "content": "..."}
  ],
  "language": "en | es",
  "topic": "string",
  "level": "basic | intermediate | advanced"
}
```

## Fields

 - messages: ChatML conversation format.
 - language: Language of the interaction.
 - topic: Thematic classification.
 - level: Conceptual difficulty level.

## Topics Covered

 - Foundations of personal finance
 - Budgeting
 - Income and expense management
 - Time value of money
 - Compound interest
 - Debt management
 - Rollforward analysis
 - Net worth tracking
 - Savings strategies
 - Investment basics
 - Risk management
 - Retirement planning
 - Topics may expand in future versions.

## Annotation Process

All examples are manually curated and written to ensure:

 - Technical accounting accuracy
 - Terminological consistency
 - Pedagogical clarity
 - Neutral regulatory positioning

The dataset avoids country-specific legal advice unless explicitly indicated.

## Intended Uses

This dataset is intended for:

 - Supervised Fine-Tuning (SFT)
 - Instruction tuning
 - Financial domain specialization
 - Educational financial assistants
 - Research on bilingual financial NLP

## Out-of-Scope Uses

 - Automated financial advisory systems without human oversight
 - Regulatory or tax compliance automation
 - High-stakes investment decision systems

This dataset is educational and instructional in nature.

## Data Splits

If provided:
 - Train
 - Validation
 - Test

Otherwise, users may split according to their experimental needs.

## Bias, Risks, and Limitations

 - The dataset reflects a structured accounting perspective.
 - It does not include regional tax laws or jurisdiction-specific regulations by default.
 - It does not provide personalized financial advice.
 - It may not reflect emerging financial instruments or regulatory changes.

## Versioning

 - v1.0 — Initial bilingual release
  - Future versions may expand:
  - Advanced investment topics
  - Behavioral finance

## Citation

If you use this dataset in research, please cite:

```
@dataset{bilingual_personal_finance_chatml,
  author = {Your Name},
  title = {Bilingual Personal Finance ChatML Dataset (EN/ES)},
  year = {2026},
  publisher = {Hugging Face}
}
```

## License

MIT License (or chosen license).

## Contact

For questions, suggestions, or collaboration opportunities, please open an issue in the repository.
  "topic": "string",
  "level": "basic | intermediate | advanced"
}

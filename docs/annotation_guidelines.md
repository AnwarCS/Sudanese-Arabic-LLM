# Annotation Guidelines for Sudanese Arabic Project

## 1. Purpose
To ensure consistent, high-quality annotation of Sudanese Arabic text.

## 2. Key Points
- Identify pure Sudanese Arabic vs. Modern Standard Arabic.
- Note regional vocabulary where applicable (Khartoum, Darfur, East Sudan, North, South).
- Normalize spelling but respect Sudanese usage (e.g., شنُو؟ vs. ماذا؟).

## 3. Categories (Optional for later)
- Daily conversation
- Political speech
- Social media expressions
- Folk stories / proverbs
- Songs / poetry

## 4. Annotation Format and Label Schema

- Use JSONL or CSV format for annotated entries.
- Each annotated sample should include the following fields:
  - `text`: the raw Sudanese Arabic sentence
  - `dialect_tag`: e.g., `"SD_AR"` for Sudanese Arabic
  - `region`: e.g., `"Darfur"`, `"Khartoum"`, etc.
  - `category`: e.g., `"social_media"`, `"folk_story"` (optional)

```json
{
  "text": "شنو عملت؟",
  "dialect_tag": "SD_AR",
  "region": "Khartoum",
  "category": "daily_conversation"
}
```
---

**Note:** If unsure, tag the entry with [REVIEW] for a second annotator to check.

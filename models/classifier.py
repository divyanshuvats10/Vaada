import json
import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))


def classify_contradiction(statement_a: dict, statement_b: dict):
    prompt = f"""You are analyzing two statements made by the same Indian politician at different points in time.

Statement A:
Date: {statement_a['date']}
Context: {statement_a['video_title']}
Text: "{statement_a['text']}"

Statement B:
Date: {statement_b['date']}
Context: {statement_b['video_title']}
Text: "{statement_b['text']}"

Classify the relationship between these two statements.

Definitions:
- FLIP: Complete reversal of position
- CONTRADICTION: Incompatible factual claims
- UPDATE: Progress report on a past promise
- CONSISTENT: Same position expressed differently
- UNRELATED: Actually about different things

Return JSON only, no other text:
{{
  "classification": "FLIP|CONTRADICTION|UPDATE|CONSISTENT|UNRELATED",
  "confidence": 0.0,
  "explanation": "one sentence plain English explanation",
  "severity": "HIGH|MEDIUM|LOW",
  "topic": "specific topic these statements are about"
}}"""

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=300,
            temperature=0.1,
            response_format={"type": "json_object"}
        )

        raw = response.choices[0].message.content.strip()
        result = json.loads(raw)

        if result['classification'] in ('CONSISTENT', 'UNRELATED'):
            return None

        return result

    except Exception as e:
        print(f"Classifier error: {e}")
        return None
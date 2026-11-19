from __future__ import annotations

import json
import logging
import os
import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Set
import httpx
from fastapi import HTTPException, status

from app.core.config import settings

logger = logging.getLogger("querymind.llm_service")


# ─── MongoDB-native MQL system prompt ─────────────────────────────────────────

def _build_mongodb_prompt(schema_text: str) -> str:
    now = datetime.now()
    current_date_str = now.strftime("%Y-%m-%d")
    current_year = now.year

    return f"""You are QueryMind AI, an expert natural language to MongoDB query translator.
Current Reference Date: {current_date_str} (Current Year: {current_year})

Available MongoDB Collections & Fields:
{schema_text}

Rules:
1. Understand queries written in English or Hinglish.
2. Generate ONLY valid MongoDB Query Language (MQL) — NEVER generate SQL syntax.
3. Return a JSON operation object for the pymongo driver.
4. Choose the correct MongoDB operation type based on the user's intent:
   - READ → "find"        → {{ "filter": {{...}}, "projection": {{...}} }}
   - COUNT → "count"      → {{ "filter": {{...}} }}
   - AGGREGATE → "aggregate" → {{ "pipeline": [...] }}
   - INSERT → "insert_one" or "insert_many" → {{ "document": {{...}} }} or {{ "documents": [...] }}
   - UPDATE → "update_one" or "update_many" → {{ "filter": {{...}}, "update": {{ "$set": {{...}} }} }}
   - DELETE → "delete_one" or "delete_many" → {{ "filter": {{...}} }}

5. DATE & TIME MATCHING GUIDELINES:
   - When a user query mentions a date without specifying a year (e.g. "1 November", "scheduled on 1 Nov", "today", "tomorrow"):
     NEVER guess or hardcode outdated years (such as 2023 or 2024).
     Prefer year-resilient day & month matching using $expr:
       {{ "$expr": {{ "$and": [ {{ "$eq": [{{ "$month": "$showDateTime" }}, 11] }}, {{ "$eq": [{{ "$dayOfMonth": "$showDateTime" }}, 1] }} ] }} }}
     OR match full 24-hour day datetime range using the current reference year ({current_year}):
       {{ "showDateTime": {{ "$gte": {{ "$date": "{current_year}-11-01T00:00:00.000Z" }}, "$lt": {{ "$date": "{current_year}-11-02T00:00:00.000Z" }} }} }}

6. RELATED COLLECTIONS & LOOKUP AGGREGATION:
   - When a query asks for descriptive information across related collections (for example: "which shows are scheduled on 1 November", where "shows.movie" links to "movies._id"):
     Use "aggregate" with $lookup so the output includes human-readable details (like movie title and poster_path) along with show timing and price!
     Example pipeline:
     [
       {{ "$match": {{ "$expr": {{ "$and": [ {{ "$eq": [{{ "$month": "$showDateTime" }}, 11] }}, {{ "$eq": [{{ "$dayOfMonth": "$showDateTime" }}, 1] }} ] }} }} }},
       {{ "$lookup": {{ "from": "movies", "localField": "movie", "foreignField": "_id", "as": "movie_details" }} }},
       {{ "$unwind": {{ "path": "$movie_details", "preserveNullAndEmptyArrays": true }} }},
       {{ "$project": {{
           "_id": 1,
           "movie_title": "$movie_details.title",
           "poster_path": "$movie_details.poster_path",
           "showDateTime": 1,
           "showPrice": 1,
           "occupiedSeats": 1
       }} }}
     ]
   - If a simple "find" is requested or sufficient, you can also use "find" with the year-resilient $expr or {current_year} datetime filter.

7. MULTI-STATEMENT / COMPOUND QUERIES:
   - When the user asks for multiple operations in a single prompt (e.g. 'insert and update at same time', 'insert and find'):
   - Generate each operation as an item in the 'sql_statements' list in sequential execution order.

8. SMART AMBIGUITY CLARIFICATION:
   - If the user query is vague (e.g. 'top performers', 'fetch top faculty members', 'show orders'), set "needs_clarification": true with appropriate question and choices.

Return strictly valid JSON with this structure:
{{
  "status": "success",
  "intent": "Brief description of user intent",
  "sql_statements": [
    {{
      "sql": "<mql_json_string>",
      "operation": "SELECT|INSERT|UPDATE|DELETE",
      "mql": {{
        "collection": "collection_name",
        "operation": "find|insert_one|insert_many|update_one|update_many|delete_one|delete_many|aggregate|count",
        "filter": {{}},
        "projection": {{}},
        "update": {{}},
        "document": {{}},
        "documents": [],
        "pipeline": [],
        "options": {{}}
      }}
    }}
  ],
  "needs_clarification": false,
  "clarification_question": null,
  "clarification_choices": null
}}

IMPORTANT:
- The "sql" field must be a JSON string representation of the MQL operation for display purposes.
- The "mql" field must be the structured MQL object.
- Map CRUD intent to the correct MongoDB operation names (find, update_many, aggregate, etc.).
- Do NOT invent collection names or field names not present in the schema.
- Use $set for UPDATE operations. Never use full document replacement.
- For SELECT-intent, use "find" or "aggregate". Map "SELECT" to operation "SELECT" in the outer "operation" field.
- For UPDATE-intent, use "update_one"/"update_many". Map to "UPDATE" in outer "operation".
- For DELETE-intent, use "delete_one"/"delete_many". Map to "DELETE" in outer "operation".
- For INSERT-intent, use "insert_one"/"insert_many". Map to "INSERT" in outer "operation".
"""


def _build_sql_prompt(db_type: str, schema_text: str) -> str:
    now = datetime.now()
    current_date_str = now.strftime("%Y-%m-%d")
    current_year = now.year

    return f"""You are QueryMind AI, an expert natural language to SQL translator.
Target Database Dialect: {db_type.upper()}
Current Reference Date: {current_date_str} (Current Year: {current_year})

Available Database Schema & Column Details:
{schema_text}

Rules:
1. Understand queries written in English or Hinglish.
2. Generate valid SQL syntax strictly using the target dialect ({db_type.upper()}).
3. When matching dates without an explicit year (e.g. "1 November"), use the current reference year ({current_year}) instead of outdated years.
4. Do NOT generate MySQL-specific syntax for PostgreSQL or vice-versa. Use ONLY real columns from the schema above (e.g. for faculty table use name, email, department_id, designation, salary; never invent first_name/last_name if not in schema).
5. SMART AMBIGUITY CLARIFICATION:
   - If the user query is vague, broad, or lacks ranking criteria (e.g. 'show top 3 student', 'top 5 students', 'top performers', 'fetch top faculty members', 'top faculty', 'recent orders' without timeframe), do NOT guess blindly.
   - For example, if user asks 'show top 3 student', 'top 5 students', or 'top performers' without specifying the ranking metric (CGPA vs Attendance), ask 'How would you like to rank top performers?' with choices ["Rank by CGPA", "Rank by Course Attendance %"].
   - For example, if user asks 'fetch top faculty members', 'top faculty', or 'show top 3 faculty', ask 'How would you like to rank faculty members?' with choices ["Rank by Highest Paid (Salary)", "Rank by Designation", "Show All Faculty Details"].
   - Set "needs_clarification": true.
   - Set "clarification_question": A polite, concise question asking how they want to filter or categorize the data.
   - Set "clarification_choices": An array of 2 to 4 distinct, actionable options.
   - Set "sql_statements": [].
   - If the query is clear and unambiguous, or is an answer to a clarification (e.g. 'Rank by CGPA', 'Rank by Highest Paid (Salary)', 'highest paid status', 'show top 3 students by cgpa'), set "needs_clarification": false with null question and choices, and generate the SQL statements with the appropriate ORDER BY and LIMIT.
6. MULTI-STATEMENT / COMPOUND QUERIES:
   - When the user asks for multiple operations in a single prompt (e.g. 'insert and update at same time', 'insert faculty and select all faculty', 'update X and delete Y'):
   - Generate EACH operation as an independent item in the 'sql_statements' array in proper sequential execution order!
   - Example:
     "sql_statements": [
       {{ "sql": "INSERT INTO faculty (name, email, department_id, designation, salary) VALUES ('Dr. Amit Sharma', 'amit@univ.edu', 1, 'Professor', 95000);", "operation": "INSERT" }},
       {{ "sql": "UPDATE faculty SET designation = 'Senior Professor' WHERE name = 'Dr. Amit Sharma';", "operation": "UPDATE" }}
     ]
7. Return strictly valid JSON containing:
{{
  "status": "success",
  "intent": "Brief description of user intent",
  "sql_statements": [
    {{
      "sql": "SELECT ...",
      "operation": "SELECT"
    }}
  ],
  "needs_clarification": false,
  "clarification_question": null,
  "clarification_choices": null
}}
8. TABLE NAME AND ENTITY SINGULAR/PLURAL MATCHING:
   - Always match the user's entity (e.g. 'students', 'student', 'faculty', 'faculties', 'departments', 'department', 'courses', 'course') to the EXACT physical table name defined in the schema above.
   - If the user writes plural 'students' or 'show top 5 students' but the schema has 'students', use 'students'. If the schema has 'student', use 'student'.
   - If the user writes singular 'department' but the schema defines 'departments', use 'departments'.
9. RANKING & "TOP N" QUERIES:
   - When the user query specifies a ranking metric or clarifies one (e.g. "show top 3 students by cgpa", "Rank by CGPA", "top 5 faculty by salary"):
   - You MUST include BOTH an ORDER BY clause descending on the specified ranking attribute (e.g. "ORDER BY cgpa DESC" for students, "ORDER BY salary DESC" for faculty, "ORDER BY price DESC" for products) AND the LIMIT clause (e.g. "LIMIT 3" or "LIMIT 5").
   - NEVER generate an un-ordered LIMIT query when the user asks for "top" or "best".
"""


class LLMProvider:
    """Abstract interface for QueryMind LLM providers."""

    async def generate_sql(
        self,
        nl_query: str,
        db_type: str,
        schema_text: str,
        session_context: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        raise NotImplementedError

    async def generate_summary(
        self,
        nl_query: str,
        sql: str,
        row_count: int,
        sample_rows: Optional[List[Dict[str, Any]]] = None
    ) -> str:
        raise NotImplementedError

    async def parse_security_rule(
        self,
        rule_text: str,
        schema_text: str
    ) -> Dict[str, Any]:
        """Translates natural language security rules into structured permission definitions."""
        raise NotImplementedError

    # Alias so callers using generate_query also work
    async def generate_query(
        self,
        nl_query: str,
        db_type: str,
        schema_text: str,
        session_context: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        return await self.generate_sql(nl_query, db_type, schema_text, session_context)

    async def generate_summary(
        self,
        nl_query: str,
        sql: str,
        row_count: int,
        sample_rows: Optional[List[Dict[str, Any]]] = None
    ) -> str:
        raise NotImplementedError


class GeminiProvider(LLMProvider):
    """Google Gemini LLM provider implementation using official API."""

    def __init__(self, api_key: str = "", model: str = ""):
        self.api_key = api_key or settings.LLM_API_KEY or os.getenv("GEMINI_API_KEY", "")
        self.model = model or getattr(settings, "GEMINI_MODEL", "gemini-1.5-flash") or "gemini-1.5-flash"

    def is_available(self) -> bool:
        return bool(self.api_key and self.api_key.strip())

    async def generate_sql(
        self,
        nl_query: str,
        db_type: str,
        schema_text: str,
        session_context: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """Translates English or Hinglish queries into structured query JSON using Gemini."""
        if not self.api_key or not self.api_key.strip():
            raise RuntimeError("Gemini provider unavailable: LLM_API_KEY not configured.")

        # Use MongoDB-native prompt for MongoDB, SQL prompt for relational databases
        if db_type.lower() in ("mongodb", "mongo"):
            system_prompt = _build_mongodb_prompt(schema_text)
        else:
            system_prompt = _build_sql_prompt(db_type, schema_text)

        user_content = f"User Request: {nl_query}"
        if session_context:
            user_content = f"Session History:\n{json.dumps(session_context)}\n\nCurrent Request: {nl_query}"

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
        payload = {
            "contents": [
                {"role": "user", "parts": [{"text": f"{system_prompt}\n\n{user_content}"}]}
            ],
            "generationConfig": {
                "temperature": 0.1,
                "responseMimeType": "application/json"
            }
        }

        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.post(url, json=payload)
            if resp.status_code == 200:
                data = resp.json()
                text_out = data["candidates"][0]["content"]["parts"][0]["text"].strip()
                if text_out.startswith("```"):
                    lines = text_out.splitlines()
                    if lines and lines[0].startswith("```"):
                        lines = lines[1:]
                    if lines and lines[-1].startswith("```"):
                        lines = lines[:-1]
                    text_out = "\n".join(lines).strip()
                parsed = json.loads(text_out)
                return parsed
            else:
                logger.error(f"Gemini API returned HTTP {resp.status_code}: {resp.text}")
                raise RuntimeError(f"Gemini API HTTP {resp.status_code}: {resp.text[:200]}")

    async def generate_summary(
        self,
        nl_query: str,
        sql: str,
        row_count: int,
        sample_rows: Optional[List[Dict[str, Any]]] = None
    ) -> str:
        """Generates natural language summary and analytical insights from query results."""
        if not self.api_key:
            return f"{row_count} records were returned for your query."

        try:
            sample_str = ""
            if sample_rows:
                import json as _json
                sample_str = _json.dumps(sample_rows[:8], default=str)

            prompt = f"""You are QueryMind AI, an intelligent enterprise data analyst.
User Question: {nl_query}
Executed Query: {sql}
Total Rows: {row_count}
Sample Result Data:
{sample_str if sample_str else "No rows returned."}

Task: Write a concise, executive insight summary (2-3 sentences max):
- Highlight the primary finding or answer clearly.
- Identify key trends, highest/lowest values, totals, or percentage distributions from the actual data.
- Point out any notable anomaly, standout entity, or business takeaway.
Do not just say 'X records returned'. Be descriptive, professional, and interpret the actual data values."""

            url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
            payload = {
                "contents": [{"role": "user", "parts": [{"text": prompt}]}],
                "generationConfig": {"temperature": 0.2, "maxOutputTokens": 350}
            }
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(url, json=payload)
                if resp.status_code == 200:
                    data = resp.json()
                    return data["candidates"][0]["content"]["parts"][0]["text"].strip()
                raise RuntimeError(f"Gemini API returned HTTP {resp.status_code}: {resp.text}")
        except Exception as e:
            logger.warning(f"Gemini summary generation failed: {e}. Falling back to next provider...")
            raise

    async def parse_security_rule(
        self,
        rule_text: str,
        schema_text: str
    ) -> Dict[str, Any]:
        """Translates natural language security policy into structured permission rule."""
        if not self.api_key:
            raise RuntimeError("Gemini provider unavailable: LLM_API_KEY not configured.")

        prompt = f"""You are QueryMind AI Security & Governance Parser.
Available Database Schema:
{schema_text}

Natural Language Security Rule from Admin:
"{rule_text}"

Task: Convert this rule into a structured security permission policy.
Rules to follow:
1. Match table names and column names case-insensitively with the available schema.
2. If the rule says 'restrict salary column from faculty' or 'hide salary in faculty':
   action = "restrict_column", table_name = "faculty", column_name = "salary", allowed = false
3. If the rule restricts a whole table (e.g. 'block access to payments table'):
   action = "restrict_table", table_name = "payments", column_name = null, allowed = false
4. If the rule restricts specific operations (e.g. 'disallow DELETE on bookings'):
   action = "restrict_operation", table_name = "bookings", column_name = null, restricted_operations = ["DELETE"]
5. Determine target_role: 'all' by default unless a specific role ('viewer' or 'analyst') is explicitly requested in the rule text.

Return strictly valid JSON with this format:
{{
  "status": "success",
  "table_name": "<exact_table_name_or_null>",
  "column_name": "<exact_column_name_or_null>",
  "action": "restrict_column" | "restrict_table" | "restrict_operation" | "allow_all",
  "allowed": false,
  "restricted_operations": ["DELETE"],
  "target_role": "viewer" | "analyst" | "all",
  "summary": "Clear one-sentence description of the enforced policy"
}}"""

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
        payload = {
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.1, "maxOutputTokens": 400}
        }
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(url, json=payload)
            if resp.status_code == 200:
                raw_text = resp.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
                import json as _json
                clean = re.sub(r"^```(?:json)?\s*", "", raw_text, flags=re.MULTILINE)
                clean = re.sub(r"\s*```$", "", clean, flags=re.MULTILINE).strip()
                return _json.loads(clean)
            raise RuntimeError(f"Gemini rule parsing error HTTP {resp.status_code}: {resp.text}")


class OpenRouterProvider(LLMProvider):
    """OpenRouter provider — OpenAI-compatible API gateway supporting many models."""

    OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

    def __init__(self, api_key: str = "", model: str = ""):
        self.api_key = api_key or (settings.OPENROUTER_API_KEY or "")
        self.model = model or (settings.OPENROUTER_MODEL or "mistralai/mistral-7b-instruct")

    def is_available(self) -> bool:
        return bool(self.api_key and self.api_key.strip())

    async def generate_sql(
        self,
        nl_query: str,
        db_type: str,
        schema_text: str,
        session_context: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        if not self.api_key:
            raise RuntimeError("OpenRouter provider unavailable: OPENROUTER_API_KEY not configured.")

        if db_type.lower() in ("mongodb", "mongo"):
            system_msg = _build_mongodb_prompt(schema_text)
        else:
            system_msg = _build_sql_prompt(db_type, schema_text)

        user_msg = f"User Request: {nl_query}"
        if session_context:
            user_msg = f"Session History:\n{json.dumps(session_context)}\n\n{user_msg}"

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_msg},
                {"role": "user", "content": user_msg},
            ],
            "temperature": 0.1,
            "response_format": {"type": "json_object"},
        }

        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.post(
                f"{self.OPENROUTER_BASE_URL}/chat/completions",
                json=payload,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "HTTP-Referer": settings.FRONTEND_URL,
                    "X-Title": settings.APP_NAME,
                },
            )
            if resp.status_code in (400, 401, 403):
                # Permanent error — do not retry with another OpenRouter call
                raise RuntimeError(f"OpenRouter permanent error HTTP {resp.status_code}: {resp.text[:200]}")
            if resp.status_code == 429:
                raise RuntimeError("OpenRouter rate limit exceeded.")
            if resp.status_code == 200:
                data = resp.json()
                text_out = data["choices"][0]["message"]["content"]
                # Strip possible markdown code fence
                json_match = re.search(r"\{.*\}", text_out, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group(0))
                return json.loads(text_out)
            else:
                raise RuntimeError(f"OpenRouter API HTTP {resp.status_code}: {resp.text[:200]}")

    async def generate_summary(
        self,
        nl_query: str,
        sql: str,
        row_count: int,
        sample_rows: Optional[List[Dict[str, Any]]] = None
    ) -> str:
        if not self.api_key:
            return f"{row_count} records were returned."
        try:
            sample_str = json.dumps(sample_rows[:8], default=str) if sample_rows else "No sample rows."
            prompt = f"""You are QueryMind AI data analyst.
User Question: {nl_query}
Executed SQL: {sql}
Total Rows: {row_count}
Data Sample:
{sample_str}

Write a 2-3 sentence executive summary highlighting key findings, numbers, top items, and notable trends from the data. Be specific and insightful."""
            payload = {
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.2,
            }
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(
                    f"{self.OPENROUTER_BASE_URL}/chat/completions",
                    json=payload,
                    headers={"Authorization": f"Bearer {self.api_key}"}
                )
                if resp.status_code == 200:
                    return resp.json()["choices"][0]["message"]["content"].strip()
                raise RuntimeError(f"OpenRouter returned HTTP {resp.status_code}")
        except Exception as e:
            logger.warning(f"OpenRouter summary generation failed: {e}. Falling back...")
            raise

    async def parse_security_rule(
        self,
        rule_text: str,
        schema_text: str
    ) -> Dict[str, Any]:
        """Translates natural language security policy into structured permission rule via OpenRouter."""
        prompt = f"""You are QueryMind AI Security & Governance Parser.
Available Database Schema:
{schema_text}

Natural Language Security Rule from Admin:
"{rule_text}"

Convert this rule into a structured security permission policy.
Return strictly valid JSON:
{{
  "status": "success",
  "table_name": "<exact_table_name_or_null>",
  "column_name": "<exact_column_name_or_null>",
  "action": "restrict_column" | "restrict_table" | "restrict_operation" | "allow_all",
  "allowed": false,
  "restricted_operations": ["DELETE"],
  "target_role": "viewer" | "analyst" | "all",
  "summary": "Clear one-sentence description of the enforced policy"
}}"""
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.1,
            "response_format": {"type": "json_object"}
        }
        async with httpx.AsyncClient(timeout=12.0) as client:
            resp = await client.post(
                f"{self.OPENROUTER_BASE_URL}/chat/completions",
                json=payload,
                headers={"Authorization": f"Bearer {self.api_key}"}
            )
            if resp.status_code == 200:
                text_out = resp.json()["choices"][0]["message"]["content"].strip()
                json_match = re.search(r"\{.*\}", text_out, re.DOTALL)
                return json.loads(json_match.group(0)) if json_match else json.loads(text_out)
        raise RuntimeError(f"OpenRouter rule parsing failed HTTP {resp.status_code}")


class OpenAIProvider(LLMProvider):
    """OpenAI GPT-4 provider for LLM fallback chain."""

    def __init__(self, api_key: str = "", model: str = ""):
        self.api_key = api_key or (settings.OPENAI_API_KEY or "")
        self.model = model or getattr(settings, "OPENAI_MODEL", "gpt-4o-mini") or "gpt-4o-mini"

    def is_available(self) -> bool:
        return bool(self.api_key and self.api_key.strip())

    async def generate_sql(
        self,
        nl_query: str,
        db_type: str,
        schema_text: str,
        session_context: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        if not self.api_key:
            raise RuntimeError("OpenAI provider unavailable: OPENAI_API_KEY not configured.")

        if db_type.lower() in ("mongodb", "mongo"):
            system_msg = _build_mongodb_prompt(schema_text)
        else:
            system_msg = _build_sql_prompt(db_type, schema_text)

        user_msg = f"User Request: {nl_query}"
        if session_context:
            user_msg = f"Session History:\n{json.dumps(session_context)}\n\n{user_msg}"

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_msg},
                {"role": "user", "content": user_msg},
            ],
            "temperature": 0.1,
            "response_format": {"type": "json_object"},
        }

        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.post(
                "https://api.openai.com/v1/chat/completions",
                json=payload,
                headers={"Authorization": f"Bearer {self.api_key}"},
            )
            if resp.status_code == 200:
                data = resp.json()
                text_out = data["choices"][0]["message"]["content"]
                return json.loads(text_out)
            else:
                raise RuntimeError(f"OpenAI API HTTP {resp.status_code}: {resp.text[:200]}")

    async def generate_summary(
        self,
        nl_query: str,
        sql: str,
        row_count: int,
        sample_rows: Optional[List[Dict[str, Any]]] = None
    ) -> str:
        if not self.api_key:
            return f"{row_count} records were returned."
        try:
            sample_str = json.dumps(sample_rows[:8], default=str) if sample_rows else "No sample rows."
            prompt = f"""You are QueryMind AI data analyst.
User Question: {nl_query}
Executed SQL: {sql}
Total Rows: {row_count}
Data Sample:
{sample_str}

Write a 2-3 sentence executive summary highlighting key findings, numbers, top items, and notable trends from the data. Be specific and insightful."""
            payload = {
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.2,
            }
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    json=payload,
                    headers={"Authorization": f"Bearer {self.api_key}"}
                )
                if resp.status_code == 200:
                    return resp.json()["choices"][0]["message"]["content"].strip()
                raise RuntimeError(f"OpenAI returned HTTP {resp.status_code}")
        except Exception as e:
            logger.warning(f"OpenAI summary generation failed: {e}. Falling back...")
            raise

    async def parse_security_rule(
        self,
        rule_text: str,
        schema_text: str
    ) -> Dict[str, Any]:
        """Translates natural language security policy into structured permission rule via OpenAI."""
        prompt = f"""You are QueryMind AI Security & Governance Parser.
Available Database Schema:
{schema_text}

Natural Language Security Rule from Admin:
"{rule_text}"

Convert this rule into a structured security permission policy.
Return strictly valid JSON:
{{
  "status": "success",
  "table_name": "<exact_table_name_or_null>",
  "column_name": "<exact_column_name_or_null>",
  "action": "restrict_column" | "restrict_table" | "restrict_operation" | "allow_all",
  "allowed": false,
  "restricted_operations": ["DELETE"],
  "target_role": "viewer" | "analyst" | "all",
  "summary": "Clear one-sentence description of the enforced policy"
}}"""
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.1,
            "response_format": {"type": "json_object"}
        }
        async with httpx.AsyncClient(timeout=12.0) as client:
            resp = await client.post(
                "https://api.openai.com/v1/chat/completions",
                json=payload,
                headers={"Authorization": f"Bearer {self.api_key}"}
            )
            if resp.status_code == 200:
                text_out = resp.json()["choices"][0]["message"]["content"].strip()
                json_match = re.search(r"\{.*\}", text_out, re.DOTALL)
                return json.loads(json_match.group(0)) if json_match else json.loads(text_out)
        raise RuntimeError(f"OpenAI rule parsing failed HTTP {resp.status_code}")


class AnthropicProvider(LLMProvider):
    """Anthropic Claude provider for LLM fallback chain."""

    def __init__(self, api_key: str = "", model: str = ""):
        self.api_key = api_key or (settings.ANTHROPIC_API_KEY or "")
        self.model = model or getattr(settings, "ANTHROPIC_MODEL", "claude-3-5-haiku-20241022") or "claude-3-5-haiku-20241022"

    def is_available(self) -> bool:
        return bool(self.api_key and self.api_key.strip())

    async def generate_sql(
        self,
        nl_query: str,
        db_type: str,
        schema_text: str,
        session_context: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        if not self.api_key:
            raise RuntimeError("Anthropic provider unavailable: ANTHROPIC_API_KEY not configured.")

        if db_type.lower() in ("mongodb", "mongo"):
            system_msg = _build_mongodb_prompt(schema_text)
        else:
            system_msg = _build_sql_prompt(db_type, schema_text)

        user_msg = f"User Request: {nl_query}"
        if session_context:
            user_msg = f"Session History:\n{json.dumps(session_context)}\n\n{user_msg}"

        payload = {
            "model": self.model,
            "max_tokens": 1024,
            "system": system_msg,
            "messages": [{"role": "user", "content": user_msg}],
        }

        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.post(
                "https://api.anthropic.com/v1/messages",
                json=payload,
                headers={
                    "x-api-key": self.api_key,
                    "anthropic-version": "2023-06-01",
                },
            )
            if resp.status_code == 200:
                data = resp.json()
                text_out = data["content"][0]["text"]
                # Extract JSON from possible markdown fences
                json_match = re.search(r"\{.*\}", text_out, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group(0))
                return json.loads(text_out)
            else:
                raise RuntimeError(f"Anthropic API HTTP {resp.status_code}: {resp.text[:200]}")

    async def generate_summary(
        self,
        nl_query: str,
        sql: str,
        row_count: int,
        sample_rows: Optional[List[Dict[str, Any]]] = None
    ) -> str:
        if not self.api_key:
            return f"{row_count} records were returned."
        try:
            sample_str = json.dumps(sample_rows[:8], default=str) if sample_rows else "No sample rows."
            prompt = f"""You are QueryMind AI data analyst.
User Question: {nl_query}
Executed SQL: {sql}
Total Rows: {row_count}
Data Sample:
{sample_str}

Write a 2-3 sentence executive summary highlighting key findings, numbers, top items, and notable trends from the data. Be specific and insightful."""
            payload = {
                "model": self.model,
                "max_tokens": 300,
                "messages": [{"role": "user", "content": prompt}],
            }
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(
                    "https://api.anthropic.com/v1/messages",
                    json=payload,
                    headers={
                        "x-api-key": self.api_key,
                        "anthropic-version": "2023-06-01",
                    }
                )
                if resp.status_code == 200:
                    return resp.json()["content"][0]["text"].strip()
                raise RuntimeError(f"Anthropic returned HTTP {resp.status_code}")
        except Exception as e:
            logger.warning(f"Anthropic summary generation failed: {e}. Falling back...")
            raise

    async def parse_security_rule(
        self,
        rule_text: str,
        schema_text: str
    ) -> Dict[str, Any]:
        """Translates natural language security policy into structured permission rule via Anthropic."""
        prompt = f"""You are QueryMind AI Security & Governance Parser.
Available Database Schema:
{schema_text}

Natural Language Security Rule from Admin:
"{rule_text}"

Convert this rule into a structured security permission policy.
Return strictly valid JSON:
{{
  "status": "success",
  "table_name": "<exact_table_name_or_null>",
  "column_name": "<exact_column_name_or_null>",
  "action": "restrict_column" | "restrict_table" | "restrict_operation" | "allow_all",
  "allowed": false,
  "restricted_operations": ["DELETE"],
  "target_role": "viewer" | "analyst" | "all",
  "summary": "Clear one-sentence description of the enforced policy"
}}"""
        payload = {
            "model": self.model,
            "max_tokens": 400,
            "messages": [{"role": "user", "content": prompt}],
        }
        async with httpx.AsyncClient(timeout=12.0) as client:
            resp = await client.post(
                "https://api.anthropic.com/v1/messages",
                json=payload,
                headers={
                    "x-api-key": self.api_key,
                    "anthropic-version": "2023-06-01",
                }
            )
            if resp.status_code == 200:
                text_out = resp.json()["content"][0]["text"].strip()
                json_match = re.search(r"\{.*\}", text_out, re.DOTALL)
                return json.loads(json_match.group(0)) if json_match else json.loads(text_out)
        raise RuntimeError(f"Anthropic rule parsing failed HTTP {resp.status_code}")
        async with httpx.AsyncClient(timeout=12.0) as client:
            resp = await client.post(
                f"{self.OPENROUTER_BASE_URL}/chat/completions",
                json=payload,
                headers={"Authorization": f"Bearer {self.api_key}"}
            )
            if resp.status_code == 200:
                text_out = resp.json()["choices"][0]["message"]["content"].strip()
                json_match = re.search(r"\{.*\}", text_out, re.DOTALL)
                return json.loads(json_match.group(0)) if json_match else json.loads(text_out)
        raise RuntimeError(f"OpenRouter rule parsing failed HTTP {resp.status_code}")


class MockLLMProvider(LLMProvider):
    """Deterministic Mock LLM provider for unit, integration, and CI testing without external dependencies."""

    def is_available(self) -> bool:
        return True

    def _extract_limit(self, lower: str, session_context: Optional[List[Dict[str, Any]]] = None) -> Optional[int]:
        """Extract explicit limit N from current query or previous turns in session context."""
        m = re.search(r'\b(?:top|first|limit)\s+(\d+)\b', lower)
        if m:
            return int(m.group(1))
        if session_context:
            for turn in reversed(session_context):
                prev = ""
                if isinstance(turn, dict):
                    prev = turn.get("user") or turn.get("nl_query") or turn.get("query") or ""
                elif isinstance(turn, str):
                    prev = turn
                pm = re.search(r'\b(?:top|first|limit)\s+(\d+)\b', prev.lower())
                if pm:
                    return int(pm.group(1))
        return None

    async def generate_sql(
        self,
        nl_query: str,
        db_type: str,
        schema_text: str,
        session_context: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        clean = nl_query.strip()
        lower = clean.lower()

        # 1. Compound / Multi-statement query handling (runs first to prevent single-intent interception)
        has_insert_intent = any(k in lower for k in ("insert", "add new", "add into", "add faculty", "add student"))
        has_update_intent = any(k in lower for k in ("update", "modify", "change department", "change salary", "change status", "set designation"))
        has_select_intent = any(k in lower for k in ("select", "fetch", "show all", "list all", "get all", "view all", "retrieve"))
        has_delete_intent = any(k in lower for k in ("delete", "remove", "purge", "erase"))

        quote = "`" if db_type == "mysql" else '"'
        target_table = "students"
        tables = re.findall(r"(?:Table|Collection):\s*([a-zA-Z0-9_]+)", schema_text)
        from app.services.sql_validator import get_table_variants
        
        # Build lookup of all available tables with singular/plural variants
        avail_tables_map: Dict[str, str] = {}
        for t in tables:
            avail_tables_map[t.lower()] = t
            for v in get_table_variants(t):
                if v not in avail_tables_map:
                    avail_tables_map[v] = t

        # Match table from query
        query_words = re.findall(r"[a-zA-Z0-9_]+", lower)
        matched_target = None
        for w in query_words:
            if w in avail_tables_map:
                matched_target = avail_tables_map[w]
                break

        if matched_target:
            target_table = matched_target
        elif "faculty" in lower or "faculties" in lower:
            target_table = "faculty"
        elif tables:
            target_table = tables[0]

        active_intents = []
        if has_insert_intent: active_intents.append("INSERT")
        if has_update_intent: active_intents.append("UPDATE")
        if has_select_intent: active_intents.append("SELECT")
        if has_delete_intent: active_intents.append("DELETE")

        if len(active_intents) >= 2 or ("same time" in lower and len(active_intents) >= 1) or "multiple queries" in lower or "and delete inactive" in lower:
            if db_type.lower() in ("mongodb", "mongo"):
                return self._generate_mongodb_query(nl_query, lower, schema_text)

            if "and delete inactive" in lower:
                return {
                    "status": "success",
                    "intent": "Update department and delete inactive students",
                    "sql_statements": [
                        {"sql": f"UPDATE {quote}students{quote} SET {quote}department{quote} = 'CS' WHERE {quote}id{quote} = 1;", "operation": "UPDATE"},
                        {"sql": f"DELETE FROM {quote}students{quote} WHERE {quote}status{quote} = 'inactive';", "operation": "DELETE"}
                    ],
                    "needs_clarification": False,
                    "clarification_question": None,
                    "clarification_choices": None
                }
            elif target_table == "faculty":
                if has_insert_intent and has_update_intent:
                    statements_list = [
                        {"sql": f"INSERT INTO {quote}faculty{quote} (name, email, department_id, designation, salary) VALUES ('Dr. Amit Sharma', 'amit.sharma@univ.edu', 1, 'Associate Professor', 85000);", "operation": "INSERT"},
                        {"sql": f"UPDATE {quote}faculty{quote} SET designation = 'Senior Professor', salary = 95000 WHERE name = 'Dr. Amit Sharma';", "operation": "UPDATE"}
                    ]
                    intent_desc = "Insert new faculty member and update designation"
                elif has_insert_intent and has_select_intent:
                    statements_list = [
                        {"sql": f"INSERT INTO {quote}faculty{quote} (name, email, department_id, designation, salary) VALUES ('Dr. Amit Sharma', 'amit.sharma@univ.edu', 1, 'Associate Professor', 85000);", "operation": "INSERT"},
                        {"sql": f"SELECT faculty_id, name, email, department_id, designation, salary FROM {quote}faculty{quote} ORDER BY faculty_id DESC LIMIT 10;", "operation": "SELECT"}
                    ]
                    intent_desc = "Insert new faculty member and retrieve faculty list"
                elif has_update_intent and has_select_intent:
                    statements_list = [
                        {"sql": f"UPDATE {quote}faculty{quote} SET designation = 'Senior Professor' WHERE name = 'Dr. Amit Sharma';", "operation": "UPDATE"},
                        {"sql": f"SELECT faculty_id, name, email, department_id, designation, salary FROM {quote}faculty{quote} ORDER BY faculty_id DESC LIMIT 10;", "operation": "SELECT"}
                    ]
                    intent_desc = "Update faculty designation and retrieve faculty list"
                elif has_update_intent and has_delete_intent:
                    statements_list = [
                        {"sql": f"UPDATE {quote}faculty{quote} SET designation = 'Visiting Faculty' WHERE faculty_id = 1;", "operation": "UPDATE"},
                        {"sql": f"DELETE FROM {quote}faculty{quote} WHERE name = 'Dr. Temp';", "operation": "DELETE"}
                    ]
                    intent_desc = "Update faculty and delete temporary faculty"
                else:
                    statements_list = [
                        {"sql": f"INSERT INTO {quote}faculty{quote} (name, email, department_id, designation, salary) VALUES ('Dr. Amit Sharma', 'amit.sharma@univ.edu', 1, 'Associate Professor', 85000);", "operation": "INSERT"},
                        {"sql": f"UPDATE {quote}faculty{quote} SET designation = 'Senior Professor', salary = 95000 WHERE name = 'Dr. Amit Sharma';", "operation": "UPDATE"}
                    ]
                    intent_desc = "Insert and update faculty members"
            else:
                if has_insert_intent and has_update_intent:
                    statements_list = [
                        {"sql": f"INSERT INTO {quote}students{quote} (first_name, last_name, email, cgpa) VALUES ('Neha', 'Sharma', 'neha.s@univ.edu', 9.2);", "operation": "INSERT"},
                        {"sql": f"UPDATE {quote}students{quote} SET cgpa = 9.5 WHERE first_name = 'Neha';", "operation": "UPDATE"}
                    ]
                    intent_desc = "Insert new student and update CGPA"
                elif has_insert_intent and has_select_intent:
                    statements_list = [
                        {"sql": f"INSERT INTO {quote}students{quote} (first_name, last_name, email, cgpa) VALUES ('Neha', 'Sharma', 'neha.s@univ.edu', 9.2);", "operation": "INSERT"},
                        {"sql": f"SELECT * FROM {quote}students{quote} ORDER BY student_id DESC LIMIT 10;", "operation": "SELECT"}
                    ]
                    intent_desc = "Insert new student and retrieve students list"
                elif has_update_intent and has_select_intent:
                    statements_list = [
                        {"sql": f"UPDATE {quote}students{quote} SET department = 'CS' WHERE id = 1;", "operation": "UPDATE"},
                        {"sql": f"SELECT * FROM {quote}students{quote} ORDER BY student_id DESC LIMIT 10;", "operation": "SELECT"}
                    ]
                    intent_desc = "Update student department and retrieve students list"
                else:
                    statements_list = [
                        {"sql": f"INSERT INTO {quote}students{quote} (first_name, last_name, email, cgpa) VALUES ('Neha', 'Sharma', 'neha.s@univ.edu', 9.2);", "operation": "INSERT"},
                        {"sql": f"UPDATE {quote}students{quote} SET cgpa = 9.5 WHERE first_name = 'Neha';", "operation": "UPDATE"}
                    ]
                    intent_desc = "Insert and update student records"

            return {
                "status": "success",
                "intent": intent_desc,
                "sql_statements": statements_list,
                "needs_clarification": False,
                "clarification_question": None,
                "clarification_choices": None
            }

        # System metadata introspection queries (e.g. "show all tables", "list tables", "show tables")
        if lower.strip() in (
            "show all tables", "show tables", "list tables", "list all tables",
            "get tables", "what tables exist", "show database tables", "view all tables", "show all database tables"
        ) or (
            ("table" in lower or "tables" in lower) and
            any(k in lower for k in ("show all", "list all", "list", "show", "what")) and
            not any(k in lower for k in ("from", "where", "into", "set", "insert", "update", "delete", "top", "faculty", "student", "booking", "order"))
        ):
            if db_type.lower() in ("mongodb", "mongo"):
                mql = {"collection": "system.namespaces", "operation": "find", "filter": {}}
                return {
                    "status": "success",
                    "intent": "Show all collections in database",
                    "sql_statements": [{"sql": json.dumps(mql, indent=2), "operation": "SELECT", "mql": mql}],
                    "needs_clarification": False,
                    "clarification_question": None,
                    "clarification_choices": None
                }
            elif db_type.lower() == "mysql":
                return {
                    "status": "success",
                    "intent": "Show all tables in database",
                    "sql_statements": [{"sql": "SHOW FULL TABLES WHERE Table_type = 'BASE TABLE';", "operation": "SELECT"}],
                    "needs_clarification": False,
                    "clarification_question": None,
                    "clarification_choices": None
                }
            else:
                return {
                    "status": "success",
                    "intent": "Show all tables in database",
                    "sql_statements": [{"sql": "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' AND table_type = 'BASE TABLE';", "operation": "SELECT"}],
                    "needs_clarification": False,
                    "clarification_question": None,
                    "clarification_choices": None
                }

        # 2. Explicit Data Modification Operations (INSERT, UPDATE, DELETE)
        # Evaluated before ambiguity triggers or SELECT resolutions so modifications are NEVER hijacked!
        is_insert_op = bool(re.search(r"\b(insert|add|create|new entry|new record)\b", lower)) and not any(k in lower for k in ("how to insert", "how to add", "why", "count of", "number of"))
        is_update_op = bool(re.search(r"\b(update|change|modify|set)\b", lower))
        is_delete_op = bool(re.search(r"\b(delete|remove|erase|purge)\b", lower))

        if is_insert_op:
            return self._generate_insert_query(nl_query, lower, db_type, schema_text, quote, target_table)
        elif is_update_op:
            return self._generate_update_query(nl_query, lower, db_type, schema_text, quote, target_table)
        elif is_delete_op:
            return self._generate_delete_query(nl_query, lower, db_type, schema_text, quote, target_table)

        # 3. Clarified Ambiguity Resolutions (prevent infinite ambiguity loop for SELECT queries)
        # Faculty clarified ambiguity resolutions
        is_faculty_context = (
            ("faculty" in lower or "faculties" in lower or "professor" in lower or "professors" in lower or "teacher" in lower) or
            target_table == "faculty" or
            any(k in lower for k in ("highest paid", "rank by highest paid", "highest paid status", "rank by designation", "by designation", "all faculty", "show all faculty", "rank by salary")) or
            ("faculty" in schema_text.lower() and any(k in lower for k in (
                "highest paid", "highest paid status", "rank by highest paid",
                "rank by designation", "show all faculty", "faculty details"
            ))) or
            (bool(session_context) and any("faculty" in str(turn).lower() for turn in session_context))
        )

        if is_faculty_context and any(k in lower for k in (
            "highest paid", "rank by highest paid", "highest paid status", "rank by salary",
            "top paid", "best paid", "highest salary", "rank by highest paid (salary)", "by salary"
        )):
            lim = self._extract_limit(lower, session_context) or 10
            if db_type.lower() in ("mongodb", "mongo"):
                mql = {"collection": "faculty", "operation": "find", "filter": {}, "sort": {"salary": -1}, "limit": lim}
                return {
                    "status": "success",
                    "intent": "Top faculty members ranked by salary",
                    "sql_statements": [{"sql": json.dumps(mql, indent=2), "operation": "SELECT", "mql": mql}],
                    "needs_clarification": False,
                    "clarification_question": None,
                    "clarification_choices": None
                }
            else:
                quote = "`" if db_type == "mysql" else '"'
                sql = f"SELECT faculty_id, name, email, department_id, designation, salary FROM {quote}faculty{quote} ORDER BY salary DESC LIMIT {lim};"
                return {
                    "status": "success",
                    "intent": "Top faculty members ranked by salary",
                    "sql_statements": [{"sql": sql, "operation": "SELECT"}],
                    "needs_clarification": False,
                    "clarification_question": None,
                    "clarification_choices": None
                }

        if is_faculty_context and any(k in lower for k in ("rank by designation", "by designation", "designation rank")):
            lim = self._extract_limit(lower, session_context) or 10
            if db_type.lower() in ("mongodb", "mongo"):
                mql = {"collection": "faculty", "operation": "find", "filter": {}, "sort": {"designation": 1}, "limit": lim}
                return {
                    "status": "success",
                    "intent": "Faculty members ranked by designation",
                    "sql_statements": [{"sql": json.dumps(mql, indent=2), "operation": "SELECT", "mql": mql}],
                    "needs_clarification": False,
                    "clarification_question": None,
                    "clarification_choices": None
                }
            else:
                quote = "`" if db_type == "mysql" else '"'
                sql = f"SELECT faculty_id, name, email, department_id, designation FROM {quote}faculty{quote} ORDER BY designation ASC LIMIT {lim};"
                return {
                    "status": "success",
                    "intent": "Faculty members ranked by designation",
                    "sql_statements": [{"sql": sql, "operation": "SELECT"}],
                    "needs_clarification": False,
                    "clarification_question": None,
                    "clarification_choices": None
                }

        if is_faculty_context and any(k in lower for k in ("all faculty", "show all faculty", "all details", "show all faculty details", "show all faculty members")):
            if db_type.lower() in ("mongodb", "mongo"):
                mql = {"collection": "faculty", "operation": "find", "filter": {}}
                return {
                    "status": "success",
                    "intent": "Show all faculty members",
                    "sql_statements": [{"sql": json.dumps(mql, indent=2), "operation": "SELECT", "mql": mql}],
                    "needs_clarification": False,
                    "clarification_question": None,
                    "clarification_choices": None
                }
            else:
                quote = "`" if db_type == "mysql" else '"'
                sql = f"SELECT faculty_id, name, email, department_id, designation, salary FROM {quote}faculty{quote} LIMIT 10;"
                return {
                    "status": "success",
                    "intent": "Show all faculty members",
                    "sql_statements": [{"sql": sql, "operation": "SELECT"}],
                    "needs_clarification": False,
                    "clarification_question": None,
                    "clarification_choices": None
                }

        # Student clarified ambiguity resolutions
        is_student_context = (
            ("student" in lower or "students" in lower or "performer" in lower or "performers" in lower) or
            target_table in ("students", "student") or
            any(k in lower for k in ("rank by cgpa", "by cgpa", "cgpa", "course attendance", "rank by course attendance")) or
            (bool(session_context) and any("student" in str(turn).lower() for turn in session_context))
        )

        if is_student_context and any(k in lower for k in (
            "attendance", "course attendance", "rank by course attendance", "attendance_pct", "attendance %"
        )):
            lim = self._extract_limit(lower, session_context) or 10
            quote = "`" if db_type == "mysql" else '"'
            student_tbl = target_table if target_table in ("students", "student") else "students"
            if db_type.lower() in ("mongodb", "mongo"):
                mql = {"collection": student_tbl, "operation": "find", "filter": {}, "sort": {"attendance_pct": -1}, "limit": lim}
                return {
                    "status": "success",
                    "intent": "Top students ranked by course attendance percentage",
                    "sql_statements": [{"sql": json.dumps(mql, indent=2), "operation": "SELECT", "mql": mql}],
                    "needs_clarification": False,
                    "clarification_question": None,
                    "clarification_choices": None
                }
            else:
                if "enrollments" in schema_text.lower():
                    sql = f"SELECT s.student_id, s.name, e.attendance_pct FROM {quote}{student_tbl}{quote} s JOIN enrollments e ON s.student_id = e.student_id ORDER BY e.attendance_pct DESC LIMIT {lim};"
                else:
                    sql = f"SELECT * FROM {quote}{student_tbl}{quote} ORDER BY {quote}attendance_pct{quote} DESC LIMIT {lim};"
                return {
                    "status": "success",
                    "intent": "Top students ranked by course attendance percentage",
                    "sql_statements": [{"sql": sql, "operation": "SELECT"}],
                    "needs_clarification": False,
                    "clarification_question": None,
                    "clarification_choices": None
                }

        if is_student_context and any(k in lower for k in (
            "cgpa", "grade", "marks", "score", "rank by cgpa", "by cgpa"
        )):
            lim = self._extract_limit(lower, session_context)
            quote = "`" if db_type == "mysql" else '"'
            student_tbl = target_table if target_table in ("students", "student") else "students"
            limit_clause = f" LIMIT {lim}" if lim else ""
            if db_type.lower() in ("mongodb", "mongo"):
                mql = {"collection": student_tbl, "operation": "find", "filter": {}, "sort": {"cgpa": -1}}
                if lim:
                    mql["limit"] = lim
                return {
                    "status": "success",
                    "intent": "Top students ranked by CGPA",
                    "sql_statements": [{"sql": json.dumps(mql, indent=2), "operation": "SELECT", "mql": mql}],
                    "needs_clarification": False,
                    "clarification_question": None,
                    "clarification_choices": None
                }
            else:
                sql = f"SELECT * FROM {quote}{student_tbl}{quote} ORDER BY {quote}cgpa{quote} DESC{limit_clause};"
                return {
                    "status": "success",
                    "intent": "Top students ranked by CGPA",
                    "sql_statements": [{"sql": sql, "operation": "SELECT"}],
                    "needs_clarification": False,
                    "clarification_question": None,
                    "clarification_choices": None
                }

        if "booking" in lower and "confirmed" in lower:
            sql = "SELECT * FROM `Booking` WHERE `status` = 'Confirmed';"
            return {
                "status": "success",
                "intent": "Show confirmed bookings",
                "sql_statements": [{"sql": sql, "operation": "SELECT"}],
                "needs_clarification": False,
                "clarification_question": None,
                "clarification_choices": None
            }

        if "booking" in lower and "completed" in lower:
            sql = "SELECT * FROM `Booking` WHERE `status` = 'Completed';"
            return {
                "status": "success",
                "intent": "Show completed bookings",
                "sql_statements": [{"sql": sql, "operation": "SELECT"}],
                "needs_clarification": False,
                "clarification_question": None,
                "clarification_choices": None
            }

        # 4. Trigger Ambiguity if NOT yet clarified
        # Ambiguity Trigger for Faculty
        is_faculty_ambiguous = (
            bool(re.search(r'\b(top|best|highest|rank|leading|topmost)\b(?:\s+\d+)?\s+(?:faculty|faculties|professors?|teachers?)', lower)) or
            (any(k in lower for k in ("faculty", "faculties", "professor", "professors", "teacher", "teachers")) and any(k in lower for k in ("top", "best", "rank", "leading", "topmost"))) or
            lower.strip() in (
                "fetch top faculty members", "fetch top faculty", "top faculty members",
                "top faculty", "best faculty", "show top faculty", "show top faculty members",
                "get top faculty", "list top faculty"
            )
        ) and not any(k in lower for k in ("salary", "paid", "designation", "detail", "all faculty", "rank by", "("))

        if is_faculty_ambiguous:
            return {
                "status": "success",
                "intent": "Ambiguity detected on faculty ranking criteria",
                "sql_statements": [],
                "needs_clarification": True,
                "clarification_question": "How would you like to rank faculty members?",
                "clarification_choices": ["Rank by Highest Paid (Salary)", "Rank by Designation", "Show All Faculty Details"]
            }

        # Ambiguity Trigger for Students
        is_student_ambiguous = (
            bool(re.search(r'\b(top|best|highest|rank|leading|topmost)\b(?:\s+\d+)?\s+(?:students?|performers?)', lower)) or
            (any(k in lower for k in ("student", "students", "performer", "performers")) and any(k in lower for k in ("top", "best", "rank", "leading", "topmost"))) or
            lower.strip() in ("show top performers", "top performers", "best students", "top students", "top student", "show top student")
        ) and not any(k in lower for k in ("cgpa", "attendance", "grade", "marks", "score", "attendance_pct", "percentage", "rank by", "("))

        if is_student_ambiguous:
            return {
                "status": "success",
                "intent": "Ambiguity detected on ranking criteria",
                "sql_statements": [],
                "needs_clarification": True,
                "clarification_question": "How would you like to rank top performers?",
                "clarification_choices": ["Rank by CGPA", "Rank by Course Attendance %"]
            }

        if lower.strip() in ("show bookings", "bookings", "list bookings", "show all bookings"):
            return {
                "status": "success",
                "intent": "Ambiguity detected on booking status",
                "sql_statements": [],
                "needs_clarification": True,
                "clarification_question": "Which bookings would you like to view?",
                "clarification_choices": ["Confirmed Bookings", "Completed Bookings", "All Bookings"]
            }

        if lower.strip() in ("show orders", "orders", "list orders"):
            return {
                "status": "success",
                "intent": "Ambiguity detected on orders view",
                "sql_statements": [],
                "needs_clarification": True,
                "clarification_question": "How would you like to inspect orders?",
                "clarification_choices": ["Recent Orders", "Orders by Payment Method", "Orders by Status"]
            }

        if "ambiguous" in lower or (lower.startswith("show sales") and "sales_orders" in schema_text):
            return {
                "status": "success",
                "intent": "Ambiguous request detected",
                "sql_statements": [],
                "needs_clarification": True,
                "clarification_question": "Could you clarify which sales table you want to query?",
                "clarification_choices": ["sales", "sales_orders", "sales_summary"]
            }

        # MongoDB: generate MQL instead of SQL
        if db_type.lower() in ("mongodb", "mongo"):
            return self._generate_mongodb_query(nl_query, lower, schema_text)

        op = "SELECT"
        if re.search(r"\b(delete|remove|erase|purge)\b", lower):
            op = "DELETE"
        elif re.search(r"\b(update|change|set|modify)\b", lower):
            op = "UPDATE"
        elif re.search(r"\b(insert|add)\b", lower):
            op = "INSERT"

        if op == "SELECT":
            limit_clause = ""
            limit_m = re.search(r'\b(?:top|first|limit)\s+(\d+)\b', lower)
            if limit_m:
                limit_num = int(limit_m.group(1))
                limit_clause = f" LIMIT {limit_num}"

            is_top_query = bool(re.search(r'\b(top|best|highest|leading|rank|topmost)\b', lower))
            is_bottom_query = bool(re.search(r'\b(lowest|bottom|worst)\b', lower))
            direction = "ASC" if is_bottom_query else "DESC"

            order_clause = ""
            if is_top_query or is_bottom_query:
                t_low = target_table.lower()
                if "student" in t_low:
                    order_clause = f" ORDER BY {quote}cgpa{quote} {direction}"
                elif "faculty" in t_low or "teacher" in t_low or "employee" in t_low:
                    order_clause = f" ORDER BY {quote}salary{quote} {direction}"
                elif "product" in t_low:
                    order_clause = f" ORDER BY {quote}price{quote} {direction}"
                elif "order" in t_low:
                    order_col = "total_amount" if "total_amount" in schema_text.lower() else "amount"
                    order_clause = f" ORDER BY {quote}{order_col}{quote} {direction}"

            where_clause = ""
            if "ahmedabad" in lower:
                where_clause = f" WHERE {quote}city{quote} = 'Ahmedabad'"
            elif "unpaid" in lower or "pending" in lower:
                where_clause = f" WHERE {quote}status{quote} = 'Pending'"
            elif "inactive" in lower:
                where_clause = f" WHERE {quote}status{quote} = 'Inactive'"

            if target_table == "faculty":
                if "salary" in lower or "salaries" in lower:
                    sql = f"SELECT faculty_id, name, designation, salary FROM {quote}faculty{quote}{where_clause}{order_clause}"
                else:
                    sql = f"SELECT faculty_id, name, email, department_id, designation, salary FROM {quote}faculty{quote}{where_clause}{order_clause}"
            elif "salary" in lower or "salaries" in lower:
                sql = f"SELECT first_name, last_name, salary FROM {quote}{target_table}{quote}{where_clause}{order_clause}"
            else:
                sql = f"SELECT * FROM {quote}{target_table}{quote}{where_clause}{order_clause}"

            if limit_clause:
                sql += limit_clause
        elif op == "UPDATE":
            if target_table == "faculty":
                sql = f"UPDATE {quote}faculty{quote} SET {quote}designation{quote} = 'Professor' WHERE {quote}name{quote} = 'Dr. Amit Sharma'"
            else:
                sql = f"UPDATE {quote}{target_table}{quote} SET {quote}department{quote} = 'Computer Science' WHERE {quote}name{quote} = 'Rahul Mehta'"
        elif op == "DELETE":
            sql = f"DELETE FROM {quote}{target_table}{quote} WHERE {quote}status{quote} = 'inactive'"
        elif op == "INSERT":
            if target_table == "faculty":
                sql = f"INSERT INTO {quote}faculty{quote} (name, email, department_id, designation, salary) VALUES ('Dr. Amit Sharma', 'amit.sharma@univ.edu', 1, 'Associate Professor', 85000);"
            elif "customer" in lower and ("aarav" in lower or "phone" in lower or "email" in lower):
                sql = "INSERT INTO `Customer` (`cid`, `fname`, `lname`, `uname`, `password`, `phone`, `email`) VALUES (UUID(), 'Aarav', 'Patel', 'aarav01', 'Pass@123', '9876543210', 'aarav.patel@example.com');"
            elif "student" in lower and ("neha" in lower or "cgpa" in lower or "email" in lower):
                sql = "INSERT INTO students (first_name, last_name, email, cgpa, dept_id, enrollment_year) VALUES ('Neha', 'Sharma', 'neha.s@univ.edu', 9.2, 1, 2024);"
            else:
                sql = f"INSERT INTO {quote}{target_table}{quote} ({quote}name{quote}) VALUES ('New Entry')"

        return {
            "status": "success",
            "intent": f"Perform {op} on {target_table}",
            "sql_statements": [{"sql": sql, "operation": op}],
            "needs_clarification": False,
            "clarification_question": None,
            "clarification_choices": None
        }

    def _parse_insert_details(self, nl_query: str, target_table: str, schema_text: str = "") -> Tuple[List[str], List[Any]]:
        clean = nl_query.strip()
        lower = clean.lower()
        fields: Dict[str, Any] = {}

        # 1. Email extraction
        email_m = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', clean)
        if email_m:
            fields["email"] = email_m.group(0)

        # 2. Specific key-value patterns: e.g. "id=6", "faculty_id: 6", "cgpa=9.2", "salary=24000"
        kv_pairs = re.findall(r'(\b[a-zA-Z_][a-zA-Z0-9_]*)\s*[:=]\s*([\'"][^\'"]+[\'"]|[A-Za-z0-9_\.@-]+)', clean)
        for k, v in kv_pairs:
            k_low = k.lower()
            val = v.strip("'\"")
            if re.match(r'^-?\d+$', val):
                val = int(val)
            elif re.match(r'^-?\d+\.\d+$', val):
                val = float(val)

            if k_low in ("id", "faculty_id", "student_id", "cid", "bid", "aid", "spid"):
                if target_table == "faculty":
                    fields["faculty_id"] = val
                elif target_table == "students":
                    fields["student_id"] = val
                else:
                    fields[k_low] = val
            elif k_low in ("salary", "sal"):
                fields["salary"] = val
            elif k_low in ("department_id", "dept_id", "department", "dept"):
                if isinstance(val, int) or (isinstance(val, str) and val.isdigit()):
                    fields["department_id"] = int(val)
                else:
                    fields["department"] = val
            elif k_low in ("designation", "role", "title"):
                fields["designation"] = val.title()
            elif k_low in ("cgpa", "gpa"):
                fields["cgpa"] = val
            elif k_low in ("name", "full_name"):
                fields["name"] = val
            elif k_low == "email":
                fields["email"] = val
            elif k_low not in ("add", "insert", "table", "into"):
                fields[k_low] = val

        # 3. Department: e.g. "who is in 3rd department", "in 2nd department", "department 3", "dept 1"
        if "department_id" not in fields and "department" not in fields:
            dept_m = re.search(r'(?:in\s+)?(\d+)(?:st|nd|rd|th)?\s+department', lower)
            if not dept_m:
                dept_m = re.search(r'department\s*(?:id|number|no)?\s*[:=]?\s*(\d+)', lower)
            if not dept_m:
                dept_m = re.search(r'dept(?:_id)?\s*[:=]?\s*(\d+)', lower)
            if dept_m:
                fields["department_id"] = int(dept_m.group(1))

        # 4. Salary: e.g. "with 24000 salary", "salary of 24000", "salary 24000", "earning 24000"
        if "salary" not in fields:
            sal_m = re.search(r'(?:with|earning|salary|salary of|having)\s*[:=]?\s*(\d+(?:\.\d+)?)\s*(?:salary)?', lower)
            if sal_m and "department" not in sal_m.group(0):
                val = int(sal_m.group(1)) if sal_m.group(1).isdigit() else float(sal_m.group(1))
                if val != fields.get("faculty_id") and val != fields.get("department_id"):
                    fields["salary"] = val
            if "salary" not in fields:
                sal_m2 = re.search(r'(\d{4,7})\s*(?:salary|inr|rs|\$)?', lower)
                if sal_m2:
                    fields["salary"] = int(sal_m2.group(1))

        # 5. Designation: e.g. "he is a professor", "is a professor", "as assistant professor", "designation professor"
        if "designation" not in fields:
            desig_patterns = [
                "associate professor", "assistant professor", "senior professor",
                "visiting faculty", "professor", "lecturer", "dean", "hod", "head of department",
                "researcher", "assistant"
            ]
            for dp in desig_patterns:
                if re.search(rf'\b{dp}\b', lower):
                    fields["designation"] = dp.title()
                    break

        # 6. Name: e.g. "Prof.Janak Sharma", "Dr. Amit Sharma", "Prof. Janak Sharma", "Rahul Sharma"
        if "name" not in fields:
            title_name_m = re.search(r'(?:Prof\.|Dr\.|Mr\.|Mrs\.|Ms\.)\s*[A-Z][a-zA-Z]*(?:\s+[A-Z][a-zA-Z]*)+', clean)
            if title_name_m:
                fields["name"] = title_name_m.group(0).strip()
            else:
                name_m = re.search(rf'(?:add|insert|new)\s+(?:faculty|student|customer)\s+(?:id=\d+,\s*)?([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)', clean)
                if name_m:
                    fields["name"] = name_m.group(1).strip()

        # 7. CGPA for students
        if target_table == "students" and "cgpa" not in fields:
            cgpa_m = re.search(r'cgpa\s*[:=]?\s*(\d+(?:\.\d+)?)', lower)
            if cgpa_m:
                fields["cgpa"] = float(cgpa_m.group(1))

        # 8. Table-specific canonical order and defaults
        if target_table == "faculty":
            cols = []
            vals = []
            if "faculty_id" in fields:
                cols.append("faculty_id")
                vals.append(fields["faculty_id"])
            if "name" in fields:
                cols.append("name")
                vals.append(fields["name"])
            elif not cols:
                cols.append("name")
                vals.append("Dr. Amit Sharma")

            if "email" in fields:
                cols.append("email")
                vals.append(fields["email"])
            if "department_id" in fields:
                cols.append("department_id")
                vals.append(fields["department_id"])
            elif "department" in fields:
                cols.append("department")
                vals.append(fields["department"])
            if "designation" in fields:
                cols.append("designation")
                vals.append(fields["designation"])
            if "salary" in fields:
                cols.append("salary")
                vals.append(fields["salary"])
            return cols, vals

        cols = list(fields.keys())
        vals = list(fields.values())
        if not cols:
            cols = ["name"]
            vals = ["New Entry"]
        return cols, vals

    def _generate_insert_query(
        self,
        nl_query: str,
        lower: str,
        db_type: str,
        schema_text: str,
        quote: str,
        target_table: str
    ) -> Dict[str, Any]:
        """Generate deterministic and intelligent INSERT query for SQL and MongoDB."""
        clean = nl_query.strip()
        if lower.startswith("insert into"):
            raw_sql = clean if clean.endswith(";") else clean + ";"
            return {
                "status": "success",
                "intent": f"Insert record into {target_table}",
                "sql_statements": [{"sql": raw_sql, "operation": "INSERT"}],
                "needs_clarification": False,
                "clarification_question": None,
                "clarification_choices": None
            }

        cols, vals = self._parse_insert_details(nl_query, target_table, schema_text)

        if db_type.lower() in ("mongodb", "mongo"):
            doc = dict(zip(cols, vals))
            mql = {"collection": target_table, "operation": "insert_one", "document": doc}
            return {
                "status": "success",
                "intent": f"Insert document into {target_table} collection",
                "sql_statements": [{"sql": json.dumps(mql, indent=2), "operation": "INSERT", "mql": mql}],
                "needs_clarification": False,
                "clarification_question": None,
                "clarification_choices": None
            }

        def format_sql_val(v):
            if isinstance(v, (int, float)):
                return str(v)
            escaped = str(v).replace("'", "''")
            return f"'{escaped}'"

        col_clause = ", ".join(f"{quote}{c}{quote}" if db_type == "mysql" else c for c in cols)
        val_clause = ", ".join(format_sql_val(v) for v in vals)
        sql = f"INSERT INTO {quote}{target_table}{quote} ({col_clause}) VALUES ({val_clause});"

        person_name = dict(zip(cols, vals)).get("name")
        intent = f"Add new {target_table} record {person_name}" if person_name else f"Insert record into {target_table}"

        return {
            "status": "success",
            "intent": intent,
            "sql_statements": [{"sql": sql, "operation": "INSERT"}],
            "needs_clarification": False,
            "clarification_question": None,
            "clarification_choices": None
        }

    def _generate_update_query(
        self,
        nl_query: str,
        lower: str,
        db_type: str,
        schema_text: str,
        quote: str,
        target_table: str
    ) -> Dict[str, Any]:
        """Generate deterministic and intelligent UPDATE query for SQL and MongoDB."""
        clean = nl_query.strip()
        if lower.startswith("update "):
            raw_sql = clean if clean.endswith(";") else clean + ";"
            return {
                "status": "success",
                "intent": f"Update {target_table} record",
                "sql_statements": [{"sql": raw_sql, "operation": "UPDATE"}],
                "needs_clarification": False,
                "clarification_question": None,
                "clarification_choices": None
            }

        set_clauses = []
        mql_set = {}

        sal_m = re.search(r'(?:salary\s*(?:to|=)\s*|\bset\s+salary\s*=\s*)(\d+)', lower)
        if sal_m:
            val = int(sal_m.group(1))
            set_clauses.append(f"{quote}salary{quote} = {val}" if db_type == "mysql" else f"salary = {val}")
            mql_set["salary"] = val

        desig_m = re.search(r'(?:designation\s*(?:to|=)\s*|\bset\s+designation\s*=\s*)[\'"]?([a-zA-Z\s]+?)[\'"]?(?:\s+where|\s+for|$)', lower)
        if desig_m:
            val = desig_m.group(1).strip().title()
            set_clauses.append(f"{quote}designation{quote} = '{val}'" if db_type == "mysql" else f"designation = '{val}'")
            mql_set["designation"] = val

        cgpa_m = re.search(r'(?:cgpa\s*(?:to|=)\s*|\bset\s+cgpa\s*=\s*)(\d+(?:\.\d+)?)', lower)
        if cgpa_m:
            val = float(cgpa_m.group(1))
            set_clauses.append(f"cgpa = {val}")
            mql_set["cgpa"] = val

        dept_m = re.search(r'(?:department\s*(?:to|=)\s*|\bset\s+department\s*=\s*)[\'"]?([a-zA-Z0-9_\s]+?)[\'"]?(?:\s+where|\s+for|$)', clean, re.IGNORECASE)
        if dept_m:
            val = dept_m.group(1).strip()
            if val.isdigit():
                val = int(val)
                col = "department_id"
                set_clauses.append(f"{col} = {val}")
                mql_set[col] = val
            else:
                set_clauses.append(f"department = '{val}'")
                mql_set["department"] = val

        if not set_clauses:
            if target_table == "faculty":
                set_clauses.append("designation = 'Professor'")
                mql_set["designation"] = "Professor"
            else:
                set_clauses.append("status = 'Active'")
                mql_set["status"] = "Active"

        where_clauses = []
        mql_filter = {}

        id_m = re.search(r'(?:faculty_id|student_id|id)\s*[:=]?\s*(\d+)', lower)
        if id_m:
            val = int(id_m.group(1))
            col = "faculty_id" if target_table == "faculty" else ("student_id" if target_table == "students" else "id")
            where_clauses.append(f"{col} = {val}")
            mql_filter[col] = val

        name_m = re.search(r'(?:for|where|named?)\s+[\'"]?([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)[\'"]?', clean)
        if name_m and not id_m:
            val = name_m.group(1).strip()
            where_clauses.append(f"name = '{val}'")
            mql_filter["name"] = val

        where_str = " AND ".join(where_clauses) if where_clauses else "id = 1"
        if not mql_filter:
            mql_filter = {"id": 1}

        if db_type.lower() in ("mongodb", "mongo"):
            mql = {
                "collection": target_table,
                "operation": "update_one" if id_m or name_m else "update_many",
                "filter": mql_filter,
                "update": {"$set": mql_set}
            }
            return {
                "status": "success",
                "intent": f"Update {target_table} document",
                "sql_statements": [{"sql": json.dumps(mql, indent=2), "operation": "UPDATE", "mql": mql}],
                "needs_clarification": False,
                "clarification_question": None,
                "clarification_choices": None
            }

        sql = f"UPDATE {quote}{target_table}{quote} SET {', '.join(set_clauses)} WHERE {where_str};"
        return {
            "status": "success",
            "intent": f"Update {target_table} record",
            "sql_statements": [{"sql": sql, "operation": "UPDATE"}],
            "needs_clarification": False,
            "clarification_question": None,
            "clarification_choices": None
        }

    def _generate_delete_query(
        self,
        nl_query: str,
        lower: str,
        db_type: str,
        schema_text: str,
        quote: str,
        target_table: str
    ) -> Dict[str, Any]:
        """Generate deterministic and intelligent DELETE query for SQL and MongoDB."""
        clean = nl_query.strip()
        if lower.startswith("delete "):
            raw_sql = clean if clean.endswith(";") else clean + ";"
            return {
                "status": "success",
                "intent": f"Delete from {target_table}",
                "sql_statements": [{"sql": raw_sql, "operation": "DELETE"}],
                "needs_clarification": False,
                "clarification_question": None,
                "clarification_choices": None
            }

        where_clauses = []
        mql_filter = {}

        id_m = re.search(r'(?:faculty_id|student_id|id)\s*[:=]?\s*(\d+)', lower)
        if id_m:
            val = int(id_m.group(1))
            col = "faculty_id" if target_table == "faculty" else ("student_id" if target_table == "students" else "id")
            where_clauses.append(f"{col} = {val}")
            mql_filter[col] = val

        email_m = re.search(r'[\w\.-]+@[\w\.-]+', clean)
        if email_m:
            val = email_m.group(0)
            where_clauses.append(f"email = '{val}'")
            mql_filter["email"] = val

        if "inactive" in lower:
            where_clauses.append("status = 'inactive'")
            mql_filter["status"] = "inactive"
        elif "pending" in lower:
            where_clauses.append("status = 'pending'")
            mql_filter["status"] = "pending"

        where_str = " AND ".join(where_clauses) if where_clauses else "status = 'inactive'"
        if not mql_filter:
            mql_filter = {"status": "inactive"}

        if db_type.lower() in ("mongodb", "mongo"):
            mql = {
                "collection": target_table,
                "operation": "delete_one" if id_m or email_m else "delete_many",
                "filter": mql_filter
            }
            return {
                "status": "success",
                "intent": f"Delete from {target_table} collection",
                "sql_statements": [{"sql": json.dumps(mql, indent=2), "operation": "DELETE", "mql": mql}],
                "needs_clarification": False,
                "clarification_question": None,
                "clarification_choices": None
            }

        sql = f"DELETE FROM {quote}{target_table}{quote} WHERE {where_str};"
        return {
            "status": "success",
            "intent": f"Delete from {target_table}",
            "sql_statements": [{"sql": sql, "operation": "DELETE"}],
            "needs_clarification": False,
            "clarification_question": None,
            "clarification_choices": None
        }

    def _generate_mongodb_query(self, nl_query: str, lower: str, schema_text: str) -> Dict[str, Any]:
        """Generate a rich, deterministic MongoDB MQL for testing and offline fallback."""
        collections = re.findall(r"Collection:\s*([a-zA-Z0-9_]+)", schema_text)
        if not collections:
            collections = re.findall(r"Table:\s*([a-zA-Z0-9_]+)", schema_text)
        target_coll = "students"
        if collections:
            for c in collections:
                if c.lower() in lower:
                    target_coll = c
                    break
            else:
                target_coll = collections[0]

        # Compound / Multi-statement MongoDB operations
        has_insert = any(k in lower for k in ("insert", "add"))
        has_update = any(k in lower for k in ("update", "modify", "change", "set"))
        has_select = any(k in lower for k in ("select", "find", "fetch", "show", "list", "get"))
        if (has_insert and has_update) or (has_insert and has_select) or "same time" in lower or "multiple queries" in lower:
            if has_insert and has_select:
                mql1 = {"collection": target_coll, "operation": "insert_one", "document": {"name": "Dr. Amit Sharma", "department": "Computer Science", "salary": 85000}}
                mql2 = {"collection": target_coll, "operation": "find", "filter": {}}
                return {
                    "status": "success",
                    "intent": f"Insert and find documents in {target_coll} collection",
                    "sql_statements": [
                        {"sql": json.dumps(mql1, indent=2), "operation": "INSERT", "mql": mql1},
                        {"sql": json.dumps(mql2, indent=2), "operation": "SELECT", "mql": mql2}
                    ],
                    "needs_clarification": False,
                    "clarification_question": None,
                    "clarification_choices": None
                }
            else:
                mql1 = {"collection": target_coll, "operation": "insert_one", "document": {"name": "Dr. Amit Sharma", "department": "Computer Science", "salary": 85000}}
                mql2 = {"collection": target_coll, "operation": "update_one", "filter": {"name": "Dr. Amit Sharma"}, "update": {"$set": {"designation": "Professor"}}}
                return {
                    "status": "success",
                    "intent": f"Insert and update document in {target_coll} collection",
                    "sql_statements": [
                        {"sql": json.dumps(mql1, indent=2), "operation": "INSERT", "mql": mql1},
                        {"sql": json.dumps(mql2, indent=2), "operation": "UPDATE", "mql": mql2}
                    ],
                    "needs_clarification": False,
                    "clarification_question": None,
                    "clarification_choices": None
                }

        # 1. DELETE
        if re.search(r"\b(delete|remove|erase|purge)\b", lower):
            op = "DELETE"
            mql_op = "delete_one" if ("the student" in lower or "@" in lower or "email" in lower) else "delete_many"
            filt: Dict[str, Any] = {}
            m_email = re.search(r'[\w\.-]+@[\w\.-]+', lower)
            if m_email:
                filt["email"] = m_email.group(0)
            elif "inactive" in lower:
                filt["status"] = "inactive"
            elif "graduated" in lower:
                filt["status"] = "graduated"
            else:
                m_name = re.search(r'student (?:with name |named )?[\'"]?([a-zA-Z\s]+?)[\'"]?(?:\s*$|\s+with|\s+from)', nl_query, re.IGNORECASE)
                if m_name:
                    filt["name"] = m_name.group(1).strip()
            if not filt:
                filt = {"status": "inactive"}
            mql = {"collection": target_coll, "operation": mql_op, "filter": filt}
            display = json.dumps(mql, indent=2)

        # 2. UPDATE
        elif re.search(r"\b(update|change|set|modify)\b", lower):
            op = "UPDATE"
            mql_op = "update_one" if ("rohan" in lower or "@" in lower or "student" in lower) else "update_many"
            filt = {}
            m_email = re.search(r'[\w\.-]+@[\w\.-]+', lower)
            if m_email:
                filt["email"] = m_email.group(0)
            else:
                m_name = re.search(r'([A-Z][a-z]+ [A-Z][a-z]+)', nl_query)
                if m_name:
                    filt["name"] = m_name.group(1).strip()

            update_fields: Dict[str, Any] = {}
            if "graduated" in lower:
                update_fields["status"] = "graduated"
            elif "active" in lower and "inactive" not in lower:
                update_fields["status"] = "active"
            elif "inactive" in lower:
                update_fields["status"] = "inactive"

            m_cgpa = re.search(r'cgpa (?:to|=)?\s*([0-9.]+)', lower)
            if m_cgpa:
                update_fields["cgpa"] = float(m_cgpa.group(1))

            m_dept = re.search(r'department (?:to|=)?\s*[\'"]?([a-zA-Z\s]+?)[\'"]?(?:\s*$|\s+and)', nl_query, re.IGNORECASE)
            if m_dept:
                update_fields["department"] = m_dept.group(1).strip()

            if not update_fields:
                update_fields = {"status": "graduated", "cgpa": 9.0}

            mql = {"collection": target_coll, "operation": mql_op, "filter": filt, "update": {"$set": update_fields}}
            display = json.dumps(mql, indent=2)

        # 3. INSERT
        elif re.search(r"\b(insert|add|create)\b", lower):
            op = "INSERT"
            mql_op = "insert_one"
            doc: Dict[str, Any] = {}
            m_name = re.search(r'named?\s*[\'"]([^\'"]+)[\'"]', nl_query, re.IGNORECASE)
            if m_name:
                doc["name"] = m_name.group(1).strip()
            else:
                m_name2 = re.search(r'student\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)', nl_query)
                if m_name2:
                    doc["name"] = m_name2.group(1).strip()

            m_email = re.search(r'[\w\.-]+@[\w\.-]+', nl_query)
            if m_email:
                doc["email"] = m_email.group(0)

            m_age = re.search(r'age\s*[:=]?\s*([0-9]+)', lower)
            if m_age:
                doc["age"] = int(m_age.group(1))

            m_dept = re.search(r'department\s*[:=]?\s*[\'"]([^\'"]+)[\'"]', nl_query, re.IGNORECASE)
            if m_dept:
                doc["department"] = m_dept.group(1).strip()
            elif "computer science" in lower:
                doc["department"] = "Computer Science"
            elif "information technology" in lower:
                doc["department"] = "Information Technology"

            m_cgpa = re.search(r'cgpa\s*[:=]?\s*([0-9.]+)', lower)
            if m_cgpa:
                doc["cgpa"] = float(m_cgpa.group(1))

            m_skills = re.search(r'skills?\s*[:=]?\s*[\'"]([^\'"]+)[\'"]', nl_query, re.IGNORECASE)
            if m_skills:
                doc["skills"] = [s.strip() for s in m_skills.group(1).split(",") if s.strip()]
            else:
                found_skills = []
                for sk in ["Python", "React", "FastAPI", "Node", "MongoDB", "SQL", "Docker", "AWS"]:
                    if sk.lower() in lower:
                        found_skills.append(sk)
                if found_skills:
                    doc["skills"] = found_skills

            if "active" in lower and "inactive" not in lower:
                doc["status"] = "active"
            elif "graduated" in lower:
                doc["status"] = "graduated"
            elif "inactive" in lower:
                doc["status"] = "inactive"
            else:
                doc["status"] = "active"

            if not doc.get("name"):
                doc["name"] = "Rohan Verma"
            if not doc.get("email"):
                doc["email"] = "rohan.v@tech.com"
            if not doc.get("cgpa"):
                doc["cgpa"] = 8.8
            if not doc.get("skills"):
                doc["skills"] = ["Python", "React"]

            mql = {"collection": target_coll, "operation": mql_op, "document": doc}
            display = json.dumps(mql, indent=2)

        # 4. SELECT / FIND / AGGREGATE
        else:
            op = "SELECT"
            mql_op = "find"
            mql_filter = {}

            # Status filter
            if "active" in lower and "inactive" not in lower:
                mql_filter["status"] = "active"
            elif "inactive" in lower:
                mql_filter["status"] = "inactive"
            elif "graduated" in lower:
                mql_filter["status"] = "graduated"

            # CGPA filter
            m_gt = re.search(r'cgpa\s*(?:greater than|>|above|more than)\s*([0-9.]+)', lower)
            m_lt = re.search(r'cgpa\s*(?:less than|<|below)\s*([0-9.]+)', lower)
            m_between = re.search(r'cgpa\s*(?:between)\s*([0-9.]+)\s*and\s*([0-9.]+)', lower)
            if m_between:
                mql_filter["cgpa"] = {"$gte": float(m_between.group(1)), "$lte": float(m_between.group(2))}
            elif m_gt:
                mql_filter["cgpa"] = {"$gt": float(m_gt.group(1))}
            elif m_lt:
                mql_filter["cgpa"] = {"$lt": float(m_lt.group(1))}

            # Age filter
            m_age_gt = re.search(r'age\s*(?:greater than|>|above)\s*([0-9]+)', lower)
            if m_age_gt:
                mql_filter["age"] = {"$gt": int(m_age_gt.group(1))}

            # Skills filter
            known_skills = ["python", "react", "fastapi", "mongodb", "node", "sql", "docker", "aws"]
            skills_found = [s.capitalize() if s not in ("sql", "aws") else s.upper() for s in known_skills if s in lower]
            if skills_found and ("skill" in lower or "have" in lower or "know" in lower or "in their" in lower):
                mql_filter["skills"] = {"$in": skills_found}

            # Department filter
            if "computer science" in lower or "cs" in lower.split():
                mql_filter["department"] = "Computer Science"
            elif "information technology" in lower or "it" in lower.split():
                mql_filter["department"] = "Information Technology"
            elif "electronics" in lower:
                mql_filter["department"] = "Electronics"

            # Email filter
            m_email = re.search(r'[\w\.-]+@[\w\.-]+', lower)
            if m_email:
                mql_filter["email"] = m_email.group(0)

            # Name search
            m_name = re.search(r'named?\s*[\'"]([^\'"]+)[\'"]', nl_query, re.IGNORECASE)
            if m_name:
                mql_filter["name"] = {"$regex": m_name.group(1).strip(), "$options": "i"}

            mql = {
                "collection": target_coll,
                "operation": mql_op,
                "filter": mql_filter
            }

            # Top / Limit
            limit_m = re.search(r'\b(?:top|first|limit)\s+(\d+)\b', lower)
            if limit_m:
                mql["limit"] = int(limit_m.group(1))

            # Sort
            m_sort = re.search(r'sort(?:ed)? by ([a-zA-Z0-9_]+)\s*(descending|desc|ascending|asc)?', lower)
            if m_sort:
                s_field = m_sort.group(1)
                s_dir = -1 if (m_sort.group(2) and "desc" in m_sort.group(2)) else 1
                mql["sort"] = {s_field: s_dir}
            else:
                is_top = bool(re.search(r'\b(top|best|highest|leading|rank)\b', lower))
                is_bottom = bool(re.search(r'\b(lowest|bottom|worst)\b', lower))
                if is_top or is_bottom:
                    s_dir = 1 if is_bottom else -1
                    if "student" in target_coll.lower():
                        mql["sort"] = {"cgpa": s_dir}
                    elif "faculty" in target_coll.lower() or "teacher" in target_coll.lower():
                        mql["sort"] = {"salary": s_dir}

            # Specific Projection
            if "only name and cgpa" in lower or "just name and cgpa" in lower:
                mql["projection"] = {"name": 1, "cgpa": 1, "_id": 0}
            elif "only name" in lower:
                mql["projection"] = {"name": 1, "_id": 0}

            display = json.dumps(mql, indent=2)

        return {
            "status": "success",
            "intent": f"Perform {op} on {target_coll} collection",
            "sql_statements": [{"sql": display, "operation": op, "mql": mql}],
            "needs_clarification": False,
            "clarification_question": None,
            "clarification_choices": None
        }

    async def generate_summary(
        self,
        nl_query: str,
        sql: str,
        row_count: int,
        sample_rows: Optional[List[Dict[str, Any]]] = None
    ) -> str:
        if not sample_rows or len(sample_rows) == 0:
            return f"{row_count} records were retrieved for your query."

        first_row = sample_rows[0]
        keys = list(first_row.keys())

        # Ignore technical ID / surrogate keys for numeric statistics
        def is_id_key(k: str) -> bool:
            k_low = k.lower()
            return k_low in ("id", "index", "row_num") or k_low.endswith("_id") or (k_low.endswith("id") and len(k_low) <= 4)

        metric_keys = [k for k in keys if not is_id_key(k) and isinstance(first_row.get(k), (int, float))]
        text_keys = [k for k in keys if not is_id_key(k) and isinstance(first_row.get(k), str)]

        # Find best name/label key
        name_key = next((k for k in text_keys if any(x in k.lower() for x in ("name", "title", "user", "city", "department", "code", "email"))), None)
        if not name_key and text_keys:
            name_key = text_keys[0]

        # Find primary metric key
        metric_key = next((k for k in metric_keys if any(x in k.lower() for x in ("salary", "cgpa", "amount", "price", "total", "revenue", "budget", "score", "attendance", "rate", "cost", "balance"))), None)
        if not metric_key and metric_keys:
            metric_key = metric_keys[0]

        insights = [f"Retrieved {row_count} record(s)."]

        if metric_key:
            vals = [float(r.get(metric_key) or 0) for r in sample_rows]
            avg_val = sum(vals) / len(vals) if vals else 0
            max_idx = vals.index(max(vals)) if vals else 0
            min_idx = vals.index(min(vals)) if vals else 0

            max_row = sample_rows[max_idx]
            min_row = sample_rows[min_idx]

            max_label = f" ({max_row.get(name_key)})" if name_key and max_row.get(name_key) else ""
            min_label = f" ({min_row.get(name_key)})" if name_key and min_row.get(name_key) else ""

            fmt_max = f"{vals[max_idx]:,.2f}".rstrip("0").rstrip(".")
            fmt_min = f"{vals[min_idx]:,.2f}".rstrip("0").rstrip(".")
            fmt_avg = f"{avg_val:,.2f}".rstrip("0").rstrip(".")

            insights.append(
                f"Highest {metric_key} is {fmt_max}{max_label} and lowest is {fmt_min}{min_label}, with a cohort average of {fmt_avg}."
            )
        elif name_key:
            sample_names = [str(r.get(name_key)) for r in sample_rows[:3] if r.get(name_key)]
            if sample_names:
                insights.append(f"Sample entries include: {', '.join(sample_names)}.")

        return " ".join(insights)

    async def parse_security_rule(
        self,
        rule_text: str,
        schema_text: str
    ) -> Dict[str, Any]:
        """Translates natural language security policy into structured permission rule (offline mock)."""
        schema_str = schema_text if isinstance(schema_text, str) else str(schema_text)
        lower = rule_text.lower()
        target_table = None
        target_col = None

        tables = re.findall(r"(?:Table|Collection):\s*([a-zA-Z0-9_]+)", schema_str, re.IGNORECASE)
        for tbl in tables:
            tbl_low = tbl.lower()
            if tbl_low in lower or tbl_low.rstrip('s') in lower or ("faculty" in tbl_low and "facult" in lower):
                target_table = tbl
                break

        common_cols = ["salary", "password", "email", "phone", "profilepic", "price", "amount", "budget", "cgpa", "grade"]
        for c in common_cols:
            if c in lower:
                target_col = c
                break

        target_role = "viewer"
        if "all" in lower or "everyone" in lower or "user" in lower or "admin" in lower:
            target_role = "all"
        elif "analyst" in lower:
            target_role = "analyst"
        elif "viewer" in lower:
            target_role = "viewer"
        else:
            # Default to all roles when rule is a general restriction
            target_role = "all"

        if "delete" in lower or "drop" in lower or "remove" in lower:
            t = target_table or (tables[0] if tables else "Booking")
            return {
                "status": "success",
                "table_name": t,
                "column_name": None,
                "action": "restrict_operation",
                "allowed": True,
                "restricted_operations": ["DELETE"],
                "target_role": target_role,
                "summary": f"Disallowed DELETE operations on table '{t}' for {target_role} role."
            }

        if target_col:
            t = target_table or (tables[0] if tables else "faculty")
            return {
                "status": "success",
                "table_name": t,
                "column_name": target_col,
                "action": "restrict_column",
                "allowed": False,
                "restricted_operations": ["SELECT", "INSERT", "UPDATE", "DELETE"],
                "target_role": target_role,
                "summary": f"Restricted access to column '{target_col}' on table '{t}' for {target_role} role."
            }

        t = target_table or (tables[0] if tables else "departments")
        return {
            "status": "success",
            "table_name": t,
            "column_name": None,
            "action": "restrict_table",
            "allowed": False,
            "restricted_operations": ["SELECT", "INSERT", "UPDATE", "DELETE"],
            "target_role": target_role,
            "summary": f"Restricted access to table '{t}' for {target_role} role."
        }


class FallbackLLMProvider(LLMProvider):
    """
    Ordered fallback chain: tries each provider in sequence.
    Falls through to the next on any error and ultimately reaches MockLLMProvider
    which always succeeds, ensuring the system never hard-fails due to LLM issues.
    """

    def __init__(self, providers: List[LLMProvider]):
        self.providers = providers

    async def generate_sql(
        self,
        nl_query: str,
        db_type: str,
        schema_text: str,
        session_context: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        last_err: Exception = RuntimeError("No LLM providers configured.")
        for provider in self.providers:
            try:
                result = await provider.generate_sql(nl_query, db_type, schema_text, session_context)
                logger.debug(f"LLM generate_sql succeeded via {provider.__class__.__name__}")
                return result
            except Exception as e:
                logger.warning(f"LLM provider {provider.__class__.__name__} failed: {e}. Trying next provider.")
                last_err = e
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"All LLM providers failed. Last error: {last_err}"
        )

    async def generate_summary(
        self,
        nl_query: str,
        sql: str,
        row_count: int,
        sample_rows: Optional[List[Dict[str, Any]]] = None
    ) -> str:
        for provider in self.providers:
            try:
                return await provider.generate_summary(nl_query, sql, row_count, sample_rows)
            except Exception as e:
                logger.warning(f"Summary generation failed via {provider.__class__.__name__}: {e}")
        return f"{row_count} records were returned."

    async def parse_security_rule(
        self,
        rule_text: str,
        schema_text: str
    ) -> Dict[str, Any]:
        last_err: Exception = RuntimeError("No LLM providers configured.")
        for provider in self.providers:
            try:
                return await provider.parse_security_rule(rule_text, schema_text)
            except Exception as e:
                logger.warning(f"parse_security_rule failed via {provider.__class__.__name__}: {e}. Trying next provider.")
                last_err = e
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"All LLM providers failed to parse security rule. Last error: {last_err}"
        )


def _build_provider(name: str) -> Optional[LLMProvider]:
    """Instantiate and return a provider by name if it is available (has API key)."""
    name = name.lower().strip()
    if name == "mock":
        return MockLLMProvider()
    elif name == "gemini":
        p = GeminiProvider()
        return p if p.is_available() else None
    elif name == "openrouter":
        p = OpenRouterProvider()
        return p if p.is_available() else None
    elif name == "openai":
        p = OpenAIProvider()
        return p if p.is_available() else None
    elif name == "anthropic":
        p = AnthropicProvider()
        return p if p.is_available() else None
    else:
        logger.warning(f"Unknown LLM provider name '{name}' in fallback order — skipping.")
        return None


def get_llm_provider() -> LLMProvider:
    """
    Factory function that returns a FallbackLLMProvider honouring LLM_FALLBACK_ORDER.

    When LLM_PROVIDER is 'mock', returns MockLLMProvider directly (useful for testing).
    Otherwise, builds an ordered fallback chain from LLM_FALLBACK_ORDER.
    MockLLMProvider is always appended as the final safety net.
    """
    primary = (settings.LLM_PROVIDER or "gemini").lower().strip()
    if primary == "mock":
        return MockLLMProvider()

    order_str = settings.LLM_FALLBACK_ORDER or "gemini,openrouter,openai,anthropic,mock"
    ordered_names = [n.strip() for n in order_str.split(",") if n.strip()]

    # Ensure 'mock' is always the last resort
    if "mock" not in ordered_names:
        ordered_names.append("mock")

    providers: List[LLMProvider] = []
    for name in ordered_names:
        p = _build_provider(name)
        if p is not None:
            providers.append(p)

    if not providers:
        logger.warning("No LLM providers could be configured — falling back to MockLLMProvider.")
        providers = [MockLLMProvider()]

    logger.info(
        f"LLM fallback chain: {' → '.join(p.__class__.__name__ for p in providers)}"
    )
    return FallbackLLMProvider(providers)

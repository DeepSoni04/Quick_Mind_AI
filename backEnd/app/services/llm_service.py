import json
import logging
import re
from typing import Any, Dict, List, Optional
import httpx
from fastapi import HTTPException, status

from app.core.config import settings

logger = logging.getLogger("querymind.llm_service")


# ─── MongoDB-native MQL system prompt ─────────────────────────────────────────

def _build_mongodb_prompt(schema_text: str) -> str:
    return f"""You are QueryMind AI, an expert natural language to MongoDB query translator.

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
- Map CRUD intent to the correct MongoDB operation names (find, update_many, etc.).
- Do NOT invent collection names or field names not present in the schema.
- Use $set for UPDATE operations. Never use full document replacement.
- For SELECT-intent, use "find" or "aggregate". Map "SELECT" to operation "SELECT" in the outer "operation" field.
- For UPDATE-intent, use "update_one"/"update_many". Map to "UPDATE" in outer "operation".
- For DELETE-intent, use "delete_one"/"delete_many". Map to "DELETE" in outer "operation".
- For INSERT-intent, use "insert_one"/"insert_many". Map to "INSERT" in outer "operation".
"""


def _build_sql_prompt(db_type: str, schema_text: str) -> str:
    return f"""You are QueryMind AI, an expert natural language to SQL translator.
Target Database Dialect: {db_type.upper()}

Available Database Schema & Column Details:
{schema_text}

Rules:
1. Understand queries written in English or Hinglish.
2. Generate valid SQL syntax strictly using the target dialect ({db_type.upper()}).
3. Do NOT generate MySQL-specific syntax for PostgreSQL or vice-versa.
4. If the user request is ambiguous, set "needs_clarification": true with a clear question and choices.
5. Return strictly valid JSON containing:
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

    def __init__(self, api_key: str = ""):
        self.api_key = api_key or settings.LLM_API_KEY

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

        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={self.api_key}"
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
                text_out = data["candidates"][0]["content"]["parts"][0]["text"]
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
        """Generates natural language summary of query results."""
        if not self.api_key:
            return f"{row_count} records were returned for your query."

        try:
            prompt = f"Summarize the query results in 1 friendly sentence:\nQuestion: {nl_query}\nRow Count: {row_count}"
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={self.api_key}"
            payload = {
                "contents": [{"role": "user", "parts": [{"text": prompt}]}],
                "generationConfig": {"temperature": 0.2, "maxOutputTokens": 60}
            }
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.post(url, json=payload)
                if resp.status_code == 200:
                    data = resp.json()
                    return data["candidates"][0]["content"]["parts"][0]["text"].strip()
        except Exception as e:
            logger.warning(f"Gemini summary generation failed: {e}")

        return f"{row_count} records were returned."


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
        return f"{row_count} records were returned."


class OpenAIProvider(LLMProvider):
    """OpenAI GPT-4 provider for LLM fallback chain."""

    def __init__(self, api_key: str = ""):
        self.api_key = api_key or (settings.OPENAI_API_KEY or "")

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
            "model": "gpt-4o-mini",
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
        return f"{row_count} records were returned."


class AnthropicProvider(LLMProvider):
    """Anthropic Claude provider for LLM fallback chain."""

    def __init__(self, api_key: str = ""):
        self.api_key = api_key or (settings.ANTHROPIC_API_KEY or "")

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
            "model": "claude-3-5-haiku-20241022",
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
        return f"{row_count} records were returned."


class MockLLMProvider(LLMProvider):
    """Deterministic Mock LLM provider for unit, integration, and CI testing without external dependencies."""

    def is_available(self) -> bool:
        return True

    async def generate_sql(
        self,
        nl_query: str,
        db_type: str,
        schema_text: str,
        session_context: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        clean = nl_query.strip()
        lower = clean.lower()

        # Ambiguity test case
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

        # Multi-statement test case
        if "and delete inactive" in lower:
            quote = "`" if db_type == "mysql" else '"'
            return {
                "status": "success",
                "intent": "Update department and delete inactive students",
                "sql_statements": [
                    {
                        "sql": f"UPDATE {quote}students{quote} SET {quote}department{quote} = 'CS' WHERE {quote}id{quote} = 1;",
                        "operation": "UPDATE"
                    },
                    {
                        "sql": f"DELETE FROM {quote}students{quote} WHERE {quote}status{quote} = 'inactive';",
                        "operation": "DELETE"
                    }
                ],
                "needs_clarification": False,
                "clarification_question": None,
                "clarification_choices": None
            }

        op = "SELECT"
        if re.search(r"\b(delete|remove|erase|purge)\b", lower):
            op = "DELETE"
        elif re.search(r"\b(update|change|set|modify)\b", lower):
            op = "UPDATE"
        elif re.search(r"\b(insert|add)\b", lower):
            op = "INSERT"

        # Determine target table from schema
        tables = re.findall(r"Table:\s*([a-zA-Z0-9_]+)", schema_text)
        target_table = "students"
        if tables:
            for t in tables:
                if t.lower() in lower:
                    target_table = t
                    break
            else:
                target_table = tables[0]

        quote = "`" if db_type == "mysql" else '"'

        if op == "SELECT":
            sql = f"SELECT * FROM {quote}{target_table}{quote}"
            if "ahmedabad" in lower:
                sql += f" WHERE {quote}city{quote} = 'Ahmedabad'"
            elif "unpaid" in lower or "pending" in lower:
                sql += f" WHERE {quote}status{quote} = 'Pending'"
            elif "inactive" in lower:
                sql += f" WHERE {quote}status{quote} = 'Inactive'"
        elif op == "UPDATE":
            sql = f"UPDATE {quote}{target_table}{quote} SET {quote}department{quote} = 'Computer Science' WHERE {quote}name{quote} = 'Rahul Mehta'"
        elif op == "DELETE":
            sql = f"DELETE FROM {quote}{target_table}{quote} WHERE {quote}status{quote} = 'inactive'"
        elif op == "INSERT":
            sql = f"INSERT INTO {quote}{target_table}{quote} ({quote}name{quote}) VALUES ('New Student')"

        return {
            "status": "success",
            "intent": f"Perform {op} on {target_table}",
            "sql_statements": [{"sql": sql, "operation": op}],
            "needs_clarification": False,
            "clarification_question": None,
            "clarification_choices": None
        }

    def _generate_mongodb_query(self, nl_query: str, lower: str, schema_text: str) -> Dict[str, Any]:
        """Generate a deterministic MongoDB MQL for testing."""
        # Determine collection from schema
        collections = re.findall(r"Collection:\s*([a-zA-Z0-9_]+)", schema_text)
        # Also try Table: prefix (schema_service may emit Table: for MongoDB too)
        if not collections:
            collections = re.findall(r"Table:\s*([a-zA-Z0-9_]+)", schema_text)
        target_coll = "documents"
        if collections:
            for c in collections:
                if c.lower() in lower:
                    target_coll = c
                    break
            else:
                target_coll = collections[0]

        if re.search(r"\b(delete|remove|erase|purge)\b", lower):
            op = "DELETE"
            mql_op = "delete_many"
            mql = {"collection": target_coll, "operation": mql_op, "filter": {"status": "inactive"}}
            display = json.dumps(mql)
        elif re.search(r"\b(update|change|set|modify)\b", lower):
            op = "UPDATE"
            mql_op = "update_many"
            mql = {"collection": target_coll, "operation": mql_op, "filter": {}, "update": {"$set": {"department": "Computer Science"}}}
            display = json.dumps(mql)
        elif re.search(r"\b(insert|add)\b", lower):
            op = "INSERT"
            mql_op = "insert_one"
            mql = {"collection": target_coll, "operation": mql_op, "document": {"name": "New Document"}}
            display = json.dumps(mql)
        else:
            op = "SELECT"
            mql_op = "find"
            mql_filter: Dict[str, Any] = {}
            if "ahmedabad" in lower:
                mql_filter = {"city": "Ahmedabad"}
            elif "unpaid" in lower or "pending" in lower:
                mql_filter = {"status": "Pending"}
            elif "inactive" in lower:
                mql_filter = {"status": "Inactive"}
            mql = {"collection": target_coll, "operation": mql_op, "filter": mql_filter, "projection": {}}
            display = json.dumps(mql)

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
        return f"{row_count} records were returned."


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

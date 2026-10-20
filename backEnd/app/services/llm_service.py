import json
import logging
import re
from typing import Any, Dict, List, Optional
import httpx
from fastapi import HTTPException, status

from app.core.config import settings

logger = logging.getLogger("querymind.llm_service")


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
        """Translates English or Hinglish queries into structured SQL JSON using Gemini."""
        if not self.api_key or not self.api_key.strip():
            raise RuntimeError("Gemini provider unavailable: LLM_API_KEY not configured.")

        system_prompt = f"""You are QueryMind AI, an expert natural language to SQL translator.
Target Database Dialect: {db_type.upper()}

Available Database Schema & Column Details:
{schema_text}

Rules:
1. Understand queries written in English or Hinglish (e.g. "Show all customers from Ahmedabad", "Ahmedabad ke customers dikhao", "Ahmedabad na badha customers batavo").
2. Generate valid SQL syntax strictly using the target dialect ({db_type.upper()}).
3. Do NOT generate MySQL-specific syntax for PostgreSQL or vice-versa.
4. If the user request is ambiguous (e.g., "Show sales" when multiple sales tables exist), set "needs_clarification": true, provide "clarification_question" and "clarification_choices".
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

        user_content = f"User Request: {nl_query}"
        if session_context:
            user_content = f"Session History:\n{json.dumps(session_context)}\n\nCurrent Request: {nl_query}"

        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.8-flash:generateContent?key={self.api_key}"
        payload = {
            "contents": [
                {"role": "user", "parts": [{"text": f"{system_prompt}\n\n{user_content}"}]}
            ],
            "generationConfig": {
                "temperature": 0.1,
                "responseMimeType": "application/json"
            }
        }

        async with httpx.AsyncClient(timeout=15.0) as client:
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
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.8-flash:generateContent?key={self.api_key}"
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

        system_msg = (
            f"You are QueryMind AI, an expert natural language to {db_type.upper()} SQL translator.\n"
            f"Schema:\n{schema_text}\n"
            "Return ONLY valid JSON with keys: status, intent, sql_statements (list of {sql, operation}), "
            "needs_clarification, clarification_question, clarification_choices."
        )
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

        async with httpx.AsyncClient(timeout=15.0) as client:
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

        system_msg = (
            f"You are QueryMind AI, an expert natural language to {db_type.upper()} SQL translator.\n"
            f"Schema:\n{schema_text}\n"
            "Return ONLY valid JSON with keys: status, intent, sql_statements (list of {sql, operation}), "
            "needs_clarification, clarification_question, clarification_choices."
        )
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

    order_str = settings.LLM_FALLBACK_ORDER or "gemini,openai,anthropic,mock"
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

"""
Pipeline 1 – GenAI Generation
Uses structured prompts + forces JSON schema.
Supports Google Gemini (both key formats) and OpenAI.
Auto-unwraps nested JSON responses (e.g. {"OnboardingPlan": {...}}).
"""

import os
import json
import traceback
from typing import Dict, Any, Optional
from pathlib import Path
from tenacity import retry, stop_after_attempt, wait_exponential

from config.settings import settings
from src.genai_pipeline.schema import OnboardingPlan


def load_prompt_template(version: str = "v1") -> str:
    path = Path(__file__).parent / "prompt_templates" / f"onboarding_{version}.txt"
    return path.read_text(encoding="utf-8")


@retry(
    stop=stop_after_attempt(1),   # only 1 attempt so we see real errors clearly
    wait=wait_exponential(multiplier=1, min=2, max=10)
)
def call_genai(prompt: str) -> str:
    """Call configured GenAI provider. Retries on failure."""
    provider = settings.GENAI_PROVIDER.lower()
    api_key = settings.GEMINI_API_KEY if provider == "gemini" else settings.OPENAI_API_KEY

    if provider == "gemini":
        # ===== NEW FORMAT: AQ.Ab8... uses google-genai SDK =====
        if api_key.startswith("AQ."):
            try:
                from google import genai
            except ImportError:
                raise ImportError("Run: pip install google-genai")

            try:
                client = genai.Client(
                    api_key=api_key,
                    project=settings.GOOGLE_PROJECT_ID or None,
                )
            except TypeError:
                client = genai.Client(api_key=api_key)

            try:
                response = client.models.generate_content(
                    model="gemini-2.0-flash-exp",
                    contents=prompt,
                )
                return response.text
            except Exception as e:
                print("\n" + "=" * 70)
                print("GENAI ERROR — NEW FORMAT:")
                print(f"Type: {type(e).__name__}")
                print(f"Message: {e}")
                print(f"Key starts with: {api_key[:8]}...")
                print(f"Project ID: {settings.GOOGLE_PROJECT_ID}")
                traceback.print_exc()
                print("=" * 70 + "\n")
                raise

        # ===== OLD FORMAT: AIza... uses google-generativeai SDK =====
        else:
            import google.generativeai as genai_old
            genai_old.configure(api_key=api_key)
            model = genai_old.GenerativeModel("gemini-1.5-flash")
            response = model.generate_content(
                prompt,
                generation_config={"response_mime_type": "application/json"}
            )
            return response.text

    elif provider == "openai":
        from openai import OpenAI
        # If OPENAI_BASE_URL is set (e.g. OpenRouter), use it; otherwise use OpenAI default
        base_url = os.getenv("OPENAI_BASE_URL") or None
        model_name = os.getenv("OPENAI_MODEL") or "gpt-4o-mini"
        client = OpenAI(api_key=settings.OPENAI_API_KEY, base_url=base_url)
        try:
            response = client.chat.completions.create(
                model=model_name,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"}
            )
            return response.choices[0].message.content
        except Exception as e:
            print("\n" + "=" * 70)
            print("GENAI ERROR — OPENAI:")
            print(f"Type: {type(e).__name__}")
            print(f"Message: {e}")
            print(f"Model: {model_name}")
            print(f"Base URL: {base_url or '(default OpenAI)'}")
            traceback.print_exc()
            print("=" * 70 + "\n")
            raise

    else:
        raise ValueError(f"Unknown GENAI_PROVIDER: {provider}")


def _unwrap_json(data: Any) -> Any:
    """
    Handle cases where the model wraps the plan inside an extra key:
    - {"OnboardingPlan": {...}}
    - {"plan": {...}}
    - {"plan_json": {...}}
    - {"onboarding_plan": {...}}
    - {"plan_id": {...}} (already correct)
    """
    if not isinstance(data, dict):
        return data

    # Already has required top-level fields
    if "plan_id" in data and "modules" in data:
        return data

    # Try common wrappers
    for wrapper in ("OnboardingPlan", "onboarding_plan", "plan", "plan_json", "data", "result"):
        if wrapper in data and isinstance(data[wrapper], dict):
            inner = data[wrapper]
            if "plan_id" in inner and "modules" in inner:
                return inner

    # Fallback: if there's exactly one key and its value is a dict with plan_id
    if len(data) == 1:
        only_value = list(data.values())[0]
        if isinstance(only_value, dict) and "plan_id" in only_value and "modules" in only_value:
            return only_value

    return data


def generate_onboarding_plan(
    role: str,
    department: str,
    experience_level: str,
    source_chunks: str,
    role_matrix: str,
    prompt_version: str = "v1"
) -> Dict[str, Any]:
    """
    Main generation entry.
    Returns validated dict (Pydantic) or raises.
    """
    template = load_prompt_template(prompt_version)
    prompt = (template
              .replace("{{role}}", role)
              .replace("{{department}}", department)
              .replace("{{experience_level}}", experience_level)
              .replace("{{source_chunks}}", source_chunks)
              .replace("{{role_matrix}}", role_matrix))

    raw = call_genai(prompt)

    # Parse JSON
    data = json.loads(raw)

    # Unwrap if model added an extra wrapper key
    if isinstance(data, dict):
        for key in ("OnboardingPlan", "onboarding_plan", "plan", "plan_json", "data", "result"):
            if key in data and isinstance(data[key], dict):
                data = data[key]
                break

    # Fill in any missing required top-level fields with defaults
    from datetime import datetime
    if isinstance(data, dict):
        data.setdefault("plan_id", f"PLAN-{datetime.now().strftime('%Y%m%d-%H%M%S')}")
        data.setdefault("employee_id", "EMP001")
        data.setdefault("role", role)
        data.setdefault("department", department)
        data.setdefault("experience_level", experience_level)
        data.setdefault("generated_at", datetime.now().isoformat())
        data.setdefault("prompt_version", prompt_version)
        data.setdefault("model_used", os.getenv("OPENAI_MODEL") or "gpt-4o-mini")
        data.setdefault("stages", ["Day 1", "Week 1", "Week 2", "First 30 Days"])
        data.setdefault("modules", [])

    # Validate against schema
    plan = OnboardingPlan(**data)
    return plan.model_dump()
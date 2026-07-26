import json
import re
import time
from typing import Dict, Any, Optional
from groq import Groq

from config import GROQ_API_KEY
from ai.decision_schema import Decision
from models.optimization_context import OptimizationContext


class LLMClient:

    def __init__(self):
        self.client = Groq(api_key=GROQ_API_KEY)
        self.model = "llama-3.3-70b-versatile"

    def _extract_json_str(self, text: str) -> str:
        text = text.strip()

        if text.startswith("```"):
            lines = text.splitlines()
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].startswith("```"):
                lines = lines[:-1]
            text = "\n".join(lines).strip()

        try:
            json.loads(text)
            return text
        except json.JSONDecodeError:
            pass

        match = re.search(r"(\{[\s\S]*\})", text)
        if match:
            return match.group(1).strip()

        return text

    def generate_decision_with_metadata(
        self,
        system_prompt: str,
        user_prompt: str,
        context: Optional[OptimizationContext] = None
    ) -> Dict[str, Any]:

        start_time = time.perf_counter()

        response = self.client.chat.completions.create(
            model=self.model,
            temperature=0.2,
            messages=[
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": user_prompt
                }
            ]
        )

        elapsed_ms = int((time.perf_counter() - start_time) * 1000)
        content = response.choices[0].message.content.strip()

        cleaned_json_str = self._extract_json_str(content)

        try:
            data = json.loads(cleaned_json_str)
        except json.JSONDecodeError:
            raise ValueError(f"LLM returned invalid JSON:\n{content}")



        decision = Decision.model_validate(data)

        usage_dict = {}
        if hasattr(response, "usage") and response.usage:
            usage_dict = {
                "prompt_tokens": getattr(response.usage, "prompt_tokens", None),
                "completion_tokens": getattr(response.usage, "completion_tokens", None),
                "total_tokens": getattr(response.usage, "total_tokens", None),
            }
            usage_dict = {k: v for k, v in usage_dict.items() if v is not None}

        return {
            "decision": decision,
            "raw_content": content,
            "response_time_ms": elapsed_ms,
            "model": self.model,
            "usage": usage_dict,
        }

    def generate_decision(self, system_prompt: str, user_prompt: str, context: Optional[OptimizationContext] = None) -> Decision:
        result = self.generate_decision_with_metadata(system_prompt, user_prompt, context)
        return result["decision"]
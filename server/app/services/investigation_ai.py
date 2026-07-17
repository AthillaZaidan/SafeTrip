from __future__ import annotations

import json
import os
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import httpx
from dotenv import dotenv_values
from pydantic import BaseModel, Field, ValidationError

from ..schemas.investigations import VLMResult
from ..schemas.reports import SearchAttributes


# Leave headroom for the prompt and JSON schema under Gemini's 20 MB request limit.
MAX_INLINE_VIDEO_BYTES = 19_000_000
DEFAULT_GEMINI_MODEL = "gemini-3.1-flash-lite"
DEFAULT_OLLAMA_BASE_URL = "http://127.0.0.1:11434"
DEFAULT_OLLAMA_REPORT_MODEL = "qwen3:4b-instruct"
DEFAULT_ENV_FILE = Path(__file__).resolve().parents[3] / ".env"


class OllamaReportExtraction(BaseModel):
    location: str = Field(default="", description="Explicit station location.")
    upper_clothing: str = Field(
        default="", description="Explicit upper clothing including color."
    )
    lower_clothing: str = Field(
        default="", description="Explicit lower clothing including color."
    )
    direction: str = Field(
        default="",
        description="Explicit movement direction and destination, such as menuju Exit D.",
    )
    event: str = Field(
        default="", description="Explicit action, such as berjalan or berlari."
    )
    accessories: list[str] = Field(
        default_factory=list,
        description="All explicit bags, backpacks, and carried accessories.",
    )


class InvestigationAI:
    def __init__(
        self,
        client: Any = None,
        env: Mapping[str, str] | None = None,
        model: str | None = None,
        env_file: str | Path | None = DEFAULT_ENV_FILE,
        http_client: httpx.Client | None = None,
    ):
        self._client = client
        self._http_client = http_client
        if env is None:
            file_values = (
                {
                    key: value
                    for key, value in dotenv_values(env_file).items()
                    if value is not None
                }
                if env_file is not None
                else {}
            )
            self._env = {**file_values, **os.environ}
        else:
            self._env = env
        self.model = model or self._env.get("GEMINI_MODEL") or DEFAULT_GEMINI_MODEL
        self.report_provider = self._env.get("REPORT_LLM_PROVIDER", "gemini").lower()
        self.ollama_base_url = self._env.get(
            "OLLAMA_BASE_URL", DEFAULT_OLLAMA_BASE_URL
        ).rstrip("/")
        self.ollama_report_model = self._env.get(
            "OLLAMA_REPORT_MODEL", DEFAULT_OLLAMA_REPORT_MODEL
        )

    def extract_report(
        self,
        report: Any,
        cached_extraction: SearchAttributes | dict | None = None,
    ) -> tuple[SearchAttributes, str]:
        if self.report_provider == "ollama":
            try:
                attributes = self._extract_report_with_ollama(report)
                source = "ollama"
            except Exception:
                attributes, source = self._cached_or_fallback_extraction(
                    cached_extraction
                )
        else:
            client = self._get_client()
            if client is None:
                attributes, source = self._cached_or_fallback_extraction(
                    cached_extraction
                )
            else:
                try:
                    response = client.models.generate_content(
                        model=self.model,
                        contents=self._extraction_prompt(report),
                        config={
                            "response_mime_type": "application/json",
                            "response_schema": SearchAttributes,
                            "temperature": 0,
                        },
                    )
                    attributes = SearchAttributes.model_validate(response.parsed)
                    source = "gemini"
                except Exception:
                    attributes, source = self._cached_or_fallback_extraction(
                        cached_extraction
                    )

        overrides = {
            field: value
            for field in (
                "time_window_start",
                "time_window_end",
                "location",
                "direction",
            )
            if (value := getattr(report, field, None)) not in (None, "")
        }
        merged = SearchAttributes.model_validate(
            {**attributes.model_dump(), **overrides}
        )
        return merged, source

    def _extract_report_with_ollama(self, report: Any) -> SearchAttributes:
        client = self._http_client or httpx.Client(timeout=60.0)
        response = client.post(
            f"{self.ollama_base_url}/api/chat",
            json={
                "model": self.ollama_report_model,
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "Extract every explicitly stated CCTV search attribute. "
                            "Call submit_search_attributes exactly once. Do not "
                            "explain and do not infer identity."
                        ),
                    },
                    {
                        "role": "user",
                        "content": getattr(report, "description", ""),
                    },
                ],
                "stream": False,
                "tools": [
                    {
                        "type": "function",
                        "function": {
                            "name": "submit_search_attributes",
                            "description": "Submit extracted CCTV search attributes.",
                            "parameters": self._ollama_tool_schema(),
                        },
                    }
                ],
                "options": {"temperature": 0, "num_predict": 256},
            },
        )
        response.raise_for_status()
        merged_arguments: dict[str, Any] = {}
        for tool_call in response.json()["message"]["tool_calls"]:
            function = tool_call.get("function", {})
            if function.get("name") != "submit_search_attributes":
                continue
            arguments = function.get("arguments", {})
            if isinstance(arguments, str):
                arguments = json.loads(arguments)
            if isinstance(arguments, dict):
                merged_arguments.update(arguments)
        if not merged_arguments:
            raise ValueError("Ollama did not return search attributes.")
        extraction = OllamaReportExtraction.model_validate(merged_arguments)
        return SearchAttributes.model_validate(extraction.model_dump())

    @staticmethod
    def _ollama_tool_schema() -> dict[str, Any]:
        return OllamaReportExtraction.model_json_schema()

    def verify_clip(
        self,
        path: str | Path,
        attributes: SearchAttributes,
        cached_vlm: VLMResult | dict | None = None,
    ) -> VLMResult:
        video_path = Path(path)
        media_error = self._media_error(video_path)
        if media_error:
            return self._cached_or_fallback_vlm(cached_vlm, media_error)

        client = self._get_client()
        if client is None:
            return self._cached_or_fallback_vlm(
                cached_vlm,
                "Gemini credentials are not configured.",
            )

        try:
            response = client.models.generate_content(
                model=self.model,
                contents=[
                    {
                        "inline_data": {
                            "data": video_path.read_bytes(),
                            "mime_type": "video/mp4",
                        }
                    },
                    self._verification_prompt(attributes),
                ],
                config={
                    "response_mime_type": "application/json",
                    "response_schema": VLMResult,
                    "temperature": 0,
                },
            )
            result = VLMResult.model_validate(response.parsed)
            return result.model_copy(update={"source": "gemini"})
        except Exception as error:
            return self._cached_or_fallback_vlm(
                cached_vlm,
                f"Gemini verification failed: {type(error).__name__}.",
            )

    def _get_client(self):
        if self._client is not None:
            return self._client
        api_key = self._env.get("GOOGLE_API_KEY") or self._env.get("GEMINI_API_KEY")
        if not api_key:
            return None

        from google import genai

        self._client = genai.Client(api_key=api_key)
        return self._client

    @staticmethod
    def _cached_or_fallback_extraction(
        cached_extraction: SearchAttributes | dict | None,
    ) -> tuple[SearchAttributes, str]:
        if cached_extraction is not None:
            try:
                return SearchAttributes.model_validate(cached_extraction), "cached"
            except ValidationError:
                pass
        return SearchAttributes(), "fallback"

    @staticmethod
    def _cached_or_fallback_vlm(
        cached_vlm: VLMResult | dict | None,
        reason: str,
    ) -> VLMResult:
        if cached_vlm is not None:
            try:
                result = VLMResult.model_validate(cached_vlm)
                return result.model_copy(update={"source": "cached"})
            except ValidationError:
                reason = f"{reason} Cached verification is invalid."
        return VLMResult(
            supported_attributes=[],
            contradicted_attributes=[],
            uncertainties=[reason],
            match_recommendation="possible_match",
            source="fallback",
        )

    @staticmethod
    def _media_error(path: Path) -> str | None:
        if path.suffix.casefold() != ".mp4":
            return "Only MP4 video is supported."
        try:
            size = path.stat().st_size
        except OSError:
            return "Video file is unavailable."
        if size > MAX_INLINE_VIDEO_BYTES:
            return "Video exceeds the inline Gemini request limit."
        return None

    @staticmethod
    def _extraction_prompt(report: Any) -> str:
        return (
            "Extract only observable search attributes from this CCTV incident "
            "report. Fill every field supported by the report. Map shirts, jackets, "
            "and tops (baju, kemeja, jaket) to upper_clothing; trousers, pants, and "
            "skirts (celana, rok) to lower_clothing; backpacks and bags (ransel, "
            "tas) to accessories; and walking or running actions to event. Preserve "
            "stated colors and movement direction. Leave unknown fields empty and "
            "do not infer identity.\n\n"
            f"Report: {getattr(report, 'description', '')}"
        )

    @staticmethod
    def _verification_prompt(attributes: SearchAttributes) -> str:
        return (
            "Compare the person and movement visible in this clip with the search "
            "attributes below. Report support, contradictions, uncertainty, and "
            "the relevant time range. Do not identify the person.\n\n"
            f"Search attributes: {attributes.model_dump_json()}"
        )

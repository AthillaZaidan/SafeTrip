from __future__ import annotations

import os
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from dotenv import dotenv_values
from pydantic import ValidationError

from ..schemas.investigations import VLMResult
from ..schemas.reports import SearchAttributes


# Leave headroom for the prompt and JSON schema under Gemini's 20 MB request limit.
MAX_INLINE_VIDEO_BYTES = 19_000_000
DEFAULT_GEMINI_MODEL = "gemini-3.1-flash-lite"
DEFAULT_ENV_FILE = Path(__file__).resolve().parents[3] / ".env"


class InvestigationAI:
    def __init__(
        self,
        client: Any = None,
        env: Mapping[str, str] | None = None,
        model: str | None = None,
        env_file: str | Path | None = DEFAULT_ENV_FILE,
    ):
        self._client = client
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

    def extract_report(
        self,
        report: Any,
        cached_extraction: SearchAttributes | dict | None = None,
    ) -> tuple[SearchAttributes, str]:
        client = self._get_client()
        if client is None:
            attributes, source = self._cached_or_fallback_extraction(cached_extraction)
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
            "report. Leave unknown fields empty and do not infer identity.\n\n"
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

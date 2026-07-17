import datetime
import json
from types import SimpleNamespace

import httpx

from server.app.schemas.investigations import VLMResult
from server.app.schemas.reports import SearchAttributes
from server.app.services.investigation_ai import InvestigationAI


JAKARTA = datetime.timezone(datetime.timedelta(hours=7))


class FakeModels:
    def __init__(self, parsed=None, error=None):
        self.parsed = parsed
        self.error = error
        self.calls = []

    def generate_content(self, **kwargs):
        self.calls.append(kwargs)
        if self.error:
            raise self.error
        return SimpleNamespace(parsed=self.parsed)


class FakeClient:
    def __init__(self, parsed=None, error=None):
        self.models = FakeModels(parsed=parsed, error=error)


def _report(**overrides):
    values = {
        "description": "Orang berjaket abu-abu dan tas hitam berlari menuju Exit D.",
        "time_window_start": None,
        "time_window_end": None,
        "location": "",
        "direction": "",
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def _cached_extraction():
    return {
        "time_window_start": "2026-07-17T17:05:00+07:00",
        "time_window_end": "2026-07-17T17:15:00+07:00",
        "location": "Stasiun Tanah Abang",
        "upper_clothing": "grey jacket",
        "lower_clothing": "dark trousers",
        "accessories": ["black backpack"],
        "direction": "toward Exit D",
        "event": "running",
    }


def _cached_vlm():
    return {
        "supported_attributes": ["grey jacket", "black backpack"],
        "contradicted_attributes": [],
        "uncertainties": ["face is unclear"],
        "relevant_start_seconds": 1.0,
        "relevant_end_seconds": 6.0,
        "match_recommendation": "likely_match",
        "source": "cached",
    }


def test_default_model_uses_cost_efficient_flash_lite():
    assert InvestigationAI(env={}).model == "gemini-3.1-flash-lite"


def test_env_file_is_loaded_and_shell_environment_wins(tmp_path, monkeypatch):
    env_file = tmp_path / ".env"
    env_file.write_text(
        "GEMINI_API_KEY=file-key\nGEMINI_MODEL=model-from-file\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("GEMINI_MODEL", "model-from-shell")

    ai = InvestigationAI(env_file=env_file)

    assert ai._env["GEMINI_API_KEY"] == "file-key"
    assert ai.model == "model-from-shell"


def test_live_extraction_validates_output_and_explicit_fields_win():
    parsed = {
        **_cached_extraction(),
        "location": "Wrong model location",
        "direction": "away from Exit D",
    }
    client = FakeClient(parsed=parsed)
    start = datetime.datetime(2026, 7, 17, 17, 8, tzinfo=JAKARTA)
    end = datetime.datetime(2026, 7, 17, 17, 12, tzinfo=JAKARTA)
    report = _report(
        time_window_start=start,
        time_window_end=end,
        location="Lantai 1 Concourse",
        direction="toward Exit D",
    )

    attributes, source = InvestigationAI(
        client=client,
        env={"GEMINI_MODEL": "gemini-test"},
    ).extract_report(report)

    assert source == "gemini"
    assert isinstance(attributes, SearchAttributes)
    assert attributes.time_window_start == start
    assert attributes.time_window_end == end
    assert attributes.location == "Lantai 1 Concourse"
    assert attributes.direction == "toward Exit D"
    assert attributes.upper_clothing == "grey jacket"
    call = client.models.calls[0]
    assert call["model"] == "gemini-test"
    assert call["config"]["response_schema"] is SearchAttributes


def test_ollama_extraction_uses_qwen_structured_output_and_explicit_fields_win():
    requests = []

    def handler(request: httpx.Request):
        requests.append(request)
        return httpx.Response(
            200,
            json={
                "message": {
                    "role": "assistant",
                    "content": "",
                    "tool_calls": [
                        {
                            "function": {
                                "name": "submit_search_attributes",
                                "arguments": {
                                    **_cached_extraction(),
                                    "location": "Wrong model location",
                                    "direction": "away from Exit D",
                                },
                            }
                        }
                    ],
                }
            },
        )

    report = _report(
        location="Lantai 1 Concourse",
        direction="toward Exit D",
    )
    http_client = httpx.Client(transport=httpx.MockTransport(handler))

    attributes, source = InvestigationAI(
        env={
            "REPORT_LLM_PROVIDER": "ollama",
            "OLLAMA_BASE_URL": "http://ollama.test",
            "OLLAMA_REPORT_MODEL": "qwen3:4b-instruct",
        },
        http_client=http_client,
    ).extract_report(report)

    assert source == "ollama"
    assert attributes.location == "Lantai 1 Concourse"
    assert attributes.direction == "toward Exit D"
    assert attributes.upper_clothing == "grey jacket"
    payload = json.loads(requests[0].content)
    assert str(requests[0].url) == "http://ollama.test/api/chat"
    assert payload["model"] == "qwen3:4b-instruct"
    assert payload["stream"] is False
    tool = payload["tools"][0]["function"]
    assert tool["name"] == "submit_search_attributes"
    assert set(tool["parameters"]["properties"]) == {
        "location",
        "upper_clothing",
        "lower_clothing",
        "direction",
        "event",
        "accessories",
    }
    assert tool["parameters"]["properties"]["direction"]["description"]
    assert tool["parameters"]["properties"]["event"]["description"]
    assert payload["options"]["temperature"] == 0
    assert payload["options"]["num_predict"] == 256


def test_ollama_failure_uses_cached_extraction():
    def handler(_request: httpx.Request):
        return httpx.Response(503, json={"error": "model unavailable"})

    attributes, source = InvestigationAI(
        env={"REPORT_LLM_PROVIDER": "ollama"},
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
    ).extract_report(_report(), cached_extraction=_cached_extraction())

    assert source == "cached"
    assert attributes.upper_clothing == "grey jacket"


def test_ollama_extraction_merges_attributes_from_multiple_tool_calls():
    def handler(_request: httpx.Request):
        return httpx.Response(
            200,
            json={
                "message": {
                    "tool_calls": [
                        {
                            "function": {
                                "name": "submit_search_attributes",
                                "arguments": {
                                    "upper_clothing": "jaket abu-abu",
                                    "lower_clothing": "celana hitam",
                                    "accessories": ["tas ransel hitam"],
                                },
                            }
                        },
                        {
                            "function": {
                                "name": "submit_search_attributes",
                                "arguments": {
                                    "direction": "menuju Exit D",
                                    "event": "berjalan",
                                },
                            }
                        },
                    ]
                }
            },
        )

    attributes, source = InvestigationAI(
        env={"REPORT_LLM_PROVIDER": "ollama"},
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
    ).extract_report(_report(description="report", direction=""))

    assert source == "ollama"
    assert attributes.upper_clothing == "jaket abu-abu"
    assert attributes.lower_clothing == "celana hitam"
    assert attributes.accessories == ["tas ransel hitam"]
    assert attributes.direction == "menuju Exit D"
    assert attributes.event == "berjalan"


def test_extraction_prompt_explains_clothing_and_accessory_field_mapping():
    prompt = InvestigationAI._extraction_prompt(_report())

    assert "lower_clothing" in prompt
    assert "accessories" in prompt
    assert "backpack" in prompt
    assert "Fill every field supported by the report" in prompt


def test_missing_credentials_uses_cached_extraction():
    attributes, source = InvestigationAI(env={}).extract_report(
        _report(),
        cached_extraction=_cached_extraction(),
    )

    assert source == "cached"
    assert attributes.upper_clothing == "grey jacket"
    assert attributes.accessories == ["black backpack"]


def test_extraction_api_failure_uses_cache_and_keeps_explicit_override():
    client = FakeClient(error=RuntimeError("quota exceeded"))

    attributes, source = InvestigationAI(client=client, env={}).extract_report(
        _report(location="Lantai 2 Mezzanine"),
        cached_extraction=_cached_extraction(),
    )

    assert source == "cached"
    assert attributes.location == "Lantai 2 Mezzanine"


def test_live_video_verification_sends_inline_mp4_and_validates_result(tmp_path):
    video = tmp_path / "clip.mp4"
    video.write_bytes(b"fake-mp4")
    client = FakeClient(parsed=_cached_vlm())

    result = InvestigationAI(client=client, env={}).verify_clip(
        video,
        SearchAttributes(upper_clothing="grey jacket"),
    )

    assert isinstance(result, VLMResult)
    assert result.source == "gemini"
    call = client.models.calls[0]
    assert call["contents"][0]["inline_data"] == {
        "data": b"fake-mp4",
        "mime_type": "video/mp4",
    }
    assert call["config"]["response_schema"] is VLMResult


def test_missing_video_uses_cached_vlm_without_calling_gemini(tmp_path):
    client = FakeClient(parsed=_cached_vlm())

    result = InvestigationAI(client=client, env={}).verify_clip(
        tmp_path / "missing.mp4",
        SearchAttributes(),
        cached_vlm=_cached_vlm(),
    )

    assert result.source == "cached"
    assert result.match_recommendation == "likely_match"
    assert client.models.calls == []


def test_oversized_video_uses_cached_vlm(tmp_path, monkeypatch):
    video = tmp_path / "clip.mp4"
    video.write_bytes(b"four")
    monkeypatch.setattr(
        "server.app.services.investigation_ai.MAX_INLINE_VIDEO_BYTES",
        3,
    )

    result = InvestigationAI(client=FakeClient(), env={}).verify_clip(
        video,
        SearchAttributes(),
        cached_vlm=_cached_vlm(),
    )

    assert result.source == "cached"


def test_vlm_api_failure_uses_cached_result(tmp_path):
    video = tmp_path / "clip.mp4"
    video.write_bytes(b"fake-mp4")

    result = InvestigationAI(
        client=FakeClient(error=RuntimeError("timeout")),
        env={},
    ).verify_clip(video, SearchAttributes(), cached_vlm=_cached_vlm())

    assert result.source == "cached"


def test_no_cache_returns_honest_fallback_without_supported_attributes(tmp_path):
    result = InvestigationAI(env={}).verify_clip(
        tmp_path / "missing.mp4",
        SearchAttributes(upper_clothing="grey jacket"),
    )

    assert result.source == "fallback"
    assert result.match_recommendation == "possible_match"
    assert result.supported_attributes == []
    assert result.contradicted_attributes == []
    assert result.uncertainties

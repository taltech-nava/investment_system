from __future__ import annotations

import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

os.environ.setdefault("OPENAI_API_KEY", "test-key")
os.environ.setdefault("ANTHROPIC_API_KEY", "test-anthropic-key")
os.environ.setdefault("GEMINI_API_KEY", "test-gemini-key")
os.environ.setdefault("LLM_PROVIDER", "openai")
os.environ.setdefault("LLM_MODEL", "gpt-4o-mini")


def _make_broker(provider: str | None = None, model: str | None = None):  # noqa: ANN202
    from src.services.lm_broker import LMBroker

    return LMBroker(provider=provider, model=model)


def _mock_openai_completion(content: str) -> MagicMock:
    choice = MagicMock()
    choice.message.content = content
    response = MagicMock()
    response.choices = [choice]
    return response


def _mock_anthropic_completion(content: str) -> MagicMock:
    block = MagicMock()
    block.text = content
    response = MagicMock()
    response.content = [block]
    return response


class TestLMBrokerInit:
    def test_defaults_to_settings_provider(self) -> None:
        broker = _make_broker()
        assert broker.provider == "openai"

    def test_override_provider_at_init(self) -> None:
        broker = _make_broker(provider="ollama", model="llama3.2")
        assert broker.provider == "ollama"
        assert broker.default_model == "llama3.2"

    def test_override_model_at_init(self) -> None:
        broker = _make_broker(model="gpt-4o")
        assert broker.default_model == "gpt-4o"

    def test_raises_for_unsupported_provider(self) -> None:
        from src.services.lm_broker import LMBroker

        with pytest.raises(ValueError, match="Unsupported LLM provider"):
            LMBroker(provider="unknown")

    def test_openai_sets_openai_clients(self) -> None:
        from openai import AsyncOpenAI, OpenAI

        broker = _make_broker(provider="openai")
        assert isinstance(broker.client, OpenAI)
        assert isinstance(broker.async_client, AsyncOpenAI)

    def test_anthropic_sets_anthropic_clients(self) -> None:
        import anthropic

        broker = _make_broker(provider="anthropic", model="claude-haiku-4-5-20251001")
        assert isinstance(broker._anthropic_client, anthropic.Anthropic)
        assert isinstance(broker._anthropic_async_client, anthropic.AsyncAnthropic)
        assert broker.client is None

    def test_gemini_sets_openai_client_with_gemini_base_url(self) -> None:
        from src.services.lm_broker import _GEMINI_BASE_URL

        broker = _make_broker(provider="gemini", model="gemini-2.0-flash")
        assert broker.client.base_url.host == _GEMINI_BASE_URL.split("//")[1].split("/")[0]

    def test_ollama_sets_openai_client_with_local_base_url(self) -> None:
        broker = _make_broker(provider="ollama", model="llama3.2")
        assert "localhost" in str(broker.client.base_url)

    def test_runpod_sets_openai_client_with_runpod_base_url(self) -> None:
        with patch("src.services.lm_broker.settings") as mock_settings:
            mock_settings.llm.llm_provider = "runpod"
            mock_settings.llm.llm_model = "llama3.2"
            mock_settings.llm.runpod_pod_id = "abc123"
            from src.services.lm_broker import LMBroker

            broker = LMBroker(provider="runpod", model="llama3.2")
        assert "runpod.net" in str(broker.client.base_url)


class TestAskOpenAI:
    def test_returns_response_content(self) -> None:
        broker = _make_broker(provider="openai")
        broker.client = MagicMock()
        broker.client.chat.completions.create.return_value = _mock_openai_completion("result")

        assert broker.ask("system", "user", calling_module="test") == "result"

    def test_uses_default_model(self) -> None:
        broker = _make_broker(provider="openai")
        broker.client = MagicMock()
        broker.client.chat.completions.create.return_value = _mock_openai_completion("ok")

        broker.ask("system", "user", calling_module="test")

        assert broker.client.chat.completions.create.call_args[1]["model"] == broker.default_model

    def test_uses_override_model(self) -> None:
        broker = _make_broker(provider="openai")
        broker.client = MagicMock()
        broker.client.chat.completions.create.return_value = _mock_openai_completion("ok")

        broker.ask("system", "user", model="gpt-4o", calling_module="test")

        assert broker.client.chat.completions.create.call_args[1]["model"] == "gpt-4o"

    def test_returns_error_string_on_failure(self) -> None:
        broker = _make_broker(provider="openai")
        broker.client = MagicMock()
        broker.client.chat.completions.create.side_effect = Exception("API down")

        result = broker.ask("system", "user", calling_module="test")

        assert result.startswith("Error:")
        assert "API down" in result


class TestAskAnthropic:
    def test_returns_response_content(self) -> None:
        broker = _make_broker(provider="anthropic", model="claude-haiku-4-5-20251001")
        broker._anthropic_client = MagicMock()
        broker._anthropic_client.messages.create.return_value = _mock_anthropic_completion("claude reply")

        result = broker.ask("system", "user", calling_module="test")

        assert result == "claude reply"

    def test_passes_system_and_user_correctly(self) -> None:
        broker = _make_broker(provider="anthropic", model="claude-haiku-4-5-20251001")
        broker._anthropic_client = MagicMock()
        broker._anthropic_client.messages.create.return_value = _mock_anthropic_completion("ok")

        broker.ask("my system", "my user", calling_module="test")

        call_kwargs = broker._anthropic_client.messages.create.call_args[1]
        assert call_kwargs["system"] == "my system"
        assert call_kwargs["messages"][0]["content"] == "my user"

    def test_returns_error_string_on_failure(self) -> None:
        broker = _make_broker(provider="anthropic", model="claude-haiku-4-5-20251001")
        broker._anthropic_client = MagicMock()
        broker._anthropic_client.messages.create.side_effect = Exception("Anthropic error")

        result = broker.ask("system", "user", calling_module="test")

        assert result.startswith("Error:")


class TestAskGemini:
    def test_returns_response_content(self) -> None:
        broker = _make_broker(provider="gemini", model="gemini-2.0-flash")
        broker.client = MagicMock()
        broker.client.chat.completions.create.return_value = _mock_openai_completion("gemini reply")

        assert broker.ask("system", "user", calling_module="test") == "gemini reply"


class TestAskOllama:
    def test_returns_response_content(self) -> None:
        broker = _make_broker(provider="ollama", model="llama3.2")
        broker.client = MagicMock()
        broker.client.chat.completions.create.return_value = _mock_openai_completion("llama reply")

        assert broker.ask("system", "user", calling_module="test") == "llama reply"


class TestLogging:
    def test_logs_successful_call(self, caplog: pytest.LogCaptureFixture) -> None:
        import logging

        broker = _make_broker(provider="openai")
        broker.client = MagicMock()
        broker.client.chat.completions.create.return_value = _mock_openai_completion("ok")

        with caplog.at_level(logging.INFO, logger="src.services.lm_broker"):
            broker.ask("system prompt", "user prompt", calling_module="auditor")

        assert any("llm_call" in r.message and "auditor" in r.message for r in caplog.records)

    def test_log_includes_required_fields(self, caplog: pytest.LogCaptureFixture) -> None:
        import logging

        broker = _make_broker(provider="openai")
        broker.client = MagicMock()
        broker.client.chat.completions.create.return_value = _mock_openai_completion("ok")

        with caplog.at_level(logging.INFO, logger="src.services.lm_broker"):
            broker.ask("sys", "usr", calling_module="test")

        msg = next(r.message for r in caplog.records if "llm_call" in r.message)
        assert "prompt_len=" in msg
        assert "response_len=" in msg
        assert "latency=" in msg

    def test_logs_error_on_failure(self, caplog: pytest.LogCaptureFixture) -> None:
        import logging

        broker = _make_broker(provider="openai")
        broker.client = MagicMock()
        broker.client.chat.completions.create.side_effect = Exception("timeout")

        with caplog.at_level(logging.ERROR, logger="src.services.lm_broker"):
            broker.ask("system", "user", calling_module="test_module")

        assert any(
            "llm_call" in r.message and r.levelname == "ERROR" for r in caplog.records
        )

    def test_anthropic_call_also_logs(self, caplog: pytest.LogCaptureFixture) -> None:
        import logging

        broker = _make_broker(provider="anthropic", model="claude-haiku-4-5-20251001")
        broker._anthropic_client = MagicMock()
        broker._anthropic_client.messages.create.return_value = _mock_anthropic_completion("ok")

        with caplog.at_level(logging.INFO, logger="src.services.lm_broker"):
            broker.ask("system", "user", calling_module="auditor")

        assert any("llm_call" in r.message and "auditor" in r.message for r in caplog.records)


class TestAskBatch:
    async def test_returns_one_result_per_task(self) -> None:
        broker = _make_broker(provider="openai")
        broker.async_client = AsyncMock()
        broker.async_client.chat.completions.create.return_value = _mock_openai_completion("answer")

        results = await broker.ask_batch(["q1", "q2", "q3"], calling_module="test")

        assert len(results) == 3

    async def test_returns_error_string_when_task_fails(self) -> None:
        broker = _make_broker(provider="openai")
        broker.async_client = AsyncMock()
        broker.async_client.chat.completions.create.side_effect = Exception("fail")

        results = await broker.ask_batch(["q1"], calling_module="test")

        assert results[0].startswith("Error:")

    async def test_anthropic_batch_returns_results(self) -> None:
        broker = _make_broker(provider="anthropic", model="claude-haiku-4-5-20251001")
        broker._anthropic_async_client = AsyncMock()
        broker._anthropic_async_client.messages.create.return_value = _mock_anthropic_completion("ok")

        results = await broker.ask_batch(["q1", "q2"], calling_module="test")

        assert len(results) == 2
        assert all(r == "ok" for r in results)

    async def test_logs_each_call(self, caplog: pytest.LogCaptureFixture) -> None:
        import logging

        broker = _make_broker(provider="openai")
        broker.async_client = AsyncMock()
        broker.async_client.chat.completions.create.return_value = _mock_openai_completion("ok")

        with caplog.at_level(logging.INFO, logger="src.services.lm_broker"):
            await broker.ask_batch(["q1", "q2"], calling_module="extractor")

        llm_logs = [r for r in caplog.records if "llm_call" in r.message]
        assert len(llm_logs) == 2

    async def test_passes_calling_module_to_each_worker(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        import logging

        broker = _make_broker(provider="openai")
        broker.async_client = AsyncMock()
        broker.async_client.chat.completions.create.return_value = _mock_openai_completion("ok")

        with caplog.at_level(logging.INFO, logger="src.services.lm_broker"):
            await broker.ask_batch(["q1"], calling_module="auditor")

        assert any("auditor" in r.message for r in caplog.records if "llm_call" in r.message)

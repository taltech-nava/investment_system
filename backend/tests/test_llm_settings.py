from __future__ import annotations

import os


def _fresh_settings():  # noqa: ANN202
    from importlib import reload

    import config.llm as llm_module

    reload(llm_module)
    return llm_module.LLMSettings()


class TestLLMSettings:
    def test_defaults_to_openai_provider(self) -> None:
        os.environ.pop("LLM_PROVIDER", None)
        assert _fresh_settings().llm_provider == "openai"

    def test_defaults_to_gpt4o_mini(self) -> None:
        os.environ.pop("LLM_MODEL", None)
        assert _fresh_settings().llm_model == "gpt-4o-mini"

    def test_reads_provider_from_env(self) -> None:
        os.environ["LLM_PROVIDER"] = "runpod"
        assert _fresh_settings().llm_provider == "runpod"
        os.environ.pop("LLM_PROVIDER", None)

    def test_reads_model_from_env(self) -> None:
        os.environ["LLM_MODEL"] = "gpt-4o"
        assert _fresh_settings().llm_model == "gpt-4o"
        os.environ.pop("LLM_MODEL", None)

    def test_reads_api_key_from_env(self) -> None:
        os.environ["OPENAI_API_KEY"] = "sk-test-123"
        assert _fresh_settings().openai_api_key == "sk-test-123"

    def test_settings_singleton_exposes_llm(self) -> None:
        from config.settings import settings

        assert hasattr(settings, "llm")
        assert hasattr(settings.llm, "llm_provider")
        assert hasattr(settings.llm, "llm_model")
        assert hasattr(settings.llm, "openai_api_key")


class TestPerTaskSettings:
    def test_provider_for_returns_task_specific_provider(self) -> None:
        os.environ["LLM_PROVIDER_AUDIT"] = "ollama"
        s = _fresh_settings()
        assert s.provider_for("audit") == "ollama"
        os.environ.pop("LLM_PROVIDER_AUDIT", None)

    def test_model_for_returns_task_specific_model(self) -> None:
        os.environ["LLM_MODEL_AUDIT"] = "llama3.2"
        s = _fresh_settings()
        assert s.model_for("audit") == "llama3.2"
        os.environ.pop("LLM_MODEL_AUDIT", None)

    def test_provider_for_falls_back_to_global_when_task_not_set(self) -> None:
        os.environ.pop("LLM_PROVIDER_AUDIT", None)
        os.environ["LLM_PROVIDER"] = "openai"
        s = _fresh_settings()
        assert s.provider_for("audit") == "openai"

    def test_model_for_falls_back_to_global_when_task_not_set(self) -> None:
        os.environ.pop("LLM_MODEL_AUDIT", None)
        os.environ["LLM_MODEL"] = "gpt-4o-mini"
        s = _fresh_settings()
        assert s.model_for("audit") == "gpt-4o-mini"

    def test_provider_for_extraction_independent_from_audit(self) -> None:
        os.environ["LLM_PROVIDER_AUDIT"] = "ollama"
        os.environ["LLM_PROVIDER_EXTRACTION"] = "anthropic"
        s = _fresh_settings()
        assert s.provider_for("audit") == "ollama"
        assert s.provider_for("extraction") == "anthropic"
        os.environ.pop("LLM_PROVIDER_AUDIT", None)
        os.environ.pop("LLM_PROVIDER_EXTRACTION", None)

    def test_provider_for_unknown_task_falls_back_to_global(self) -> None:
        os.environ["LLM_PROVIDER"] = "gemini"
        s = _fresh_settings()
        assert s.provider_for("unknown_task") == "gemini"


class TestBrokerFor:
    def test_returns_broker_with_task_provider(self) -> None:
        os.environ["LLM_PROVIDER_AUDIT"] = "openai"
        os.environ["LLM_MODEL_AUDIT"] = "gpt-4o-mini"
        from importlib import reload

        import src.services.lm_broker as broker_module

        reload(broker_module)
        broker = broker_module.broker_for("audit")
        assert broker.provider == "openai"
        assert broker.default_model == "gpt-4o-mini"

    def test_returns_broker_with_global_fallback(self) -> None:
        os.environ.pop("LLM_PROVIDER_AUDIT", None)
        os.environ.pop("LLM_MODEL_AUDIT", None)
        os.environ["LLM_PROVIDER"] = "openai"
        os.environ["LLM_MODEL"] = "gpt-4o-mini"
        from importlib import reload

        import src.services.lm_broker as broker_module

        reload(broker_module)
        broker = broker_module.broker_for("audit")
        assert broker.provider == "openai"

    def test_different_tasks_can_use_different_providers(self) -> None:
        from unittest.mock import MagicMock, patch

        from src.services.lm_broker import broker_for

        mock_llm = MagicMock()
        mock_llm.provider_for.side_effect = lambda t: {"audit": "openai", "extraction": "openai"}[t]
        mock_llm.model_for.side_effect = lambda t: {"audit": "gpt-4o-mini", "extraction": "gpt-4o"}[t]
        mock_llm.openai_api_key = "test-key"

        with patch("src.services.lm_broker.settings") as mock_settings:
            mock_settings.llm = mock_llm
            audit_broker = broker_for("audit")
            extraction_broker = broker_for("extraction")

        assert audit_broker.default_model == "gpt-4o-mini"
        assert extraction_broker.default_model == "gpt-4o"

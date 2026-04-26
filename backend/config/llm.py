from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

_ENV_FILE = Path(__file__).parent.parent.parent / ".env"


class LLMSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=_ENV_FILE, extra="ignore")

    # Fallback defaults — used when a task has no explicit provider/model set
    llm_provider: str = "openai"
    llm_model: str = "gpt-4o-mini"

    # Per-task provider and model
    # Audit: PDF quality classification (SLM-suitable — fast, cheap, repetitive)
    llm_provider_audit: str = ""
    llm_model_audit: str = ""

    # Extraction: price target extraction from research documents (LLM-quality task)
    llm_provider_extraction: str = ""
    llm_model_extraction: str = ""

    # Provider API keys
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    gemini_api_key: str = ""

    # Ollama local SLM
    ollama_host: str = "http://localhost:11434"

    # RunPod remote SLM
    runpod_pod_id: str = ""

    def provider_for(self, task: str) -> str:
        task_provider = getattr(self, f"llm_provider_{task}", "")
        return task_provider or self.llm_provider

    def model_for(self, task: str) -> str:
        task_model = getattr(self, f"llm_model_{task}", "")
        return task_model or self.llm_model

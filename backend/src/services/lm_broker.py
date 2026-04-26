import asyncio
import logging
import time

import anthropic
from openai import AsyncOpenAI, OpenAI

from config.settings import settings

logger = logging.getLogger(__name__)


def broker_for(task: str) -> "LMBroker":
    """
    Returns a broker configured for the given task, using per-task settings
    from .env (e.g. LLM_PROVIDER_AUDIT, LLM_MODEL_AUDIT), falling back to
    the global LLM_PROVIDER / LLM_MODEL defaults.

    Known tasks: "audit", "extraction"
    """
    return LMBroker(
        provider=settings.llm.provider_for(task),
        model=settings.llm.model_for(task),
    )

# Gemini OpenAI-compatible endpoint
_GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"


class LMBroker:
    """
    Central switchboard for all LLM/SLM calls in the pipeline.

    Instantiate with an explicit provider/model to override settings defaults:
        LMBroker(provider="anthropic", model="claude-opus-4-5")
        LMBroker(provider="ollama", model="llama3.2")

    Supported providers:
        openai    — OpenAI API (cloud LLM)
        anthropic — Anthropic API (cloud LLM)
        gemini    — Google Gemini via OpenAI-compatible endpoint (cloud LLM)
        ollama    — Ollama running on local machine (local SLM)
        runpod    — Ollama running on a RunPod instance (remote SLM)
    """

    def __init__(self, provider: str | None = None, model: str | None = None) -> None:
        self.provider = provider or settings.llm.llm_provider
        self.default_model = model or settings.llm.llm_model

        if self.provider == "openai":
            self.client = OpenAI(api_key=settings.llm.openai_api_key)
            self.async_client = AsyncOpenAI(api_key=settings.llm.openai_api_key)
            self._anthropic_client = None

        elif self.provider == "anthropic":
            self._anthropic_client = anthropic.Anthropic(api_key=settings.llm.anthropic_api_key)
            self._anthropic_async_client = anthropic.AsyncAnthropic(
                api_key=settings.llm.anthropic_api_key
            )
            self.client = None
            self.async_client = None

        elif self.provider == "gemini":
            self.client = OpenAI(
                api_key=settings.llm.gemini_api_key,
                base_url=_GEMINI_BASE_URL,
            )
            self.async_client = AsyncOpenAI(
                api_key=settings.llm.gemini_api_key,
                base_url=_GEMINI_BASE_URL,
            )
            self._anthropic_client = None

        elif self.provider == "ollama":
            base_url = f"{settings.llm.ollama_host}/v1"
            self.client = OpenAI(base_url=base_url, api_key="ollama")
            self.async_client = AsyncOpenAI(base_url=base_url, api_key="ollama")
            self._anthropic_client = None

        elif self.provider == "runpod":
            pod_id = settings.llm.runpod_pod_id
            base_url = f"https://{pod_id}-11434.proxy.runpod.net/v1"
            self.client = OpenAI(base_url=base_url, api_key="ollama")
            self.async_client = AsyncOpenAI(base_url=base_url, api_key="ollama")
            self._anthropic_client = None

        else:
            raise ValueError(f"Unsupported LLM provider: {self.provider!r}")

        logger.info("LMBroker initialized: provider=%s model=%s", self.provider, self.default_model)

    def ask(
        self,
        system_prompt: str,
        user_prompt: str,
        model: str | None = None,
        temperature: float = 0.7,
        calling_module: str = "unknown",
    ) -> str:
        target_model = model or self.default_model
        start = time.monotonic()
        error = None
        response_text = ""

        try:
            if self.provider == "anthropic":
                response_text = self._anthropic_ask(system_prompt, user_prompt, target_model, temperature)
            else:
                response = self.client.chat.completions.create(
                    model=target_model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    temperature=temperature,
                )
                response_text = response.choices[0].message.content or ""
        except Exception as e:
            error = str(e)
            response_text = f"Error: {error}"

        self._log_call(
            calling_module=calling_module,
            model=target_model,
            prompt_len=len(system_prompt) + len(user_prompt),
            response_len=len(response_text),
            latency=time.monotonic() - start,
            error=error,
        )
        return response_text

    async def ask_batch(
        self,
        tasks: list[str],
        system: str = "You are a professional financial analyst.",
        batch_size: int = 5,
        model: str | None = None,
        temperature: float = 0.7,
        calling_module: str = "unknown",
    ) -> list[str]:
        target_model = model or self.default_model
        semaphore = asyncio.Semaphore(batch_size)

        async def sem_task(user_p: str) -> str:
            async with semaphore:
                return await self._async_worker(system, user_p, target_model, temperature, calling_module)

        logger.debug(
            "ask_batch: module=%s tasks=%d concurrency=%d model=%s",
            calling_module, len(tasks), batch_size, target_model,
        )
        results = await asyncio.gather(*(sem_task(t) for t in tasks))
        return list(results)

    # --- Internal helpers ---

    def _anthropic_ask(
        self, system_prompt: str, user_prompt: str, model: str, temperature: float
    ) -> str:
        response = self._anthropic_client.messages.create(
            model=model,
            max_tokens=1024,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
            temperature=temperature,
        )
        return response.content[0].text

    async def _anthropic_ask_async(
        self, system_prompt: str, user_prompt: str, model: str, temperature: float
    ) -> str:
        response = await self._anthropic_async_client.messages.create(
            model=model,
            max_tokens=1024,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
            temperature=temperature,
        )
        return response.content[0].text

    async def _async_worker(
        self,
        system_prompt: str,
        user_prompt: str,
        model: str,
        temperature: float,
        calling_module: str,
    ) -> str:
        start = time.monotonic()
        error = None
        response_text = ""

        try:
            if self.provider == "anthropic":
                response_text = await self._anthropic_ask_async(
                    system_prompt, user_prompt, model, temperature
                )
            else:
                response = await self.async_client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    temperature=temperature,
                )
                response_text = response.choices[0].message.content or ""
        except Exception as e:
            error = str(e)
            response_text = f"Error: {error}"

        self._log_call(
            calling_module=calling_module,
            model=model,
            prompt_len=len(system_prompt) + len(user_prompt),
            response_len=len(response_text),
            latency=time.monotonic() - start,
            error=error,
        )
        return response_text

    def _log_call(
        self,
        calling_module: str,
        model: str,
        prompt_len: int,
        response_len: int,
        latency: float,
        error: str | None,
    ) -> None:
        if error:
            logger.error(
                "llm_call module=%s model=%s prompt_len=%d response_len=%d latency=%.3fs error=%r",
                calling_module, model, prompt_len, response_len, latency, error,
            )
        else:
            logger.info(
                "llm_call module=%s model=%s prompt_len=%d response_len=%d latency=%.3fs",
                calling_module, model, prompt_len, response_len, latency,
            )

import asyncio
import os

from dotenv import load_dotenv
from openai import AsyncOpenAI, OpenAI

load_dotenv()


class LMBroker:
    """
    LMBroker: Central switchboard for connecting the Research Pipeline
    to LLMs (RunPod/OpenAI) and SLMs (Local/Placeholder).
    """

    def __init__(self, provider: str = "runpod", config: dict | None = None) -> None:
        """
        config should include:
        - pod_id (for RunPod)
        - openai_api_key (for OpenAI)
        - default_model (e.g., 'qwen2.5:7b' for RunPod or 'gpt-4o-mini' for OpenAI)
        """
        self.provider = provider
        self.config = config or {}
        # self.default_model = self.config.get("default_model", "qwen2.5:7b") # idled since runpod.ai is unreasonably costly, unreliable and small models offer too low quality for the task
        self.default_model = self.config.get(
            "default_model", "gpt-4o-mini"
        )  # use OpenAI gpt-4o-mini: 0.15usd/1M token on input,0.60usd/1M token on output

        # Initialize Clients
        if self.provider == "runpod":
            pod_id = self.config.get("pod_id")
            # Construct the RunPod proxy URL for Ollama
            base_url = f"https://{pod_id}-11434.proxy.runpod.net/v1"
            self.client = OpenAI(base_url=base_url, api_key="ollama")
            self.async_client = AsyncOpenAI(base_url=base_url, api_key="ollama")

        elif self.provider == "openai":
            api_key = self.config.get("OPENAI_API_KEY") or os.environ.get("OPENAI_API_KEY")
            self.client = OpenAI(api_key=api_key)
            self.async_client = AsyncOpenAI(api_key=api_key)

        print(f"   [Broker] Initialized for {self.provider.upper()} (Model: {self.default_model})")

    def ask(
        self,
        system_prompt: str,
        user_prompt: str,
        model: str | None = None,
        temperature: float = 0.7,
    ) -> str:
        """
        Standard synchronous call for single completions.
        """
        target_model = model or self.default_model
        try:
            response = self.client.chat.completions.create(
                model=target_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=temperature,
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Error: {e!s}"

    async def _async_worker(
        self, system_prompt: str, user_prompt: str, model: str, temperature: float
    ) -> str:
        """Internal worker for handling individual async calls within a batch."""
        try:
            response = await self.async_client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=temperature,
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Error: {e!s}"

    async def ask_batch(
        self,
        tasks: list[str],
        system: str = "You are a professional financial auditor.",
        batch_size: int = 5,
        model: str | None = None,
        temperature: float = 0.7,
    ) -> list[str]:
        """
        The 'Batching Knob'. Fires multiple requests concurrently using a Semaphore.
        'tasks' is a list of user_prompts.
        """
        target_model = model or self.default_model
        semaphore = asyncio.Semaphore(batch_size)

        async def sem_task(user_p: str) -> str:
            async with semaphore:
                return await self._async_worker(system, user_p, target_model, temperature)

        print(f"   [Batching] Firing {len(tasks)} requests (Concurrency: {batch_size})...")
        results = await asyncio.gather(*(sem_task(t) for t in tasks))
        return results

    def local_slm_triage_placeholder(self, text_preview: str) -> bool:
        """
        Placeholder for a local SLM (1B-3B). Currently returns True.
        """
        return True

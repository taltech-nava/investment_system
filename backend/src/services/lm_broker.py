import asyncio
import json
from openai import OpenAI, AsyncOpenAI

class LMBroker:
    """
    LMBroker: Central switchboard for connecting the Research Pipeline 
    to LLMs (RunPod/OpenAI) and SLMs (Local/Placeholder).
    """
    
    def __init__(self, provider="runpod", config=None):
        """
        config should include:
        - pod_id (for RunPod)
        - openai_api_key (for OpenAI)
        - default_model (e.g., 'qwen2.5:7b' for RunPod or 'gpt-4o-mini' for OpenAI)
        """
        self.provider = provider
        self.config = config or {}
        self.default_model = self.config.get("default_model", "qwen2.5:7b")
        
        # Initialize Clients
        if self.provider == "runpod":
            pod_id = self.config.get("pod_id")
            # Construct the RunPod proxy URL for Ollama
            base_url = f"https://{pod_id}-11434.proxy.runpod.net/v1"
            self.client = OpenAI(base_url=base_url, api_key="ollama")
            self.async_client = AsyncOpenAI(base_url=base_url, api_key="ollama")
            
        elif self.provider == "openai":
            api_key = self.config.get("openai_api_key")
            self.client = OpenAI(api_key=api_key)
            self.async_client = AsyncOpenAI(api_key=api_key)
            
        print(f"   [Broker] Initialized for {self.provider.upper()} (Model: {self.default_model})")

    def ask(self, system_prompt, user_prompt, model=None, temperature=0.7):
        """
        Standard synchronous call for single completions.
        """
        target_model = model or self.default_model
        try:
            response = self.client.chat.completions.create(
                model=target_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=temperature
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Error: {str(e)}"

    async def _async_worker(self, system_prompt, user_prompt, model, temperature):
        """Internal worker for handling individual async calls within a batch."""
        try:
            response = await self.async_client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=temperature
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Error: {str(e)}"

    async def ask_batch(self, tasks, system_prompt="You are a professional financial auditor.", batch_size=5, model=None, temperature=0.7):
        """
        The 'Batching Knob'. Fires multiple requests concurrently using a Semaphore.
        'tasks' is a list of user_prompts.
        """
        target_model = model or self.default_model
        semaphore = asyncio.Semaphore(batch_size)
        
        async def sem_task(user_p):
            async with semaphore:
                return await self._async_worker(system_prompt, user_p, target_model, temperature)

        print(f"   [Batching] Firing {len(tasks)} requests (Concurrency: {batch_size})...")
        results = await asyncio.gather(*(sem_task(t) for t in tasks))
        return results

    def local_slm_triage_placeholder(self, text_preview):
        """
        Placeholder for a local SLM (1B-3B). Currently returns True.
        """
        return True

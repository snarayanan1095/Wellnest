import requests
import os
from typing import Dict, Any


class NIMLLMService:
    """Service for interacting with NVIDIA NIM Llama-3 API for text generation"""

    # Llama-3.1 Nemotron Nano endpoint
    LLAMA3_ENDPOINT = "https://integrate.api.nvidia.com/v1/chat/completions"

    @staticmethod
    def build_llama3_prompt(routine: Dict[str, Any]) -> str:
        """
        Build a prompt for Llama-3 to summarize the routine data.

        Args:
            routine: Dictionary containing routine metrics

        Returns:
            Formatted prompt string
        """
        summary = (
            "Here's a daily routine record in JSON. "
            "Summarize the household's activity in 2 sentences. "
            "If the routine looks unusual, mention possible reasons.\n\n"
            f"Routine:\n{routine}\n\nSummary:"
        )
        return summary

    @staticmethod
    def get_llama3_summary(routine_dict: Dict[str, Any]) -> str:
        """
        Call the Llama-3 API to generate a natural language summary of the routine.

        Args:
            routine_dict: Dictionary containing routine metrics (wake_up_time, bed_time, etc.)

        Returns:
            LLM-generated summary string

        Raises:
            requests.HTTPError: If the API call fails
            KeyError: If NIM_API_KEY is not found in environment variables
        """
        prompt = NIMLLMService.build_llama3_prompt(routine_dict)
        return NIMLLMService.get_custom_summary(prompt, max_tokens=128)

    @staticmethod
    def get_custom_summary(prompt: str, max_tokens: int = 150, temperature: float = 0.7) -> str:
        """
        Call the Llama-3 API with a custom prompt.

        Args:
            prompt: Custom prompt for the LLM
            max_tokens: Maximum tokens to generate
            temperature: Temperature for generation (0-1)

        Returns:
            LLM-generated response string

        Raises:
            requests.HTTPError: If the API call fails
            KeyError: If NIM_API_KEY is not found in environment variables
        """
        api_key = os.getenv("NIM_API_KEY")
        if not api_key:
            raise KeyError("NIM_API_KEY not found in environment variables")

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        data = {
            "model": "meta/llama-3.1-8b-instruct",
            "messages": [
                {
                    "role": "system",
                    "content": "You are a healthcare assistant analyzing elderly care patterns. Be concise and focus on actionable insights."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "max_tokens": max_tokens,
            "temperature": temperature,
            "top_p": 1.0,
            "stream": False
        }

        try:
            response = requests.post(
                NIMLLMService.LLAMA3_ENDPOINT,
                headers=headers,
                json=data,
                timeout=30
            )
            response.raise_for_status()

            result = response.json()
            # Extract the generated text from the response
            summary = result["choices"][0]["message"]["content"].strip()
            return summary

        except requests.exceptions.RequestException as e:
            print(f"⚠ Error calling NIM LLM API: {e}")
            raise

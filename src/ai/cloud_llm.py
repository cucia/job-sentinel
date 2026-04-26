"""
Cloud AI Provider Support for JobSentinel Agents

Supports multiple cloud AI providers:
- OpenAI (GPT-4, GPT-3.5)
- Anthropic Claude (Claude 3.5 Sonnet, Claude 3 Opus)
- Google Gemini
- OpenRouter (free tier available)
- Groq (fast & free tier)
- Together.ai (cheap)
- Ollama (local fallback)
"""

import os
from typing import List, Dict, Optional


class CloudLLMClient:
    """Unified client for multiple cloud AI providers."""

    def __init__(self, provider: str = "openai", model: str = None, api_key: str = None):
        self.provider = provider.lower()
        self.model = model
        self.api_key = api_key or self._get_api_key()
        self._client = None

    def _get_api_key(self) -> Optional[str]:
        """Get API key from environment."""
        key_map = {
            "openai": "OPENAI_API_KEY",
            "anthropic": "ANTHROPIC_API_KEY",
            "claude": "ANTHROPIC_API_KEY",
            "gemini": "GEMINI_API_KEY",
            "google": "GEMINI_API_KEY",
            "openrouter": "OPENROUTER_API_KEY",
            "groq": "GROQ_API_KEY",
            "together": "TOGETHER_API_KEY",
        }
        env_var = key_map.get(self.provider)
        return os.environ.get(env_var) if env_var else None

    def _get_default_model(self) -> str:
        """Get default model for provider."""
        defaults = {
            "openai": "gpt-4-turbo-preview",
            "anthropic": "claude-3-5-sonnet-20241022",
            "claude": "claude-3-5-sonnet-20241022",
            "gemini": "gemini-1.5-pro",
            "google": "gemini-1.5-pro",
            "openrouter": "google/gemini-flash-1.5",  # Free
            "groq": "llama-3.1-70b-versatile",  # Free tier
            "together": "meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo",
            "ollama": "llama3.2:latest",
        }
        return self.model or defaults.get(self.provider, "gpt-4-turbo-preview")

    def chat(self, messages: List[Dict[str, str]], temperature: float = 0.2) -> str:
        """Send chat request to cloud provider."""
        if self.provider in ["openai"]:
            return self._chat_openai(messages, temperature)
        elif self.provider in ["anthropic", "claude"]:
            return self._chat_anthropic(messages, temperature)
        elif self.provider in ["gemini", "google"]:
            return self._chat_gemini(messages, temperature)
        elif self.provider == "openrouter":
            return self._chat_openrouter(messages, temperature)
        elif self.provider == "groq":
            return self._chat_groq(messages, temperature)
        elif self.provider == "together":
            return self._chat_together(messages, temperature)
        elif self.provider == "ollama":
            return self._chat_ollama(messages, temperature)
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")

    def _chat_openai(self, messages: List[Dict[str, str]], temperature: float) -> str:
        """OpenAI API."""
        try:
            import openai

            if not self.api_key:
                raise ValueError("OPENAI_API_KEY not set")

            client = openai.OpenAI(api_key=self.api_key)
            response = client.chat.completions.create(
                model=self._get_default_model(),
                messages=messages,
                temperature=temperature,
            )
            return response.choices[0].message.content.strip()
        except ImportError:
            raise RuntimeError("openai package not installed. Run: pip install openai")
        except Exception as e:
            raise RuntimeError(f"OpenAI API error: {e}")

    def _chat_anthropic(self, messages: List[Dict[str, str]], temperature: float) -> str:
        """Anthropic Claude API."""
        try:
            import anthropic

            if not self.api_key:
                raise ValueError("ANTHROPIC_API_KEY not set")

            client = anthropic.Anthropic(api_key=self.api_key)

            # Convert messages format
            system_msg = None
            user_messages = []
            for msg in messages:
                if msg["role"] == "system":
                    system_msg = msg["content"]
                else:
                    user_messages.append(msg)

            response = client.messages.create(
                model=self._get_default_model(),
                max_tokens=2048,
                temperature=temperature,
                system=system_msg,
                messages=user_messages,
            )
            return response.content[0].text.strip()
        except ImportError:
            raise RuntimeError("anthropic package not installed. Run: pip install anthropic")
        except Exception as e:
            raise RuntimeError(f"Anthropic API error: {e}")

    def _chat_gemini(self, messages: List[Dict[str, str]], temperature: float) -> str:
        """Google Gemini API."""
        try:
            import google.generativeai as genai

            if not self.api_key:
                raise ValueError("GEMINI_API_KEY not set")

            genai.configure(api_key=self.api_key)
            model = genai.GenerativeModel(self._get_default_model())

            # Convert messages to Gemini format
            prompt = "\n\n".join([f"{msg['role']}: {msg['content']}" for msg in messages])

            response = model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=temperature,
                ),
            )
            return response.text.strip()
        except ImportError:
            raise RuntimeError("google-generativeai package not installed. Run: pip install google-generativeai")
        except Exception as e:
            raise RuntimeError(f"Gemini API error: {e}")

    def _chat_ollama(self, messages: List[Dict[str, str]], temperature: float) -> str:
        """Ollama local LLM (fallback)."""
        from src.ai.llm import chat
        return chat(messages, model=self._get_default_model(), temperature=temperature)

    def _chat_openrouter(self, messages: List[Dict[str, str]], temperature: float) -> str:
        """OpenRouter API (uses OpenAI SDK)."""
        try:
            import openai

            if not self.api_key:
                raise ValueError("OPENROUTER_API_KEY not set")

            client = openai.OpenAI(
                api_key=self.api_key,
                base_url="https://openrouter.ai/api/v1"
            )
            response = client.chat.completions.create(
                model=self._get_default_model(),
                messages=messages,
                temperature=temperature,
            )
            return response.choices[0].message.content.strip()
        except ImportError:
            raise RuntimeError("openai package not installed. Run: pip install openai")
        except Exception as e:
            raise RuntimeError(f"OpenRouter API error: {e}")

    def _chat_groq(self, messages: List[Dict[str, str]], temperature: float) -> str:
        """Groq API (fast inference)."""
        try:
            import openai

            if not self.api_key:
                raise ValueError("GROQ_API_KEY not set")

            client = openai.OpenAI(
                api_key=self.api_key,
                base_url="https://api.groq.com/openai/v1"
            )
            response = client.chat.completions.create(
                model=self._get_default_model(),
                messages=messages,
                temperature=temperature,
            )
            return response.choices[0].message.content.strip()
        except ImportError:
            raise RuntimeError("openai package not installed. Run: pip install openai")
        except Exception as e:
            raise RuntimeError(f"Groq API error: {e}")

    def _chat_together(self, messages: List[Dict[str, str]], temperature: float) -> str:
        """Together.ai API."""
        try:
            import openai

            if not self.api_key:
                raise ValueError("TOGETHER_API_KEY not set")

            client = openai.OpenAI(
                api_key=self.api_key,
                base_url="https://api.together.xyz/v1"
            )
            response = client.chat.completions.create(
                model=self._get_default_model(),
                messages=messages,
                temperature=temperature,
            )
            return response.choices[0].message.content.strip()
        except ImportError:
            raise RuntimeError("openai package not installed. Run: pip install openai")
        except Exception as e:
            raise RuntimeError(f"Together.ai API error: {e}")


def create_llm_client(settings: dict) -> CloudLLMClient:
    """Factory function to create LLM client from settings."""
    ai_config = settings.get("ai", {})

    provider = ai_config.get("provider", "openai")
    model = ai_config.get("model")
    api_key = ai_config.get("api_key")

    return CloudLLMClient(provider=provider, model=model, api_key=api_key)

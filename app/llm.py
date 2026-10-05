"""
LLM Interface for Cisco AI Assistant
Supports Gemini and OpenAI models
"""

import os
import json
from typing import Dict, Any, Optional, TYPE_CHECKING
import logging
from dotenv import load_dotenv

from .prompts import PromptTemplates

load_dotenv()
logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from openai import OpenAI
    import google.generativeai as genai

class LLMInterface:
    def __init__(self, provider: str = "gemini", model: Optional[str] = None):
        """
        Initialize LLM interface.

        Args:
            provider: Either 'gemini' or 'openai'
            model: Specific model name (optional)
        """
        self.provider = provider.lower()
        self.model = model
        self.client = None
        self._initialize_client()

    def _initialize_client(self):
        """Initialize the appropriate LLM client."""
        if self.provider == "gemini":
            try:
                import google.generativeai as genai
                api_key = os.getenv("GEMINI_API_KEY")
                if not api_key:
                    raise ValueError("GEMINI_API_KEY not found in environment")
                genai.configure(api_key=api_key)
                self.model_name = self.model or "gemini-3.8-flash"
                self.client = genai.GenerativeModel(self.model_name)
                logger.info(f"Initialized Gemini client with model {self.model_name}")
            except ImportError:
                logger.error("Google Generative AI package not installed")
                raise
        elif self.provider == "openai":
            try:
                from openai import OpenAI
                api_key = os.getenv("OPENAI_API_KEY")
                if not api_key:
                    raise ValueError("OPENAI_API_KEY not found in environment")
                self.client = OpenAI(api_key=api_key)
                self.model_name = self.model or "gpt-3.5-turbo"
                logger.info(f"Initialized OpenAI client with model {self.model_name}")
            except ImportError:
                logger.error("OpenAI package not installed")
                raise
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")

    def generate_network_json(self, prompt: str) -> Dict[str, Any]:
        """
        Generate network topology JSON from natural language prompt.

        Args:
            prompt: Natural language description of network

        Returns:
            Dictionary representing network topology
        """
        if self.provider == "gemini":
            return self._generate_with_gemini(prompt)
        elif self.provider == "openai":
            return self._generate_with_openai(prompt)
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")

    def _generate_with_gemini(self, prompt: str) -> Dict[str, Any]:
        """Generate using Gemini model."""
        # Get the prompt template from prompts.py
        prompt_template = PromptTemplates.network_topology_prompt()
        json_structure = '''
        {
            "devices": [
                {
                    "id": "unique_device_id",
                    "type": "router|switch|pc|server|cloud|firewall|loadbalancer",
                    "label": "human readable label",
                    "position": {"x": 0, "y": 0},  // optional, for layout
                    "properties": {
                        "ip": "ip_address",  // optional
                        "hostname": "hostname",  // optional
                        "model": "device_model",  // optional
                        "os": "operating_system"  // optional
                    }
                }
            ],
            "connections": [
                {
                    "source": "device_id",
                    "target": "device_id",
                    "label": "connection_label",  // optional
                    "type": "ethernet|serial|wireless|vpn",  // optional
                    "properties": {
                        "bandwidth": "1Gbps",  // optional
                        "latency": "10ms"  // optional
                    }
                }
            ]
        }
        '''
        enhanced_prompt = prompt_template.format(json_structure=json_structure, network_description=prompt)

        try:
            # Assert that the client is not None
            assert self.client is not None
            # For type checking in Gemini branch, we know it's a GenerativeModel
            if self.provider == "gemini":
                response = self.client.generate_content(enhanced_prompt)  # type: ignore
                response_text = (response.text or "").strip()
            else:
                # This branch should not be reached due to the provider check above
                raise ValueError(f"Unexpected provider {self.provider} in _generate_with_gemini")

            # Try to find JSON in the response
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]

            response_text = response_text.strip()
            return json.loads(response_text)
        except Exception as e:
            logger.error(f"Error generating with Gemini: {e}")
            # Return a basic structure as fallback
            return {
                "devices": [],
                "connections": [],
                "error": str(e)
            }

    def _generate_with_openai(self, prompt: str) -> Dict[str, Any]:
        """Generate using OpenAI model."""
        # Get the prompt template from prompts.py
        prompt_template = PromptTemplates.network_topology_prompt()
        json_structure = '''
        {
            "devices": [
                {
                    "id": "unique_device_id",
                    "type": "router|switch|pc|server|cloud|firewall|loadbalancer",
                    "label": "human readable label",
                    "position": {"x": 0, "y": 0},  // optional, for layout
                    "properties": {
                        "ip": "ip_address",  // optional
                        "hostname": "hostname",  // optional
                        "model": "device_model",  // optional
                        "os": "operating_system"  // optional
                    }
                }
            ],
            "connections": [
                {
                    "source": "device_id",
                    "target": "device_id",
                    "label": "connection_label",  // optional
                    "type": "ethernet|serial|wireless|vpn",  // optional
                    "properties": {
                        "bandwidth": "1Gbps",  // optional
                        "latency": "10ms"  // optional
                    }
                }
            ]
        }
        '''
        enhanced_prompt = prompt_template.format(json_structure=json_structure, network_description=prompt)

        try:
            # For OpenAI provider, we know self.client should be an OpenAI instance
            if self.provider != "openai":
                raise ValueError(f"Expected OpenAI provider, got {self.provider}")

            # Assert that the client is not None for type checking
            assert self.client is not None
            # At this point, self.client should be an OpenAI instance
            if self.provider == "openai":
                # We need to import OpenAI here to avoid circular imports
                from openai import OpenAI
                assert isinstance(self.client, OpenAI)
                response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[
                        {"role": "system", "content": "You are a network topology expert that outputs only valid JSON."},
                        {"role": "user", "content": enhanced_prompt}
                    ],
                    temperature=0.1
                )

            response_text = (response.choices[0].message.content or "").strip()

            # Try to find JSON in the response
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]

            response_text = response_text.strip()
            return json.loads(response_text)
        except Exception as e:
            logger.error(f"Error generating with OpenAI: {e}")
            # Return a basic structure as fallback
            return {
                "devices": [],
                "connections": [],
                "error": str(e)
            }

# Convenience function
def create_llm_interface(provider: str = "gemini", model: Optional[str] = None) -> LLMInterface:
    """Factory function to create LLM interface."""
    return LLMInterface(provider=provider, model=model)
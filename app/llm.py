"""
LLM Interface for Cisco AI Assistant
Supports Gemini and OpenAI models
"""

import os
import json
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

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
                self.model_name = self.model or "gemini-pro"
                self.client = genai.GenerativeModel(self.model_name)
                logger.info(f"Initialized Gemini client with model {self.model_name}")
            except ImportError:
                logger.error("Google Generative AI package not installed")
                raise
        elif self.provider == "openai":
            try:
                import openai
                api_key = os.getenv("OPENAI_API_KEY")
                if not api_key:
                    raise ValueError("OPENAI_API_KEY not found in environment")
                openai.api_key = api_key
                self.model_name = self.model or "gpt-3.5-turbo"
                self.client = openai
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
        # Enhanced prompt for structured JSON output
        enhanced_prompt = f"""
        You are a network topology expert. Convert the following natural language
        network description into a structured JSON format.

        The JSON should have the following structure:
        {{
            "devices": [
                {{
                    "id": "unique_device_id",
                    "type": "router|switch|pc|server|cloud|firewall|loadbalancer",
                    "label": "human readable label",
                    "position": {{"x": 0, "y": 0}},  // optional, for layout
                    "properties": {{
                        "ip": "ip_address",  // optional
                        "hostname": "hostname",  // optional
                        "model": "device_model",  // optional
                        "os": "operating_system"  // optional
                    }}
                }}
            ],
            "connections": [
                {{
                    "source": "device_id",
                    "target": "device_id",
                    "label": "connection_label",  // optional
                    "type": "ethernet|serial|wireless|vpn",  // optional
                    "properties": {{
                        "bandwidth": "1Gbps",  // optional
                        "latency": "10ms"  // optional
                    }}
                }}
            ]
        }}

        Only output valid JSON. Do not include any additional text.

        Network description: {prompt}
        """

        try:
            response = self.client.generate_content(enhanced_prompt)
            # Extract JSON from response
            response_text = response.text.strip()

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
        # Enhanced prompt for structured JSON output
        enhanced_prompt = f"""
        You are a network topology expert. Convert the following natural language
        network description into a structured JSON format.

        The JSON should have the following structure:
        {{
            "devices": [
                {{
                    "id": "unique_device_id",
                    "type": "router|switch|pc|server|cloud|firewall|loadbalancer",
                    "label": "human readable label",
                    "position": {{"x": 0, "y": 0}},  // optional, for layout
                    "properties": {{
                        "ip": "ip_address",  // optional
                        "hostname": "hostname",  // optional
                        "model": "device_model",  // optional
                        "os": "operating_system"  // optional
                    }}
                }}
            ],
            "connections": [
                {{
                    "source": "device_id",
                    "target": "device_id",
                    "label": "connection_label",  // optional
                    "type": "ethernet|serial|wireless|vpn",  // optional
                    "properties": {{
                        "bandwidth": "1Gbps",  // optional
                        "latency": "10ms"  // optional
                    }}
                }}
            ]
        }}

        Only output valid JSON. Do not include any additional text.

        Network description: {prompt}
        """

        try:
            response = self.client.ChatCompletion.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": "You are a network topology expert that outputs only valid JSON."},
                    {"role": "user", "content": enhanced_prompt}
                ],
                temperature=0.1
            )

            response_text = response.choices[0].message.content.strip()

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
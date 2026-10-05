"""
Prompt templates for the Cisco AI Assistant
"""

from typing import Dict, Any

class PromptTemplates:
    """Collection of prompt templates for different LLM interactions."""

    @staticmethod
    def network_topology_prompt() -> str:
        """Prompt for generating network topology from natural language."""
        return """
        You are a network topology expert. Convert the following natural language
        network description into a structured JSON format.

        The JSON should have the following structure:
        {json_structure}

        Only output valid JSON. Do not include any additional text.

        Network description: {network_description}
        """

    @staticmethod
    def network_validation_prompt() -> str:
        """Prompt for validating network topology (if using LLM for validation)."""
        return """
        You are a network validation expert. Review the following network topology
        JSON and identify any logical issues such as:
        - Duplicate IP addresses
        - Orphaned devices (no connections)
        - Invalid connections
        - Network loops
        - Missing required fields

        Provide your analysis in JSON format with:
        {
            "is_valid": true/false,
            "issues": [
                {
                    "type": "error|warning",
                    "message": "description of issue",
                    "device_id": "related_device_id_if_applicable",
                    "connection": ["source_device", "target_device"] if applicable
                }
            ],
            "suggestions": [
                "suggestion for improvement"
            ]
        }
        """

    @staticmethod
    def network_explanation_prompt() -> str:
        """Prompt for generating explanations of network topology."""
        return """
        You are a network engineering instructor. Explain the following network
        topology in clear, educational terms suitable for a student learning
        networking concepts.

        Focus on:
        - Overall network purpose and function
        - Role of each device type
        - How devices connect and communicate
        - Any notable design patterns or best practices
        - Potential improvements or considerations

        Network topology JSON:
        {topology_json}
        """

# Convenience functions
def get_network_topology_prompt() -> str:
    """Get the network topology generation prompt."""
    return PromptTemplates.network_topology_prompt()

def get_network_validation_prompt() -> str:
    """Get the network validation prompt."""
    return PromptTemplates.network_validation_prompt()

def get_network_explanation_prompt() -> str:
    """Get the network explanation prompt."""
    return PromptTemplates.network_explanation_prompt()
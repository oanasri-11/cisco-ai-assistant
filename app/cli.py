"""
Command Line Interface for Cisco AI Assistant
"""

import sys
import argparse
import os
from typing import Optional
from .llm import LLMInterface, create_llm_interface
from .schemas import NetworkTopology
from .validator import validate_network_topology
from .renderer import generate_network_diagram
from .prompts import get_network_topology_prompt
import json
import logging

logger = logging.getLogger(__name__)

class CLI:
    def __init__(self):
        """Initialize the CLI."""
        self.llm_interface = None
        self.setup_logging()

    def setup_logging(self):
        """Setup basic logging."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

    def initialize_llm(self, provider: str = "gemini", model: Optional[str] = None):
        """Initialize the LLM interface."""
        try:
            self.llm_interface = create_llm_interface(provider=provider, model=model)
            logger.info(f"LLM interface initialized with {provider}")
        except Exception as e:
            logger.error(f"Failed to initialize LLM: {e}")
            print(f"Error: Failed to initialize LLM: {e}")
            print("Please check your API keys and try again.")
            sys.exit(1)

    def run(self):
        """Main CLI entry point."""
        parser = argparse.ArgumentParser(
            description="Cisco AI Assistant - Generate network diagrams from natural language"
        )
        parser.add_argument(
            "--provider",
            choices=["gemini", "openai"],
            default="gemini",
            help="LLM provider to use (default: gemini)"
        )
        parser.add_argument(
            "--model",
            help="Specific model to use (optional)"
        )
        parser.add_argument(
            "--output",
            default="outputs",
            help="Output directory for diagrams (default: outputs)"
        )
        parser.add_argument(
            "--format",
            choices=["png", "svg", "pdf"],
            default="png",
            help="Output format for diagrams (default: png)"
        )
        parser.add_argument(
            "--no-validation",
            action="store_true",
            help="Skip network validation step"
        )
        parser.add_argument(
            "--explain",
            action="store_true",
            help="Generate explanation of the network topology"
        )
        parser.add_argument(
            "prompt",
            nargs="?",
            help="Natural language network description"
        )

        args = parser.parse_args()

        # Initialize LLM
        self.initialize_llm(provider=args.provider, model=args.model)

        # Get prompt from user if not provided
        if args.prompt:
            network_prompt = args.prompt
        else:
            network_prompt = input("Enter your network description: ")

        if not network_prompt.strip():
            print("Error: No network description provided.")
            sys.exit(1)

        print("\n🔄 Processing your network description...")

        # Generate network topology from LLM
        try:
            topology_data = self.llm_interface.generate_network_json(network_prompt)

            # Check if LLM returned an error
            if "error" in topology_data and topology_data["error"]:
                print(f"❌ LLM Error: {topology_data['error']}")
                sys.exit(1)

        except Exception as e:
            logger.error(f"Failed to generate network topology: {e}")
            print(f"❌ Failed to generate network topology: {e}")
            sys.exit(1)

        print("✅ Network topology generated")

        # Validate topology if requested
        if not args.no_validation:
            print("🔍 Validating network topology...")
            is_valid, errors, warnings = validate_network_topology(topology_data)

            if warnings:
                print("⚠️  Warnings:")
                for warning in warnings:
                    print(f"   - {warning}")

            if not is_valid:
                print("❌ Validation failed:")
                for error in errors:
                    print(f"   - {error}")

                # Ask if user wants to continue anyway
                response = input("\nContinue anyway? (y/N): ")
                if response.lower() != 'y':
                    sys.exit(1)
            else:
                print("✅ Network topology validated")

        # Generate explanation if requested
        if args.explain:
            print("💡 Generating explanation...")
            self._generate_explanation(network_prompt, topology_data)

        # Generate diagram
        print(f"🎨 Generating diagram ({args.format.upper()} format)...")
        success, message, output_file = generate_network_diagram(
            topology=topology_data,
            output_dir=args.output,
            filename="network_diagram",
            output_format=args.format
        )

        if success:
            print(f"✅ {message}")
            print(f"📁 Diagram saved to: {os.path.abspath(output_file)}")
        else:
            print(f"❌ {message}")
            sys.exit(1)

    def _generate_explanation(self, prompt: str, topology_data: dict):
        """Generate and display explanation of the network topology."""
        try:
            explanation_prompt = f"""
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
            {json.dumps(topology_data, indent=2)}

            Original description:
            {prompt}
            """

            # For now, we'll just print a simple explanation
            # In a full implementation, we'd call the LLM with this prompt
            print("\n📝 Network Explanation:")
            print("=" * 50)

            devices = topology_data.get('devices', [])
            connections = topology_data.get('connections', [])

            print(f"This network consists of {len(devices)} device(s) and {len(connections)} connection(s).")

            if devices:
                print("\nDevices:")
                for device in devices:
                    device_type = device.get('type', 'unknown')
                    label = device.get('label', device.get('id', 'unnamed'))
                    print(f"  - {label} ({device_type})")

                    # Show properties if available
                    props = device.get('properties', {})
                    if props:
                        prop_strs = [f"{k}: {v}" for k, v in props.items() if v]
                        if prop_strs:
                            print(f"    Properties: {', '.join(prop_strs)}")

            if connections:
                print("\nConnections:")
                for conn in connections:
                    source = conn.get('source', 'unknown')
                    target = conn.get('target', 'unknown')
                    label = conn.get('label', '')
                    conn_type = conn.get('type', 'unspecified')
                    label_text = f" [{label}]" if label else ""
                    print(f"  - {source} --{label_text}--> {target} ({conn_type})")

            print("=" * 50)

        except Exception as e:
            logger.warning(f"Could not generate explanation: {e}")
            print("⚠️  Could not generate detailed explanation")

def main():
    """Entry point for the CLI."""
    cli = CLI()
    cli.run()

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
Cisco AI Assistant - Main Entry Point
"""

import sys
import os
from .cli import CLI

def main():
    """Main entry point for the Cisco AI Assistant."""
    cli = CLI()
    cli.run()

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OneClickDock Knowledge Base MCP Server Launcher
Located inside tools/ directory.
"""
import sys
import os

# Ensure project root (parent directory of tools/) is in sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from Agent.knowledge_base.cli import main

if __name__ == "__main__":
    if len(sys.argv) == 1:
        # Default to running mcp stdio loop if no args passed
        sys.argv.append("mcp")
    main()

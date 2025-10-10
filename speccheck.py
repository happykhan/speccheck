#!/usr/bin/env python3
"""
Backward compatibility wrapper for speccheck CLI.
The actual CLI has been moved to speccheck/cli.py
"""
from speccheck.cli import main

if __name__ == "__main__":
    main()

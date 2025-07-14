#!/usr/bin/env python3
"""
Launcher for WindowsUpdate
"""
import os
import sys

# Change to script directory
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Add current directory to path
sys.path.insert(0, os.getcwd())

# Import and run client
from client.main import main

if __name__ == '__main__':
    main()

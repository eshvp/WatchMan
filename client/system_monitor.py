"""
System information collector for WatchMan client.
Gathers CPU, memory, network, and other system metrics.
"""
import psutil
import platform
import socket
import subprocess
import json
from datetime import datetime
import uuid
import os

class SystemMonitor:
    """Collects comprehensive system information"""
    
    def __init__(self):
        self.device_id = self._generate_device_id()
        self.hostname = platform.node()
    
    def _generate_device_id(self) -> str:
        """Generate unique device identifier"""
        import hashlib
        system_info = f"{platform.node()}-{platform.system()}-{platform.processor()}"
        return hashlib.md5(system_info.encode()).hexdigest()[:12]
    
    def get_cpu_info(self) -> dict:
        """Get CPU information and usage"""
        try:
            cpu_freq = psutil.cpu_freq()
            return {
                'type': platform.processor(),
                'cores_physical': psutil.cpu_count(logical=False),
                'cores_logical': psutil.cpu_count(logical=True),
                'frequency_mhz': cpu_freq.current if cpu_freq else 0,
                'frequency_max': cpu_freq.max if cpu_freq else 0,
                'usage_percent': psutil.cpu_percent(interval=1),
                'usage_per_core': psutil.cpu_percent(interval=1, percpu=True)
            }
        except Exception as e:
            return {'error': str(e)}
    
    def get_memory_info(self) -> dict:
        """Get memory information and usage"""
        try:
            memory = psutil.virtual_memory()
            swap = psutil.swap_memory()
            
            return {
                'total_gb': round(memory.total / (1024**3), 2),
                'available_gb': round(memory.available / (1024**3), 2),
                'used_gb': round(memory.used / (1024**3), 2),
                'usage_percent': memory.percent,
                'swap_total_gb': round(swap.total / (1024**3), 2),
                'swap_used_gb': round(swap.used / (1024**3), 2),
                'swap_percent': swap.percent
            }
        except Exception as e:
            return {'error': str(e)}
    
    def get_disk_info(self) -> dict:
        """Get disk usage information"""
        try:
            disk_usage = psutil.disk_usage('/')
            disk_io = psutil.disk_io_counters()
            
            return {
                'total_gb': round(disk_usage.total / (1024**3), 2),
                'used_gb': round(disk_usage.used / (1024**3), 2),
                'free_gb': round(disk_usage.free / (1024**3), 2),
                'usage_percent': (disk_usage.used / disk_usage.total) * 100,
                'read_bytes': disk_io.read_bytes if disk_io else 0,
                'write_bytes': disk_io.write_bytes if disk_io else 0
            }
        except Exception as e:
            return {'error': str(e)}
    
    def get_network_info(self) -> dict:
        """Get network information"""
        try:
            # Get network interfaces
            interfaces = psutil.net_if_addrs()
            stats = psutil.net_if_stats()
            io_counters = psutil.net_io_counters(pernic=True)
            
            network_data = {
                'interfaces': {},
                'total_bytes_sent': 0,
                'total_bytes_recv': 0
            }
            
            for interface, addresses in interfaces.items():
                if interface in stats:
                    interface_info = {
                        'is_up': stats[interface].isup,
                        'speed': stats[interface].speed,
                        'addresses': []
                    }
                    
                    for addr in addresses:
                        addr_info = {
                            'family': str(addr.family),
                            'address': addr.address,
                            'netmask': addr.netmask,
                            'broadcast': addr.broadcast
                        }
                        interface_info['addresses'].append(addr_info)
                    
                    if interface in io_counters:
                        interface_info['bytes_sent'] = io_counters[interface].bytes_sent
                        interface_info['bytes_recv'] = io_counters[interface].bytes_recv
                        network_data['total_bytes_sent'] += io_counters[interface].bytes_sent
                        network_data['total_bytes_recv'] += io_counters[interface].bytes_recv
                    
                    network_data['interfaces'][interface] = interface_info
            
            # Get current IP addresses
            try:
                # Get IPv4
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                s.connect(("8.8.8.8", 80))
                ipv4 = s.getsockname()[0]
                s.close()
            except:
                ipv4 = "Unknown"
            
            network_data['current_ipv4'] = ipv4
            network_data['hostname'] = socket.gethostname()
            
            return network_data
            
        except Exception as e:
            return {'error': str(e)}
    
    def get_wifi_info(self) -> dict:
        """Get WiFi connection information (Windows specific)"""
        try:
            if platform.system() == "Windows":
                # Use netsh to get WiFi info
                result = subprocess.run(
                    ['netsh', 'wlan', 'show', 'profile'],
                    capture_output=True, text=True, shell=True
                )
                
                if result.returncode == 0:
                    # Parse WiFi profiles
                    profiles = []
                    for line in result.stdout.split('\n'):
                        if 'All User Profile' in line:
                            profile = line.split(':')[-1].strip()
                            profiles.append(profile)
                    
                    # Get current connection
                    current_result = subprocess.run(
                        ['netsh', 'wlan', 'show', 'interfaces'],
                        capture_output=True, text=True, shell=True
                    )
                    
                    current_ssid = "Not connected"
                    if current_result.returncode == 0:
                        for line in current_result.stdout.split('\n'):
                            if 'SSID' in line and 'BSSID' not in line:
                                current_ssid = line.split(':')[-1].strip()
                                break
                    
                    return {
                        'current_ssid': current_ssid,
                        'available_profiles': profiles[:10],  # Limit to 10
                        'connection_type': 'WiFi'
                    }
            
            return {'connection_type': 'Unknown', 'current_ssid': 'Unknown'}
            
        except Exception as e:
            return {'error': str(e)}
    
    def get_gpu_info(self) -> dict:
        """Get graphics card information"""
        try:
            if platform.system() == "Windows":
                # Use wmic to get GPU info
                result = subprocess.run(
                    ['wmic', 'path', 'win32_VideoController', 'get', 'name'],
                    capture_output=True, text=True, shell=True
                )
                
                if result.returncode == 0:
                    gpus = []
                    for line in result.stdout.split('\n'):
                        line = line.strip()
                        if line and line != 'Name':
                            gpus.append(line)
                    
                    return {'graphics_cards': gpus}
            
            return {'graphics_cards': ['Unknown']}
            
        except Exception as e:
            return {'error': str(e)}
    
    def get_uptime(self) -> dict:
        """Get system uptime"""
        try:
            boot_time = psutil.boot_time()
            uptime_seconds = datetime.now().timestamp() - boot_time
            
            days = int(uptime_seconds // 86400)
            hours = int((uptime_seconds % 86400) // 3600)
            minutes = int((uptime_seconds % 3600) // 60)
            
            return {
                'boot_time': datetime.fromtimestamp(boot_time).isoformat(),
                'uptime_seconds': int(uptime_seconds),
                'uptime_formatted': f"{days}d {hours}h {minutes}m"
            }
        except Exception as e:
            return {'error': str(e)}
    
    def get_system_info(self) -> dict:
        """Get basic system information"""
        try:
            return {
                'hostname': self.hostname,
                'device_id': self.device_id,
                'platform': platform.platform(),
                'system': platform.system(),
                'release': platform.release(),
                'version': platform.version(),
                'machine': platform.machine(),
                'processor': platform.processor(),
                'python_version': platform.python_version(),
                'timestamp': datetime.utcnow().isoformat()
            }
        except Exception as e:
            return {'error': str(e)}
    
    def get_all_metrics(self) -> dict:
        """Get comprehensive system metrics"""
        return {
            'system_info': self.get_system_info(),
            'cpu_info': self.get_cpu_info(),
            'memory_info': self.get_memory_info(),
            'disk_info': self.get_disk_info(),
            'network_info': self.get_network_info(),
            'wifi_info': self.get_wifi_info(),
            'gpu_info': self.get_gpu_info(),
            'uptime_info': self.get_uptime()
        }

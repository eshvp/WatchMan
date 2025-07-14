"""
Communication protocols and message handling for WatchMan system.
"""
import json
import uuid
from datetime import datetime
from typing import Dict, Any, Optional

class MessageType:
    """Message type constants"""
    HEARTBEAT = "heartbeat"
    SYSTEM_INFO = "system_info"
    SCREEN_CAPTURE = "screen_capture"
    DEVICE_STATUS = "device_status"
    COMMAND = "command"
    RESPONSE = "response"
    AUTHENTICATION = "auth"
    DISCONNECT = "disconnect"

class WatchManMessage:
    """Standard message format for WatchMan communications"""
    
    def __init__(self, msg_type: str, data: Dict[str, Any], device_id: str = None):
        self.id = str(uuid.uuid4())
        self.type = msg_type
        self.data = data
        self.device_id = device_id or self._generate_device_id()
        self.timestamp = datetime.utcnow().isoformat()
    
    def _generate_device_id(self) -> str:
        """Generate unique device identifier"""
        import platform
        import hashlib
        
        # Create device fingerprint
        system_info = f"{platform.node()}-{platform.system()}-{platform.processor()}"
        return hashlib.md5(system_info.encode()).hexdigest()[:12]
    
    def to_json(self) -> str:
        """Serialize message to JSON"""
        return json.dumps({
            'id': self.id,
            'type': self.type,
            'data': self.data,
            'device_id': self.device_id,
            'timestamp': self.timestamp
        })
    
    @classmethod
    def from_json(cls, json_str: str) -> 'WatchManMessage':
        """Deserialize message from JSON"""
        data = json.loads(json_str)
        msg = cls(data['type'], data['data'], data['device_id'])
        msg.id = data['id']
        msg.timestamp = data['timestamp']
        return msg

def create_heartbeat_message(device_id: str) -> WatchManMessage:
    """Create heartbeat message"""
    return WatchManMessage(
        MessageType.HEARTBEAT,
        {'status': 'alive', 'timestamp': datetime.utcnow().isoformat()},
        device_id
    )

def create_system_info_message(system_data: Dict[str, Any], device_id: str) -> WatchManMessage:
    """Create system information message"""
    return WatchManMessage(
        MessageType.SYSTEM_INFO,
        system_data,
        device_id
    )

def create_screen_capture_message(image_data: str, device_id: str) -> WatchManMessage:
    """Create screen capture message"""
    return WatchManMessage(
        MessageType.SCREEN_CAPTURE,
        {'image': image_data, 'format': 'base64_png'},
        device_id
    )

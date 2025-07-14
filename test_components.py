"""
Example scripts for testing WatchMan components
"""

# Test system monitor
def test_system_monitor():
    from client.system_monitor import SystemMonitor
    
    monitor = SystemMonitor()
    print("Device ID:", monitor.device_id)
    print("Hostname:", monitor.hostname)
    print("\nCPU Info:")
    print(monitor.get_cpu_info())
    print("\nMemory Info:")
    print(monitor.get_memory_info())
    print("\nNetwork Info:")
    print(monitor.get_network_info())

# Test encryption
def test_encryption():
    from shared.encryption import EncryptionManager
    
    enc = EncryptionManager("test_password")
    
    test_data = "This is a secret message"
    encrypted = enc.encrypt(test_data)
    decrypted = enc.decrypt(encrypted)
    
    print(f"Original: {test_data}")
    print(f"Encrypted: {encrypted}")
    print(f"Decrypted: {decrypted}")
    print(f"Match: {test_data == decrypted}")

# Test protocol
def test_protocol():
    from shared.protocol import WatchManMessage, MessageType, create_heartbeat_message
    
    # Create a test message
    data = {"test": "data", "number": 123}
    msg = WatchManMessage(MessageType.SYSTEM_INFO, data, "test_device")
    
    # Serialize and deserialize
    json_str = msg.to_json()
    restored_msg = WatchManMessage.from_json(json_str)
    
    print(f"Original message ID: {msg.id}")
    print(f"Restored message ID: {restored_msg.id}")
    print(f"Data matches: {msg.data == restored_msg.data}")

if __name__ == "__main__":
    print("Testing WatchMan Components")
    print("=" * 40)
    
    print("\n1. Testing System Monitor:")
    try:
        test_system_monitor()
    except Exception as e:
        print(f"Error: {e}")
    
    print("\n2. Testing Encryption:")
    try:
        test_encryption()
    except Exception as e:
        print(f"Error: {e}")
    
    print("\n3. Testing Protocol:")
    try:
        test_protocol()
    except Exception as e:
        print(f"Error: {e}")
    
    print("\nTesting completed!")

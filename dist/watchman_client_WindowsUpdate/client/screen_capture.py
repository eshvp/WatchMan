"""
Screen capture functionality for WatchMan client.
Captures desktop screenshots for remote monitoring.
"""
import base64
import io
from PIL import Image, ImageGrab
import time
from datetime import datetime

class ScreenCapture:
    """Handles desktop screen capture operations"""
    
    def __init__(self, quality: int = 85, max_width: int = 1920):
        self.quality = quality
        self.max_width = max_width
        self.last_capture_time = 0
        self.min_interval = 1.0  # Minimum seconds between captures
    
    def capture_screen(self, compress: bool = True) -> str:
        """Capture the current screen and return as base64 encoded image"""
        try:
            # Rate limiting
            current_time = time.time()
            if current_time - self.last_capture_time < self.min_interval:
                return None
            
            self.last_capture_time = current_time
            
            # Capture screenshot
            screenshot = ImageGrab.grab()
            
            if compress:
                screenshot = self._compress_image(screenshot)
            
            # Convert to base64
            buffer = io.BytesIO()
            screenshot.save(buffer, format='PNG')
            image_data = base64.b64encode(buffer.getvalue()).decode('utf-8')
            
            return image_data
            
        except Exception as e:
            print(f"Error capturing screen: {e}")
            return None
    
    def _compress_image(self, image: Image.Image) -> Image.Image:
        """Compress image for faster transmission"""
        # Resize if too large
        if image.width > self.max_width:
            ratio = self.max_width / image.width
            new_height = int(image.height * ratio)
            image = image.resize((self.max_width, new_height), Image.Resampling.LANCZOS)
        
        # Convert to RGB if necessary (for JPEG compression)
        if image.mode == 'RGBA':
            rgb_image = Image.new('RGB', image.size, (255, 255, 255))
            rgb_image.paste(image, mask=image.split()[-1])
            image = rgb_image
        
        return image
    
    def capture_region(self, x: int, y: int, width: int, height: int) -> str:
        """Capture a specific region of the screen"""
        try:
            # Capture specific region
            bbox = (x, y, x + width, y + height)
            screenshot = ImageGrab.grab(bbox)
            
            # Convert to base64
            buffer = io.BytesIO()
            screenshot.save(buffer, format='PNG')
            image_data = base64.b64encode(buffer.getvalue()).decode('utf-8')
            
            return image_data
            
        except Exception as e:
            print(f"Error capturing screen region: {e}")
            return None
    
    def get_screen_info(self) -> dict:
        """Get screen resolution and information"""
        try:
            screenshot = ImageGrab.grab()
            return {
                'width': screenshot.width,
                'height': screenshot.height,
                'mode': screenshot.mode,
                'timestamp': datetime.utcnow().isoformat()
            }
        except Exception as e:
            return {'error': str(e)}

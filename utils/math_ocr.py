"""
Mathematical OCR using Claude Vision API for accurate equation extraction
"""
import anthropic
import base64
from PIL import Image
from io import BytesIO
from pathlib import Path
from typing import Optional
from loguru import logger

from config.settings import settings


MATH_OCR_PROMPT = """You are an expert at extracting mathematical equations and formulas from images.

Please carefully extract ALL mathematical content from this image, including:
- Equations and formulas (use LaTeX notation where appropriate)
- Variable definitions
- Mathematical symbols and notation
- Any text explaining the mathematics

Format your response as clean, readable text that preserves:
1. The logical flow and structure
2. Mathematical notation (you can use Unicode symbols or LaTeX)
3. Line breaks and spacing for clarity
4. Any annotations like "(1 Mark)", "(2 Marks)", etc.

Be extremely accurate with:
- Subscripts and superscripts
- Greek letters (ψ, θ, α, etc.)
- Integrals, limits, fractions
- Special symbols (∈, →, ∞, etc.)

Extract the content verbatim without summarizing or interpreting."""


class MathOCR:
    """Advanced mathematical OCR using Claude Vision API"""
    
    def __init__(self):
        self.client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        self.model = settings.anthropic_model
        
    def _image_to_base64(self, image: Image.Image, max_size_mb: float = 3.5) -> str:
        """
        Convert PIL Image to base64 string with compression if needed
        
        Args:
            image: PIL Image object
            max_size_mb: Maximum size in MB before compression (default 3.5MB to stay well under 5MB after base64)
        """
        # Try to save with current quality
        buffered = BytesIO()
        image.save(buffered, format="PNG")
        current_size = len(buffered.getvalue())
        
        # If size is acceptable, check base64 size
        max_size_bytes = int(max_size_mb * 1024 * 1024)
        
        if current_size <= max_size_bytes:
            # Check base64 encoded size
            encoded = base64.b64encode(buffered.getvalue())
            if len(encoded) <= 5242880:  # 5MB in bytes
                return encoded.decode()
        
        logger.warning(f"Image size {current_size/1024/1024:.2f}MB, needs compression for API limit")
        
        # Base64 encoding increases size by ~33%, so target much smaller
        # API limit is 5MB base64, so aim for ~3.7MB raw PNG
        target_raw_bytes = 3700000  # 3.7MB target
        resize_ratio = (target_raw_bytes / current_size) ** 0.5  # Square root for 2D resize
        
        new_width = int(image.width * resize_ratio)
        new_height = int(image.height * resize_ratio)
        
        logger.info(f"Resizing from {image.width}x{image.height} to {new_width}x{new_height}")
        
        # Resize image
        resized = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # Save resized image with JPEG for better compression
        buffered = BytesIO()
        if resized.mode != 'RGB':
            resized = resized.convert('RGB')
        resized.save(buffered, format="JPEG", quality=85, optimize=True)
        final_size = len(buffered.getvalue())
        
        # Check final base64 size
        encoded = base64.b64encode(buffered.getvalue())
        encoded_size = len(encoded)
        
        logger.success(f"Compressed: {current_size/1024/1024:.2f}MB → {final_size/1024/1024:.2f}MB (base64: {encoded_size/1024/1024:.2f}MB)")
        
        return encoded.decode()
    
    def extract_math(self, image_path: Path) -> Optional[str]:
        """
        Extract mathematical content from an image using Claude Vision
        
        Args:
            image_path: Path to the image containing mathematical equations
            
        Returns:
            Extracted mathematical text with proper notation
        """
        try:
            # Load and encode image
            image = Image.open(image_path)
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            image_base64 = self._image_to_base64(image)
            
            # Call Claude Vision API
            message = self.client.messages.create(
                model=self.model,
                max_tokens=2048,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": "image/jpeg",
                                    "data": image_base64,
                                },
                            },
                            {
                                "type": "text",
                                "text": MATH_OCR_PROMPT
                            }
                        ],
                    }
                ],
            )
            
            extracted_text = message.content[0].text
            logger.success(f"Extracted {len(extracted_text)} chars of mathematical content")
            
            return extracted_text
            
        except Exception as e:
            logger.error(f"Math OCR failed: {e}")
            return None
    
    def extract_math_from_multiple_pages(self, image_paths: list[Path]) -> str:
        """
        Extract mathematical content from multiple pages
        
        Args:
            image_paths: List of image paths
            
        Returns:
            Combined extracted text
        """
        all_text = []
        
        for i, img_path in enumerate(image_paths, 1):
            logger.info(f"Extracting math from page {i}/{len(image_paths)}")
            text = self.extract_math(img_path)
            if text:
                all_text.append(f"=== Page {i} ===\n{text}")
        
        return "\n\n".join(all_text)

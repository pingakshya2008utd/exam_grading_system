from PIL import Image
from typing import List, Dict
from loguru import logger
from tqdm import tqdm

from utils.ocr_tools import OCREngine
from utils.vision_api import ClaudeVisionAPI
from models.schemas import OCRResult
from config.settings import settings


class OCRAgent:
    """Agent for intelligent multi-engine OCR"""
    
    def __init__(self):
        self.ocr_engine = OCREngine()
        self.vision_api = ClaudeVisionAPI()
    
    def process_images(self, image_paths: List[str], 
                      is_handwritten: bool = False) -> List[OCRResult]:
        """
        Batch OCR processing with intelligent fallback
        
        Args:
            image_paths: List of image file paths
            is_handwritten: Whether images contain handwriting
            
        Returns:
            List of OCRResult objects
        """
        logger.info(f"Processing {len(image_paths)} images with OCR")
        
        results = []
        for i, path in enumerate(tqdm(image_paths, desc="OCR Processing"), 1):
            result = self.process_single_image(path, is_handwritten)
            results.append(result)
            
            if settings.verbose:
                logger.debug(f"Page {i}: confidence={result.confidence:.2f}, "
                           f"engine={result.engine}, quality={result.quality}")
        
        avg_confidence = sum(r.confidence for r in results) / len(results)
        logger.success(f"OCR complete. Average confidence: {avg_confidence:.2f}")
        
        return results
    
    def process_single_image(self, image_path: str, 
                            is_handwritten: bool = False) -> OCRResult:
        """
        Process single image with intelligent fallback to Claude Vision
        
        Args:
            image_path: Path to image file
            is_handwritten: Whether image contains handwriting
            
        Returns:
            OCRResult object
        """
        try:
            image = Image.open(image_path)
            
            # Try local OCR first
            result = self.ocr_engine.intelligent_ocr(image, is_handwritten)
            
            # Check if Claude Vision is needed
            if self.ocr_engine.needs_claude_vision(result):
                logger.info(f"Using Claude Vision for improved OCR (confidence: {result.confidence:.2f})")
                vision_result = self.vision_api.ocr_with_vision(image, is_handwritten)
                
                # Use Vision result if it's likely better
                if vision_result.confidence > 0:
                    return vision_result
            
            return result
            
        except Exception as e:
            logger.error(f"OCR failed for {image_path}: {e}")
            return OCRResult(
                text="",
                confidence=0.0,
                engine="error",
                has_handwriting=is_handwritten,
                has_math=False,
                quality="poor"
            )
    
    def extract_from_specific_region(self, image_path: str, 
                                     bbox: tuple,
                                     is_handwritten: bool = False) -> OCRResult:
        """
        Extract text from specific region of image
        
        Args:
            image_path: Path to image file
            bbox: Bounding box (x_min%, y_min%, x_max%, y_max%)
            is_handwritten: Whether region contains handwriting
            
        Returns:
            OCRResult object
        """
        from utils.image_tools import ImageProcessor
        
        try:
            image = Image.open(image_path)
            processor = ImageProcessor()
            
            # Crop to region
            cropped = processor.crop_region(image, bbox)
            
            # Process cropped region
            result = self.ocr_engine.intelligent_ocr(cropped, is_handwritten)
            
            # Fallback to Claude Vision if needed
            if self.ocr_engine.needs_claude_vision(result):
                result = self.vision_api.ocr_with_vision(cropped, is_handwritten)
            
            return result
            
        except Exception as e:
            logger.error(f"Region extraction failed: {e}")
            return OCRResult(
                text="",
                confidence=0.0,
                engine="error",
                has_handwriting=is_handwritten,
                has_math=False,
                quality="poor"
            )

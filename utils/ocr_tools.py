import pytesseract
import easyocr
import re
from PIL import Image
from typing import Tuple, Optional
from loguru import logger

from config.settings import settings
from models.schemas import OCRResult


class OCREngine:
    """Multi-engine OCR with intelligent fallback"""
    
    def __init__(self):
        self.reader = None
        if settings.use_multi_ocr:
            try:
                self.reader = easyocr.Reader(['en'], gpu=settings.use_gpu)
                logger.info("EasyOCR initialized successfully")
            except Exception as e:
                logger.warning(f"EasyOCR initialization failed: {e}")
    
    def ocr_printed_text(self, image: Image.Image) -> OCRResult:
        """
        OCR for printed text using Tesseract
        
        Args:
            image: PIL Image
            
        Returns:
            OCRResult object
        """
        try:
            # Get OCR text and data
            data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
            text = pytesseract.image_to_string(image)
            
            # Calculate average confidence
            confidences = [int(conf) for conf in data['conf'] if int(conf) > 0]
            avg_confidence = sum(confidences) / len(confidences) / 100 if confidences else 0.0
            
            # Detect math notation
            has_math = self._detect_math_notation(text)
            
            return OCRResult(
                text=text.strip(),
                confidence=avg_confidence,
                engine="tesseract",
                has_handwriting=False,
                has_math=has_math,
                quality="good" if avg_confidence > 0.8 else "fair" if avg_confidence > 0.6 else "poor"
            )
            
        except Exception as e:
            logger.error(f"Tesseract OCR failed: {e}")
            return OCRResult(
                text="",
                confidence=0.0,
                engine="tesseract",
                has_handwriting=False,
                has_math=False,
                quality="poor"
            )
    
    def ocr_handwritten_text(self, image: Image.Image) -> OCRResult:
        """
        OCR for handwritten text using EasyOCR
        
        Args:
            image: PIL Image
            
        Returns:
            OCRResult object
        """
        if not self.reader:
            logger.warning("EasyOCR not available, falling back to Tesseract")
            return self.ocr_printed_text(image)
        
        try:
            # EasyOCR expects numpy array or image path
            import numpy as np
            img_array = np.array(image)
            
            results = self.reader.readtext(img_array)
            
            # Combine text and calculate average confidence
            texts = []
            confidences = []
            for (bbox, text, conf) in results:
                texts.append(text)
                confidences.append(conf)
            
            combined_text = ' '.join(texts)
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
            
            # Detect math notation
            has_math = self._detect_math_notation(combined_text)
            
            return OCRResult(
                text=combined_text.strip(),
                confidence=avg_confidence,
                engine="easyocr",
                has_handwriting=True,
                has_math=has_math,
                quality="good" if avg_confidence > 0.7 else "fair" if avg_confidence > 0.5 else "poor"
            )
            
        except Exception as e:
            logger.error(f"EasyOCR failed: {e}")
            return OCRResult(
                text="",
                confidence=0.0,
                engine="easyocr",
                has_handwriting=True,
                has_math=False,
                quality="poor"
            )
    
    def intelligent_ocr(self, image: Image.Image, 
                       is_handwritten: bool = False) -> OCRResult:
        """
        Intelligently select OCR engine based on content type
        
        Args:
            image: PIL Image
            is_handwritten: Whether the image likely contains handwriting
            
        Returns:
            OCRResult object
        """
        # Try appropriate engine first
        if is_handwritten:
            result = self.ocr_handwritten_text(image)
        else:
            result = self.ocr_printed_text(image)
        
        # If confidence is low and multi-OCR is enabled, try other engine
        if settings.use_multi_ocr and result.confidence < settings.ocr_confidence_threshold:
            logger.info(f"Low confidence ({result.confidence:.2f}), trying alternative OCR")
            
            if is_handwritten:
                fallback_result = self.ocr_printed_text(image)
            else:
                fallback_result = self.ocr_handwritten_text(image)
            
            # Use result with higher confidence
            if fallback_result.confidence > result.confidence:
                logger.info(f"Fallback OCR performed better ({fallback_result.confidence:.2f})")
                return fallback_result
        
        return result
    
    def _detect_math_notation(self, text: str) -> bool:
        """Detect if text contains mathematical notation"""
        # Common math indicators
        math_patterns = [
            r'[∫∑∏√∞≠≤≥±×÷]',  # Math symbols
            r'[α-ωΑ-Ω]',  # Greek letters
            r'\^|\b\d+/\d+\b',  # Exponents or fractions
            r'\$.*?\$',  # LaTeX inline math
            r'\\[a-zA-Z]+\{',  # LaTeX commands
        ]
        
        for pattern in math_patterns:
            if re.search(pattern, text):
                return True
        
        return False
    
    def _extract_latex_equations(self, text: str) -> list:
        """Extract LaTeX equations from text"""
        # Find inline math ($...$)
        inline = re.findall(r'\$(.*?)\$', text)
        
        # Find display math ($$...$$)
        display = re.findall(r'\$\$(.*?)\$\$', text)
        
        return inline + display
    
    def needs_claude_vision(self, ocr_result: OCRResult) -> bool:
        """
        Determine if Claude Vision API is needed for better results
        
        Args:
            ocr_result: Result from local OCR
            
        Returns:
            True if Claude Vision should be used
        """
        return (
            ocr_result.confidence < settings.ocr_confidence_threshold or
            (ocr_result.has_handwriting and 
             ocr_result.confidence < settings.handwriting_detection_threshold) or
            ocr_result.quality == "poor"
        )

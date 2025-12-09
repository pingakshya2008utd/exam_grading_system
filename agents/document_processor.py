from pathlib import Path
from typing import List, Tuple
from PIL import Image
from loguru import logger

from utils.pdf_tools import PDFProcessor
from utils.image_tools import ImageProcessor
from config.settings import settings


class DocumentProcessorAgent:
    """Agent for PDF to image conversion and preprocessing"""
    
    def __init__(self):
        self.pdf_processor = PDFProcessor()
        self.image_processor = ImageProcessor()
    
    def process_document(self, pdf_path: str, 
                        output_subdir: str = "processed") -> Tuple[List[str], List[float]]:
        """
        Convert PDF to preprocessed images
        
        Args:
            pdf_path: Path to PDF file
            output_subdir: Subdirectory name in images folder
            
        Returns:
            (image_paths, quality_scores) tuple
        """
        logger.info(f"Processing document: {pdf_path}")
        
        # Convert PDF to images
        images = self.pdf_processor.convert_to_images(pdf_path)
        logger.info(f"Converted to {len(images)} images")
        
        # Preprocess each image
        processed_images = []
        quality_scores = []
        
        for i, img in enumerate(images, 1):
            logger.debug(f"Preprocessing page {i}/{len(images)}")
            
            # Preprocess for OCR
            processed = self.image_processor.preprocess_for_ocr(img)
            processed_images.append(processed)
            
            # Assess quality
            quality = self.image_processor.assess_image_quality(processed)
            quality_scores.append(quality)
            
            logger.debug(f"Page {i} quality score: {quality:.2f}")
        
        # Save processed images
        output_dir = settings.images_dir / output_subdir
        image_paths = self.pdf_processor.save_images(
            processed_images, 
            str(output_dir),
            prefix="page"
        )
        
        avg_quality = sum(quality_scores) / len(quality_scores)
        logger.success(f"Processed {len(images)} pages, avg quality: {avg_quality:.2f}")
        
        return image_paths, quality_scores

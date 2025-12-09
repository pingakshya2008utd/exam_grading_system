import fitz  # PyMuPDF
from pdf2image import convert_from_path
from pathlib import Path
from typing import List, Tuple
from PIL import Image
import pdfplumber
from loguru import logger

from config.settings import settings


class PDFProcessor:
    """Handle PDF to image conversion and text extraction"""
    
    def __init__(self, dpi: int = None):
        self.dpi = dpi or settings.dpi
    
    def convert_to_images(self, pdf_path: str) -> List[Image.Image]:
        """
        Convert PDF to list of PIL images
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            List of PIL Image objects
        """
        try:
            logger.info(f"Converting PDF to images at {self.dpi} DPI: {pdf_path}")
            images = convert_from_path(
                pdf_path,
                dpi=self.dpi,
                fmt='PNG',
                thread_count=4 if settings.parallel_processing else 1
            )
            logger.success(f"Converted {len(images)} pages to images")
            return images
        except Exception as e:
            logger.error(f"Failed to convert PDF to images: {e}")
            raise
    
    def get_page_count(self, pdf_path: str) -> int:
        """Get number of pages in PDF"""
        try:
            doc = fitz.open(pdf_path)
            count = len(doc)
            doc.close()
            return count
        except Exception as e:
            logger.error(f"Failed to get page count: {e}")
            raise
    
    def extract_text_pymupdf(self, pdf_path: str) -> List[str]:
        """
        Extract text from PDF using PyMuPDF (good for printed text)
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            List of text strings, one per page
        """
        try:
            doc = fitz.open(pdf_path)
            texts = []
            for page_num in range(len(doc)):
                page = doc[page_num]
                text = page.get_text()
                texts.append(text)
            doc.close()
            logger.info(f"Extracted text from {len(texts)} pages")
            return texts
        except Exception as e:
            logger.error(f"Failed to extract text with PyMuPDF: {e}")
            raise
    
    def extract_text_pdfplumber(self, pdf_path: str) -> List[str]:
        """
        Extract text from PDF using pdfplumber (good for tables)
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            List of text strings, one per page
        """
        try:
            texts = []
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    text = page.extract_text()
                    texts.append(text if text else "")
            logger.info(f"Extracted text from {len(texts)} pages with pdfplumber")
            return texts
        except Exception as e:
            logger.error(f"Failed to extract text with pdfplumber: {e}")
            raise
    
    def save_images(self, images: List[Image.Image], output_dir: str, 
                   prefix: str = "page") -> List[str]:
        """
        Save PIL images to files
        
        Args:
            images: List of PIL images
            output_dir: Directory to save images
            prefix: Filename prefix
            
        Returns:
            List of saved file paths
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        saved_paths = []
        for i, img in enumerate(images, 1):
            filepath = output_path / f"{prefix}_{i:03d}.png"
            img.save(filepath, "PNG", quality=95, optimize=False)
            saved_paths.append(str(filepath))
            logger.debug(f"Saved image: {filepath}")
        
        logger.success(f"Saved {len(saved_paths)} images to {output_dir}")
        return saved_paths

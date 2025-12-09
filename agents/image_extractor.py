from PIL import Image
from pathlib import Path
from typing import List, Dict
from loguru import logger
import uuid

from utils.image_tools import ImageProcessor
from utils.vision_api import ClaudeVisionAPI
from models.schemas import Diagram, BoundingBox
from config.settings import settings


class ImageExtractorAgent:
    """Agent for extracting diagrams and figures from documents"""
    
    def __init__(self):
        self.image_processor = ImageProcessor()
        self.vision_api = ClaudeVisionAPI()
    
    def extract_diagrams_from_pages(self, image_paths: List[str],
                                    output_dir: str = None) -> List[List[Diagram]]:
        """
        Extract diagrams from multiple pages
        
        Args:
            image_paths: List of page image paths
            output_dir: Directory to save extracted diagrams
            
        Returns:
            List of diagram lists (one list per page)
        """
        if output_dir is None:
            output_dir = str(settings.images_dir / "diagrams")
        
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Extracting diagrams from {len(image_paths)} pages")
        
        all_diagrams = []
        total_diagrams = 0
        
        for page_num, path in enumerate(image_paths, 1):
            logger.debug(f"Processing page {page_num}/{len(image_paths)}")
            
            image = Image.open(path)
            
            # Choose extraction method
            if settings.use_ai_diagram_detection:
                diagrams = self._extract_with_ai(image, page_num, output_dir)
            else:
                diagrams = self._extract_with_cv(image, page_num, output_dir)
            
            all_diagrams.append(diagrams)
            total_diagrams += len(diagrams)
            
            if diagrams:
                logger.info(f"Page {page_num}: extracted {len(diagrams)} diagrams")
        
        logger.success(f"Extracted {total_diagrams} diagrams total")
        return all_diagrams
    
    def _extract_with_ai(self, image: Image.Image, page_num: int,
                        output_dir: str) -> List[Diagram]:
        """Extract diagrams using Claude Vision AI"""
        try:
            # Detect diagrams with AI
            detected = self.vision_api.detect_diagrams(image)
            
            diagrams = []
            for i, det in enumerate(detected):
                try:
                    # Parse bounding box
                    bbox_dict = det.get('bbox', {})
                    bbox = BoundingBox(
                        x_min=bbox_dict.get('x_min', 0),
                        y_min=bbox_dict.get('y_min', 0),
                        x_max=bbox_dict.get('x_max', 100),
                        y_max=bbox_dict.get('y_max', 100)
                    )
                    
                    # Crop diagram
                    cropped = self.image_processor.crop_region(
                        image,
                        (bbox.x_min, bbox.y_min, bbox.x_max, bbox.y_max)
                    )
                    
                    # Assess quality
                    quality = self.image_processor.assess_image_quality(cropped)
                    quality_score = min(quality / 100.0, 1.0)
                    
                    # Save diagram
                    diagram_id = f"p{page_num}_d{i+1}_{uuid.uuid4().hex[:8]}"
                    diagram_path = f"{output_dir}/{diagram_id}.png"
                    cropped.save(diagram_path)
                    
                    # Create Diagram object
                    diagram = Diagram(
                        diagram_id=diagram_id,
                        type=det.get('type', 'unknown'),
                        description=det.get('description', ''),
                        bbox=bbox,
                        image_path=diagram_path,
                        relevance=det.get('relevance', 'medium'),
                        quality_score=quality_score
                    )
                    
                    diagrams.append(diagram)
                    
                except Exception as e:
                    logger.warning(f"Failed to process diagram {i}: {e}")
                    continue
            
            return diagrams
            
        except Exception as e:
            logger.error(f"AI diagram extraction failed: {e}")
            return []
    
    def _extract_with_cv(self, image: Image.Image, page_num: int,
                        output_dir: str) -> List[Diagram]:
        """Extract diagrams using OpenCV (faster but less accurate)"""
        try:
            # Extract diagrams with OpenCV
            extracted = self.image_processor.extract_diagram_cv(
                image,
                min_size=settings.min_diagram_size
            )
            
            diagrams = []
            for i, (diagram_cv, bbox_pixels) in enumerate(extracted):
                try:
                    # Convert pixel bbox to percentage
                    x, y, w, h = bbox_pixels
                    img_width, img_height = image.size
                    
                    bbox = BoundingBox(
                        x_min=(x / img_width) * 100,
                        y_min=(y / img_height) * 100,
                        x_max=((x + w) / img_width) * 100,
                        y_max=((y + h) / img_height) * 100
                    )
                    
                    # Convert to PIL
                    diagram_pil = self.image_processor.cv2_to_pil(diagram_cv)
                    
                    # Assess quality
                    quality = self.image_processor.assess_image_quality(diagram_pil)
                    quality_score = min(quality / 100.0, 1.0)
                    
                    # Skip low quality
                    if quality < settings.image_quality_threshold:
                        logger.debug(f"Skipping low quality diagram (score: {quality:.2f})")
                        continue
                    
                    # Save diagram
                    diagram_id = f"p{page_num}_d{i+1}_{uuid.uuid4().hex[:8]}"
                    diagram_path = f"{output_dir}/{diagram_id}.png"
                    diagram_pil.save(diagram_path)
                    
                    # Create Diagram object
                    diagram = Diagram(
                        diagram_id=diagram_id,
                        type='detected',  # Type unknown with CV method
                        description='Automatically detected diagram',
                        bbox=bbox,
                        image_path=diagram_path,
                        relevance='medium',
                        quality_score=quality_score
                    )
                    
                    diagrams.append(diagram)
                    
                except Exception as e:
                    logger.warning(f"Failed to process diagram {i}: {e}")
                    continue
            
            return diagrams
            
        except Exception as e:
            logger.error(f"OpenCV diagram extraction failed: {e}")
            return []

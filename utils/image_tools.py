import cv2
import numpy as np
from PIL import Image
from typing import Tuple, List, Optional
from loguru import logger
from skimage.filters import threshold_local


class ImageProcessor:
    """Handle image preprocessing and enhancement"""
    
    @staticmethod
    def pil_to_cv2(pil_image: Image.Image) -> np.ndarray:
        """Convert PIL Image to OpenCV format"""
        return cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
    
    @staticmethod
    def cv2_to_pil(cv2_image: np.ndarray) -> Image.Image:
        """Convert OpenCV image to PIL format"""
        return Image.fromarray(cv2.cvtColor(cv2_image, cv2.COLOR_BGR2RGB))
    
    def preprocess_for_ocr(self, image: Image.Image) -> Image.Image:
        """
        Preprocess image for optimal OCR results
        
        Steps:
        1. Deskew
        2. Denoise
        3. Contrast enhancement
        4. Sharpen
        
        Args:
            image: PIL Image
            
        Returns:
            Preprocessed PIL Image
        """
        try:
            # Convert to OpenCV
            img_cv = self.pil_to_cv2(image)
            
            # Convert to grayscale
            gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
            
            # Skip deskewing - it's slow
            # gray = self._deskew(gray)
            
            # Skip denoising - it's VERY slow (can take 20+ seconds per image)
            # denoised = cv2.fastNlMeansDenoising(gray, None, h=10, 
            #                                    templateWindowSize=7, 
            #                                    searchWindowSize=21)
            
            # Contrast enhancement (CLAHE)
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            enhanced = clahe.apply(gray)
            
            # Sharpen
            kernel = np.array([[-1, -1, -1],
                             [-1,  9, -1],
                             [-1, -1, -1]])
            sharpened = cv2.filter2D(enhanced, -1, kernel)
            
            # Convert back to PIL
            return Image.fromarray(sharpened)
            
        except Exception as e:
            logger.warning(f"Preprocessing failed, returning original: {e}")
            return image
    
    def _deskew(self, image: np.ndarray) -> np.ndarray:
        """Deskew image using Hough Line Transform"""
        try:
            # Edge detection
            edges = cv2.Canny(image, 50, 150, apertureSize=3)
            
            # Hough Line Transform
            lines = cv2.HoughLines(edges, 1, np.pi / 180, 200)
            
            if lines is None:
                return image
            
            # Calculate average angle
            angles = []
            for rho, theta in lines[:, 0]:
                angle = np.degrees(theta) - 90
                angles.append(angle)
            
            median_angle = np.median(angles)
            
            # Rotate image if skew is significant
            if abs(median_angle) > 0.5:
                (h, w) = image.shape[:2]
                center = (w // 2, h // 2)
                M = cv2.getRotationMatrix2D(center, median_angle, 1.0)
                rotated = cv2.warpAffine(image, M, (w, h),
                                        flags=cv2.INTER_CUBIC,
                                        borderMode=cv2.BORDER_REPLICATE)
                return rotated
            
            return image
            
        except Exception as e:
            logger.debug(f"Deskew failed: {e}")
            return image
    
    def extract_diagram_cv(self, image: Image.Image, 
                          min_size: int = 5000) -> List[Tuple[np.ndarray, Tuple[int, int, int, int]]]:
        """
        Extract diagrams using OpenCV contour detection
        
        Args:
            image: PIL Image
            min_size: Minimum area for a valid diagram
            
        Returns:
            List of (cropped_image, bbox) tuples
        """
        try:
            img_cv = self.pil_to_cv2(image)
            gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
            
            # Threshold
            _, binary = cv2.threshold(gray, 0, 255, 
                                     cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
            
            # Find contours
            contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, 
                                          cv2.CHAIN_APPROX_SIMPLE)
            
            diagrams = []
            for contour in contours:
                area = cv2.contourArea(contour)
                if area < min_size:
                    continue
                
                x, y, w, h = cv2.boundingRect(contour)
                
                # Filter out text-like regions (very wide or very tall)
                aspect_ratio = w / h
                if aspect_ratio > 10 or aspect_ratio < 0.1:
                    continue
                
                # Crop diagram
                cropped = img_cv[y:y+h, x:x+w]
                diagrams.append((cropped, (x, y, w, h)))
            
            logger.info(f"Extracted {len(diagrams)} diagrams using OpenCV")
            return diagrams
            
        except Exception as e:
            logger.error(f"Diagram extraction failed: {e}")
            return []
    
    def crop_region(self, image: Image.Image, 
                   bbox: Tuple[float, float, float, float]) -> Image.Image:
        """
        Crop image region based on percentage-based bounding box
        
        Args:
            image: PIL Image
            bbox: (x_min%, y_min%, x_max%, y_max%) as 0-100 percentages
            
        Returns:
            Cropped PIL Image
        """
        width, height = image.size
        x_min, y_min, x_max, y_max = bbox
        
        # Convert percentages to pixels
        left = int(x_min * width / 100)
        top = int(y_min * height / 100)
        right = int(x_max * width / 100)
        bottom = int(y_max * height / 100)
        
        return image.crop((left, top, right, bottom))
    
    def assess_image_quality(self, image: Image.Image) -> float:
        """
        Assess image quality using Laplacian variance
        
        Args:
            image: PIL Image
            
        Returns:
            Quality score (higher is better, >50 is good)
        """
        try:
            img_cv = self.pil_to_cv2(image)
            gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
            
            # Calculate Laplacian variance
            laplacian = cv2.Laplacian(gray, cv2.CV_64F)
            score = laplacian.var()
            
            return float(score)
            
        except Exception as e:
            logger.warning(f"Quality assessment failed: {e}")
            return 0.0

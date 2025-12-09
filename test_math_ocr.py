#!/usr/bin/env python3
"""
Test mathematical OCR on answer sheet pages
"""
import sys
from pathlib import Path
from loguru import logger

logger.remove()
logger.add(sys.stderr, level="INFO")

from utils.math_ocr import MathOCR
from config.settings import settings

# Get answer sheet images
images_dir = settings.images_dir / "answer_A1_solution"
image_paths = sorted(list(images_dir.glob("*.png")))

print(f"\nFound {len(image_paths)} answer sheet images")
print("Looking for pages with Question 6...")

# Based on the previous run, Q6 solution likely spans multiple pages
# Let's extract from pages that might contain Q6 (typically mid-pages)
# We'll extract from pages 5-8 to catch Q6 content

math_ocr = MathOCR()

# Q7 was found on page 6, so Q6 should be on page 5
selected_pages = [4]  # 0-indexed: page 5  
pages_to_process = [image_paths[i] for i in selected_pages if i < len(image_paths)]

print(f"\nProcessing page 5 with enhanced math OCR (Claude Vision)...")

for i, img_path in enumerate(pages_to_process):
    page_num = selected_pages[i] + 1
    print(f"\n{'='*80}")
    print(f"PAGE {page_num}: {img_path.name}")
    print(f"{'='*80}")
    
    text = math_ocr.extract_math(img_path)
    
    if text:
        print(text)
        
        # Check if this contains Solution 6
        if "solution 6" in text.lower() or "question 6" in text.lower() or "q6" in text.lower():
            print(f"\n✓ Found Question 6 content on page {page_num}!")
    else:
        print(f"❌ Extraction failed for page {page_num}")

print(f"\n{'='*80}")
print("Extraction complete!")

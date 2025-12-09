#!/usr/bin/env python3
"""
Debug OCR output to see exact text structure
"""

import sys
from loguru import logger
logger.remove()
logger.add(sys.stderr, level="INFO")

from agents import OCRAgent
from config.settings import settings

# Get images
images_dir = settings.images_dir / "question_paper"
image_paths = sorted(list(images_dir.glob("*.png")))

# OCR
ocr_agent = OCRAgent()
ocr_results = ocr_agent.process_images(image_paths, is_handwritten=False)

# Print full text
full_text = "\n\n=== PAGE BREAK ===\n\n".join([r.text for r in ocr_results])

print("\n=== FULL OCR TEXT ===\n")
print(full_text)
print("\n=== END ===\n")

# Find all marks indicators
import re
marks_pattern = r'\((\d+)\s*Marks?\)'
marks_matches = list(re.finditer(marks_pattern, full_text, re.IGNORECASE))

print(f"\nFound {len(marks_matches)} marks indicators:")
for i, m in enumerate(marks_matches, 1):
    print(f"{i}. Position {m.start()}-{m.end()}: {m.group()} = {m.group(1)} marks")
    # Show context
    start = max(0, m.start() - 80)
    end = min(len(full_text), m.end() + 20)
    context = full_text[start:end].replace('\n', ' ')
    print(f"   Context: ...{context}...")

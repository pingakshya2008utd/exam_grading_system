#!/usr/bin/env python3
"""
Quick update: Extract Q6 and Q8 with Claude Vision and update answer sheet
"""
import sys
import json
from pathlib import Path
from loguru import logger

logger.remove()
logger.add(sys.stderr, level="INFO")

from utils.math_ocr import MathOCR
from config.settings import settings

print("\nExtracting Q6 and Q8 with Claude Vision API...")

math_ocr = MathOCR()
images_dir = settings.images_dir / "answer_A1_solution"
image_paths = sorted(list(images_dir.glob("*.png")))

# Extract Q6 from page 5 (index 4)
print("\n[1/4] Extracting Q6 from page 5...")
q6_text = math_ocr.extract_math(image_paths[4])

# Extract Q8 from pages 8-12 (indices 7-11)
print("\n[2/4] Extracting Q8 from page 8...")
q8_p1 = math_ocr.extract_math(image_paths[7])

print("\n[3/4] Extracting Q8 from page 11...")
q8_p2 = math_ocr.extract_math(image_paths[10])

print("\n[4/4] Extracting Q8 from page 12...")
q8_p3 = math_ocr.extract_math(image_paths[11])

# Combine Q8 parts
q8_text = f"{q8_p1}\n\n{q8_p2}\n\n{q8_p3}"

print(f"\n✓ Q6 extracted: {len(q6_text)} chars")
print(f"✓ Q8 extracted: {len(q8_text)} chars (from 3 pages)")

# Update answer sheet
answer_sheet_file = settings.output_dir / "answer_sheet_A1_solution.json"
with open(answer_sheet_file, 'r') as f:
    answer_data = json.load(f)

for answer in answer_data['answers']:
    if answer['question_number'] == '6' and q6_text:
        answer['answer_text'] = q6_text.strip()
        print(f"\n✓ Updated Q6 in answer sheet")
    elif answer['question_number'] == '8' and q8_text:
        answer['answer_text'] = q8_text.strip()
        print(f"✓ Updated Q8 in answer sheet")

with open(answer_sheet_file, 'w') as f:
    json.dump(answer_data, f, indent=2)

print(f"\n✓ Answer sheet updated: {answer_sheet_file}")
print("\nNow run: python regrade.py")

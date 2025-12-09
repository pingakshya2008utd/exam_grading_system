#!/usr/bin/env python3
"""
Enhanced answer extraction using Claude Vision API for complex mathematical content
"""
import sys
from pathlib import Path
from loguru import logger

logger.remove()
logger.add(sys.stderr, level="INFO")

from utils.math_ocr import MathOCR
from agents.ocr_agent import OCRAgent
from config.settings import settings
import json

# Get answer sheet images
images_dir = settings.images_dir / "answer_A1_solution"
image_paths = sorted(list(images_dir.glob("*.png")))

print(f"\nProcessing {len(image_paths)} answer sheet images...")
print("Using Claude Vision API for Q6 and Q8 (complex mathematical content)")

# Use Vision API for specific pages containing Q6 and Q8
math_ocr = MathOCR()

# Map of pages to extract with Vision API (0-indexed)
vision_pages = {
    4: "Q5b + Q6",  # Page 5
    5: "Q7",        # Page 6  
    6: "Q7 cont",   # Page 7
    7: "Q8 start",  # Page 8
    8: "Q8 plots",  # Page 9
    9: "Q8 plots",  # Page 10
    10: "Q8 conclusions", # Page 11
    11: "Q8 code"   # Page 12
}

# Extract text from all pages using Vision API for better accuracy
print("\n" + "="*80)
print("EXTRACTING WITH CLAUDE VISION API")
print("="*80)

all_page_texts = []
for i, img_path in enumerate(image_paths):
    page_num = i + 1
    
    if i in vision_pages:
        print(f"\n📄 Page {page_num} ({vision_pages[i]})...")
        text = math_ocr.extract_math(img_path)
        if text:
            all_page_texts.append({
                'page': page_num,
                'text': text,
                'method': 'vision_api'
            })
            print(f"✓ Extracted {len(text)} characters")
    else:
        # Use regular OCR for simpler pages
        print(f"\n📄 Page {page_num} (using regular OCR)...")
        ocr_agent = OCRAgent()
        result = ocr_agent.process_single_image(str(img_path), is_handwritten=True)
        all_page_texts.append({
            'page': page_num,
            'text': result.text,
            'method': 'regular_ocr'
        })
        print(f"✓ Extracted {len(result.text)} characters (confidence: {result.confidence:.2f})")

# Combine all text
full_text = "\n\n=== PAGE BREAK ===\n\n".join([p['text'] for p in all_page_texts])

print(f"\n" + "="*80)
print(f"Total extracted text: {len(full_text)} characters")
print("="*80)

# Now extract answers using improved pattern matching
question_numbers = ['1', '2', '3', '4', '5', '6', '7', '8']

# Manual extraction based on content analysis
answers_data = []

# Find Q6 (should be on pages 5-6)
q6_text = ""
for p in all_page_texts:
    if "Solution 6" in p['text'] or "ψ(k)" in p['text']:
        q6_text += p['text'] + "\n"

# Find Q7 (should be on pages 6-7)
q7_text = ""
for p in all_page_texts:
    if p['page'] in [6, 7] and ("normalization" in p['text'].lower() or "stationary" in p['text'].lower()):
        q7_text += p['text'] + "\n"

# Find Q8 (should be on pages 8-12)
q8_text = ""
for p in all_page_texts:
    if p['page'] >= 8 and ("transmission" in p['text'].lower() or "matlab" in p['text'].lower() or "plot" in p['text'].lower()):
        q8_text += p['text'] + "\n"

print(f"\n✓ Q6 extracted: {len(q6_text)} chars")
print(f"✓ Q7 extracted: {len(q7_text)} chars")
print(f"✓ Q8 extracted: {len(q8_text)} chars")

# Save enhanced extraction results
output_file = settings.output_dir / "enhanced_answers.json"
output_data = {
    "q6_text": q6_text,
    "q7_text": q7_text,
    "q8_text": q8_text,
    "all_pages": all_page_texts
}

with open(output_file, 'w') as f:
    json.dump(output_data, f, indent=2)

print(f"\n✓ Saved enhanced extraction to: {output_file}")
print("\nNow updating answer sheet JSON with improved Q6 and Q8 extraction...")

# Update the answer sheet JSON
answer_sheet_file = settings.output_dir / "answer_sheet_A1_solution.json"
if answer_sheet_file.exists():
    with open(answer_sheet_file, 'r') as f:
        answer_data = json.load(f)
    
    # Update Q6 and Q8 answers
    for answer in answer_data['answers']:
        if answer['question_number'] == '6':
            answer['answer_text'] = q6_text.strip() if q6_text else answer['answer_text']
            print(f"✓ Updated Q6 answer ({len(q6_text)} chars)")
        elif answer['question_number'] == '7':
            answer['answer_text'] = q7_text.strip() if q7_text else answer['answer_text']
            print(f"✓ Updated Q7 answer ({len(q7_text)} chars)")
        elif answer['question_number'] == '8':
            answer['answer_text'] = q8_text.strip() if q8_text else answer['answer_text']
            print(f"✓ Updated Q8 answer ({len(q8_text)} chars)")
    
    # Save updated answer sheet
    with open(answer_sheet_file, 'w') as f:
        json.dump(answer_data, f, indent=2)
    
    print(f"\n✓ Updated answer sheet saved to: {answer_sheet_file}")

print("\n" + "="*80)
print("ENHANCED EXTRACTION COMPLETE!")
print("="*80)
print("\nYou can now run grading with:")
print("  python regrade.py")

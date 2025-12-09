#!/usr/bin/env python3
"""
Test question paper re-processing with fixed structure analyzer
"""

import sys
from pathlib import Path
from loguru import logger

# Setup logging
logger.remove()
logger.add(sys.stderr, level="INFO", colorize=True)

from agents import DocumentProcessorAgent, OCRAgent, ImageExtractorAgent, StructureAnalyzerAgent, JSONGeneratorAgent
from config.settings import settings

def main():
    logger.info("Re-processing question paper with fixed structure analyzer...")
    
    # Initialize agents
    doc_processor = DocumentProcessorAgent()
    ocr_agent = OCRAgent()
    image_extractor = ImageExtractorAgent()
    structure_analyzer = StructureAnalyzerAgent()
    json_generator = JSONGeneratorAgent()
    
    # Use existing images if available
    question_paper_images_dir = settings.images_dir / "question_paper"
    
    if question_paper_images_dir.exists():
        logger.info("Using existing question paper images...")
        image_paths = sorted(list(question_paper_images_dir.glob("*.png")))
    else:
        logger.info("Processing question paper PDF...")
        image_paths, _ = doc_processor.process_document("A1.pdf", output_subdir="question_paper")
    
    # OCR
    logger.info("Performing OCR...")
    ocr_results = ocr_agent.process_images(image_paths, is_handwritten=False)
    
    # Extract diagrams
    logger.info("Extracting diagrams...")
    diagrams_by_page = image_extractor.extract_diagrams_from_pages(
        image_paths,
        output_dir=str(settings.images_dir / "question_diagrams")
    )
    
    # Analyze structure with FIXED parser
    logger.info("Analyzing structure with improved parser...")
    metadata, questions = structure_analyzer.analyze_question_paper(ocr_results, diagrams_by_page)
    
    logger.success(f"Found {len(questions)} questions!")
    
    # Show question summary
    for i, q in enumerate(questions, 1):
        logger.info(f"Q{q.question_number}: {q.marks} marks - {q.question_text[:80]}...")
    
    # Generate JSON
    json_path = json_generator.generate_question_paper_json(metadata, questions, 0)
    logger.success(f"Saved to: {json_path}")
    
    return json_path

if __name__ == "__main__":
    main()

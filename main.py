#!/usr/bin/env python3
"""
Exam Grading System - Main Pipeline
Orchestrates the complete workflow from PDF to graded results
"""

import time
import sys
from pathlib import Path
from typing import List, Optional
from loguru import logger
import json

from config.settings import settings
from agents import (DocumentProcessorAgent, OCRAgent, ImageExtractorAgent,
                   StructureAnalyzerAgent, JSONGeneratorAgent, GradingAgent)


class ExamGradingPipeline:
    """Main pipeline for exam grading system"""
    
    def __init__(self):
        # Initialize all agents
        self.doc_processor = DocumentProcessorAgent()
        self.ocr_agent = OCRAgent()
        self.image_extractor = ImageExtractorAgent()
        self.structure_analyzer = StructureAnalyzerAgent()
        self.json_generator = JSONGeneratorAgent()
        self.grading_agent = GradingAgent()
        
        logger.info("Exam Grading Pipeline initialized")
    
    def process_question_paper(self, pdf_path: str) -> str:
        """
        Process question paper PDF
        
        Args:
            pdf_path: Path to question paper PDF
            
        Returns:
            Path to generated JSON file
        """
        logger.info("=" * 80)
        logger.info("PROCESSING QUESTION PAPER")
        logger.info("=" * 80)
        
        start_time = time.time()
        
        # Stage 1: Document preprocessing
        logger.info("[1/4] Converting PDF to images and preprocessing...")
        image_paths, quality_scores = self.doc_processor.process_document(
            pdf_path, 
            output_subdir="question_paper"
        )
        
        # Stage 2: OCR
        logger.info("[2/4] Performing OCR on printed text...")
        ocr_results = self.ocr_agent.process_images(image_paths, is_handwritten=False)
        
        # Stage 3: Diagram extraction
        logger.info("[3/4] Extracting diagrams and figures...")
        diagrams_by_page = self.image_extractor.extract_diagrams_from_pages(
            image_paths,
            output_dir=str(settings.images_dir / "question_diagrams")
        )
        
        # Stage 4: Structure analysis
        logger.info("[4/4] Analyzing question structure...")
        metadata, questions = self.structure_analyzer.analyze_question_paper(
            ocr_results,
            diagrams_by_page
        )
        
        # Generate JSON
        processing_time = time.time() - start_time
        json_path = self.json_generator.generate_question_paper_json(
            metadata,
            questions,
            processing_time
        )
        
        logger.success(f"Question paper processed in {processing_time:.2f}s")
        logger.info(f"JSON saved to: {json_path}")
        
        return json_path
    
    def process_solution_paper(self, pdf_path: str) -> str:
        """
        Process solution paper PDF
        
        Args:
            pdf_path: Path to solution paper PDF
            
        Returns:
            Path to generated JSON file
        """
        logger.info("=" * 80)
        logger.info("PROCESSING SOLUTION PAPER")
        logger.info("=" * 80)
        
        start_time = time.time()
        
        # Stage 1: Document preprocessing
        logger.info("[1/4] Converting PDF to images and preprocessing...")
        image_paths, quality_scores = self.doc_processor.process_document(
            pdf_path,
            output_subdir="solution_paper"
        )
        
        # Stage 2: OCR (may include handwriting)
        logger.info("[2/4] Performing OCR...")
        ocr_results = self.ocr_agent.process_images(image_paths, is_handwritten=True)
        
        # Stage 3: Diagram extraction
        logger.info("[3/4] Extracting diagrams and figures...")
        diagrams_by_page = self.image_extractor.extract_diagrams_from_pages(
            image_paths,
            output_dir=str(settings.images_dir / "solution_diagrams")
        )
        
        # Stage 4: Structure analysis
        logger.info("[4/4] Analyzing solution structure...")
        metadata, solutions = self.structure_analyzer.analyze_question_paper(
            ocr_results,
            diagrams_by_page
        )
        
        # Generate JSON
        processing_time = time.time() - start_time
        json_path = self.json_generator.generate_solution_json(
            metadata,
            solutions,
            processing_time
        )
        
        logger.success(f"Solution paper processed in {processing_time:.2f}s")
        logger.info(f"JSON saved to: {json_path}")
        
        return json_path
    
    def process_answer_sheet(self, pdf_path: str, 
                           question_numbers: List[str]) -> str:
        """
        Process student answer sheet PDF
        
        Args:
            pdf_path: Path to answer sheet PDF
            question_numbers: Expected question numbers
            
        Returns:
            Path to generated JSON file
        """
        logger.info("=" * 80)
        logger.info(f"PROCESSING ANSWER SHEET: {Path(pdf_path).name}")
        logger.info("=" * 80)
        
        start_time = time.time()
        
        # Stage 1: Document preprocessing
        logger.info("[1/4] Converting PDF to images and preprocessing...")
        image_paths, quality_scores = self.doc_processor.process_document(
            pdf_path,
            output_subdir=f"answer_{Path(pdf_path).stem}"
        )
        
        # Stage 2: OCR (handwritten)
        logger.info("[2/4] Performing handwriting OCR...")
        ocr_results = self.ocr_agent.process_images(image_paths, is_handwritten=True)
        
        # Stage 3: Diagram extraction
        logger.info("[3/4] Extracting diagrams...")
        diagrams_by_page = self.image_extractor.extract_diagrams_from_pages(
            image_paths,
            output_dir=str(settings.images_dir / f"answer_diagrams_{Path(pdf_path).stem}")
        )
        
        # Stage 4: Structure analysis
        logger.info("[4/4] Extracting student answers...")
        student_info, answers = self.structure_analyzer.analyze_answer_sheet(
            ocr_results,
            diagrams_by_page,
            question_numbers
        )
        
        # Generate JSON
        processing_time = time.time() - start_time
        json_path = self.json_generator.generate_answer_sheet_json(
            student_info,
            answers,
            processing_time,
            student_id=student_info.get('id', Path(pdf_path).stem)
        )
        
        logger.success(f"Answer sheet processed in {processing_time:.2f}s")
        logger.info(f"JSON saved to: {json_path}")
        
        return json_path
    
    def grade_answer_sheet(self, question_json: str, solution_json: Optional[str],
                          answer_json: str) -> str:
        """
        Grade student answer sheet
        
        Args:
            question_json: Path to question paper JSON
            solution_json: Path to solution paper JSON (optional)
            answer_json: Path to answer sheet JSON
            
        Returns:
            Path to grading report JSON
        """
        logger.info("=" * 80)
        logger.info("GRADING ANSWER SHEET")
        logger.info("=" * 80)
        
        start_time = time.time()
        
        # Load JSONs
        if solution_json:
            logger.info("Loading question paper, solution paper, and answer sheet...")
            question_data = self.json_generator.load_json(question_json)
            solution_data = self.json_generator.load_json(solution_json)
            answer_data = self.json_generator.load_json(answer_json)
        else:
            logger.info("Loading question paper and answer sheet (no solution paper)...")
            question_data = self.json_generator.load_json(question_json)
            answer_data = self.json_generator.load_json(answer_json)
        
        # Parse data structures
        from models.schemas import Question, Answer
        
        questions = []
        if solution_json:
            # Use solution paper if available
            for q_dict in solution_data['solutions']:
                questions.append(Question(**q_dict))
        else:
            # Use question paper data without solutions
            for q_dict in question_data['questions']:
                questions.append(Question(**q_dict))
        
        answers = []
        for a_dict in answer_data['answers']:
            answers.append(Answer(**a_dict))
        
        student_info = answer_data['student_info']
        
        # Grade
        logger.info(f"Grading {len(answers)} answers...")
        report = self.grading_agent.grade_answer_sheet(questions, answers, student_info)
        
        # Update processing time
        report.processing_time = time.time() - start_time
        
        # Save grading report
        student_id = student_info.get('id', 'unknown')
        output_path = settings.output_dir / f"grading_report_{student_id}.json"
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report.model_dump(), f, indent=2, default=str)
        
        logger.success(f"Grading complete in {report.processing_time:.2f}s")
        logger.info(f"Report saved to: {output_path}")
        
        # Print summary
        self._print_grading_summary(report)
        
        return str(output_path)
    
    def _print_grading_summary(self, report):
        """Print grading summary to console"""
        logger.info("\n" + "=" * 80)
        logger.info("GRADING SUMMARY")
        logger.info("=" * 80)
        logger.info(f"Student: {report.student_info.get('name', 'Unknown')}")
        logger.info(f"ID: {report.student_info.get('id', 'Unknown')}")
        logger.info(f"Total: {report.total_marks_awarded:.1f}/{report.total_marks_available:.1f}")
        logger.info(f"Percentage: {report.percentage:.2f}%")
        logger.info(f"Grade: {report.grade}")
        logger.info(f"API Cost: ${report.api_cost:.4f}")
        logger.info("-" * 80)
        
        # Question-by-question breakdown
        for result in report.results:
            status = "✓" if result.is_correct else "✗"
            logger.info(f"{status} Q{result.question_number}: "
                       f"{result.marks_awarded:.1f}/{result.marks_available:.1f} "
                       f"[{result.grading_method}]")
            if settings.verbose:
                logger.info(f"   Feedback: {result.feedback}")
        
        logger.info("=" * 80 + "\n")


def setup_logging():
    """Configure logging"""
    logger.remove()  # Remove default handler
    
    # Console handler
    logger.add(
        sys.stderr,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
        level=settings.log_level,
        colorize=True
    )
    
    # File handler
    log_file = settings.logs_dir / f"grading_{time.strftime('%Y%m%d_%H%M%S')}.log"
    logger.add(
        log_file,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {message}",
        level="DEBUG",
        rotation="10 MB"
    )
    
    logger.info(f"Logging to: {log_file}")


def main():
    """Main entry point"""
    
    # Hardcoded paths - modify these for your exam files
    QUESTION_PAPER_PDF = "A1.pdf"  # Path to question paper
    ANSWER_SHEET_PDF = "A1_solution.pdf"      # Path to student answer sheet
    SOLUTION_PAPER_PDF = None  # Optional: Set to path of solution PDF if available, or None
    
    # Setup logging
    setup_logging()
    
    # Initialize pipeline
    pipeline = ExamGradingPipeline()
    
    try:
        # Process question paper
        logger.info("Processing hardcoded question paper...")
        question_json = pipeline.process_question_paper(QUESTION_PAPER_PDF)
        
        # Process solution paper (optional)
        solution_json = None
        if SOLUTION_PAPER_PDF:
            logger.info("Processing hardcoded solution paper...")
            solution_json = pipeline.process_solution_paper(SOLUTION_PAPER_PDF)
        else:
            logger.info("No solution paper provided - AI will grade based on question paper only")
        
        # Get question numbers for answer sheet processing
        data = pipeline.json_generator.load_json(question_json)
        question_numbers = [q['question_number'] for q in data['questions']]
        
        # Process answer sheet
        logger.info("Processing hardcoded answer sheet...")
        answer_json = pipeline.process_answer_sheet(ANSWER_SHEET_PDF, question_numbers)
        
        # Grade the answer sheet
        pipeline.grade_answer_sheet(question_json, solution_json, answer_json)
        
        logger.success("All processing complete!")
        
    except Exception as e:
        logger.exception(f"Pipeline failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

import json
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime
from loguru import logger

from models.schemas import (QuestionPaperJSON, SolutionPaperJSON, AnswerSheetJSON,
                            ExamMetadata, Question, Answer, ProcessingMetrics)
from config.settings import settings


class JSONGeneratorAgent:
    """Agent for generating structured JSON outputs"""
    
    def generate_question_paper_json(self, metadata: ExamMetadata,
                                    questions: List[Question],
                                    processing_time: float,
                                    output_filename: str = "question_paper.json") -> str:
        """
        Generate JSON for question paper
        
        Args:
            metadata: Exam metadata
            questions: List of questions
            processing_time: Time taken to process
            output_filename: Output filename
            
        Returns:
            Path to saved JSON file
        """
        logger.info(f"Generating question paper JSON with {len(questions)} questions")
        
        question_paper = QuestionPaperJSON(
            metadata=metadata,
            questions=questions,
            total_questions=len(questions),
            processing_time=processing_time,
            created_at=datetime.now()
        )
        
        # Save to file
        output_path = settings.output_dir / output_filename
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(question_paper.model_dump(), f, indent=2, default=str)
        
        logger.success(f"Question paper JSON saved to: {output_path}")
        return str(output_path)
    
    def generate_solution_json(self, metadata: ExamMetadata,
                              solutions: List[Question],
                              processing_time: float,
                              output_filename: str = "solution_paper.json") -> str:
        """
        Generate JSON for solution paper
        
        Args:
            metadata: Exam metadata
            solutions: List of questions with solutions
            processing_time: Time taken to process
            output_filename: Output filename
            
        Returns:
            Path to saved JSON file
        """
        logger.info(f"Generating solution paper JSON with {len(solutions)} solutions")
        
        solution_paper = SolutionPaperJSON(
            metadata=metadata,
            solutions=solutions,
            total_questions=len(solutions),
            processing_time=processing_time,
            created_at=datetime.now()
        )
        
        # Save to file
        output_path = settings.output_dir / output_filename
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(solution_paper.model_dump(), f, indent=2, default=str)
        
        logger.success(f"Solution paper JSON saved to: {output_path}")
        return str(output_path)
    
    def generate_answer_sheet_json(self, student_info: Dict[str, Any],
                                  answers: List[Answer],
                                  processing_time: float,
                                  student_id: str = None) -> str:
        """
        Generate JSON for student answer sheet
        
        Args:
            student_info: Student information dictionary
            answers: List of student answers
            processing_time: Time taken to process
            student_id: Student ID for filename
            
        Returns:
            Path to saved JSON file
        """
        if student_id is None:
            student_id = student_info.get('id', 'unknown')
        
        logger.info(f"Generating answer sheet JSON for student {student_id}")
        
        answer_sheet = AnswerSheetJSON(
            student_info=student_info,
            answers=answers,
            total_answers=len(answers),
            processing_time=processing_time,
            created_at=datetime.now()
        )
        
        # Save to file
        output_filename = f"answer_sheet_{student_id}.json"
        output_path = settings.output_dir / output_filename
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(answer_sheet.model_dump(), f, indent=2, default=str)
        
        logger.success(f"Answer sheet JSON saved to: {output_path}")
        return str(output_path)
    
    def load_json(self, json_path: str) -> Dict[str, Any]:
        """
        Load JSON file
        
        Args:
            json_path: Path to JSON file
            
        Returns:
            Parsed JSON as dictionary
        """
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            logger.debug(f"Loaded JSON from: {json_path}")
            return data
        except Exception as e:
            logger.error(f"Failed to load JSON from {json_path}: {e}")
            raise
    
    def generate_processing_metrics(self, total_pages: int,
                                   diagrams_extracted: int,
                                   avg_ocr_confidence: float,
                                   handwriting_pages: int,
                                   processing_time: float,
                                   api_calls: int,
                                   estimated_cost: float,
                                   output_filename: str = "processing_metrics.json") -> str:
        """
        Generate processing metrics JSON
        
        Args:
            total_pages: Number of pages processed
            diagrams_extracted: Number of diagrams extracted
            avg_ocr_confidence: Average OCR confidence
            handwriting_pages: Pages with handwriting
            processing_time: Total processing time
            api_calls: Number of API calls made
            estimated_cost: Estimated API cost
            output_filename: Output filename
            
        Returns:
            Path to saved JSON file
        """
        metrics = ProcessingMetrics(
            total_pages=total_pages,
            diagrams_extracted=diagrams_extracted,
            avg_ocr_confidence=avg_ocr_confidence,
            handwriting_pages=handwriting_pages,
            processing_time=processing_time,
            api_calls=api_calls,
            estimated_cost=estimated_cost
        )
        
        # Save to file
        output_path = settings.output_dir / output_filename
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(metrics.model_dump(), f, indent=2, default=str)
        
        logger.info(f"Processing metrics saved to: {output_path}")
        return str(output_path)

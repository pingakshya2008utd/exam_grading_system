from typing import List, Dict, Tuple
from loguru import logger
from sentence_transformers import SentenceTransformer
import numpy as np

from models.schemas import (Question, Answer, GradingResult, PartialCreditBreakdown,
                            QuestionType, GradingReport)
from utils.math_utils import MathProcessor
from utils.vision_api import ClaudeVisionAPI
from config.settings import settings


class GradingAgent:
    """Agent for grading student answers with multiple strategies"""
    
    def __init__(self):
        self.math_processor = MathProcessor()
        self.vision_api = ClaudeVisionAPI()
        
        # Load sentence transformer for semantic similarity
        try:
            self.similarity_model = SentenceTransformer('all-MiniLM-L6-v2')
            logger.info("Semantic similarity model loaded")
        except Exception as e:
            logger.warning(f"Failed to load similarity model: {e}")
            self.similarity_model = None
    
    def grade_answer_sheet(self, questions: List[Question], 
                          answers: List[Answer],
                          student_info: Dict) -> GradingReport:
        """
        Grade complete answer sheet
        
        Args:
            questions: List of questions with correct answers
            answers: List of student answers
            student_info: Student information
            
        Returns:
            GradingReport object
        """
        logger.info(f"Grading answer sheet for student {student_info.get('name', 'Unknown')}")
        
        results = []
        total_marks_available = 0.0
        total_marks_awarded = 0.0
        
        # Create question lookup
        question_map = {q.question_number: q for q in questions}
        
        # Grade each answer
        for answer in answers:
            q_num = answer.question_number
            
            if q_num not in question_map:
                logger.warning(f"Question {q_num} not found in question paper")
                continue
            
            question = question_map[q_num]
            
            # Grade the answer
            result = self._grade_single_answer(question, answer)
            results.append(result)
            
            total_marks_available += result.marks_available
            total_marks_awarded += result.marks_awarded
            
            if settings.verbose:
                logger.info(f"Q{q_num}: {result.marks_awarded:.1f}/{result.marks_available:.1f} "
                          f"({result.grading_method})")
        
        # Calculate percentage and grade
        percentage = (total_marks_awarded / total_marks_available * 100) if total_marks_available > 0 else 0
        grade = self._calculate_grade(percentage)
        
        # Create report
        report = GradingReport(
            student_info=student_info,
            results=results,
            total_marks_available=total_marks_available,
            total_marks_awarded=total_marks_awarded,
            percentage=percentage,
            grade=grade,
            processing_time=0.0,  # Will be updated by caller
            api_cost=self.vision_api.get_total_cost()
        )
        
        logger.success(f"Grading complete: {total_marks_awarded:.1f}/{total_marks_available:.1f} "
                      f"({percentage:.1f}%) - Grade: {grade}")
        
        return report
    
    def _grade_single_answer(self, question: Question, answer: Answer) -> GradingResult:
        """Grade a single answer based on question type"""
        
        # Check if answer is empty
        if not answer.answer_text or answer.answer_text == "[No answer provided]":
            return GradingResult(
                question_number=question.question_number,
                marks_available=question.marks,
                marks_awarded=0.0,
                is_correct=False,
                partial_credit=None,
                feedback="No answer provided",
                confidence=1.0,
                grading_method="no_answer"
            )
        
        # Route to appropriate grading method
        # If no correct answer is available, use AI grading for all types
        if not question.correct_answer or question.correct_answer.strip() == "":
            logger.info(f"No correct answer for Q{question.question_number}, using AI grading")
            return self._grade_with_ai(question, answer)
        
        if question.question_type == QuestionType.MCQ:
            return self._grade_mcq(question, answer)
        elif question.question_type == QuestionType.NUMERICAL:
            return self._grade_numerical(question, answer)
        elif question.question_type == QuestionType.DERIVATION or question.question_type == QuestionType.PROOF:
            return self._grade_derivation(question, answer)
        elif question.question_type == QuestionType.DIAGRAM:
            return self._grade_diagram(question, answer)
        else:  # SHORT_ANSWER, ESSAY, CODE
            return self._grade_short_answer(question, answer)
    
    def _grade_with_ai(self, question: Question, answer: Answer) -> GradingResult:
        """Grade any question type using AI when no correct answer is available"""
        
        try:
            # Use Claude Vision API for grading based on question text only
            grading_response = self.vision_api.grade_answer(
                question_type=question.question_type.value,
                marks=question.marks,
                correct_answer="",  # No sample answer available
                student_answer=answer.answer_text + (f"\n\nWorking:\n{answer.working}" if answer.working else ""),
                question_text=question.question_text  # Provide question text for context
            )
            
            marks_awarded = grading_response.get('marks_awarded', 0.0)
            feedback = grading_response.get('feedback', 'AI graded answer')
            confidence = grading_response.get('confidence', 0.8)
            
            partial_dict = grading_response.get('partial_credit', {})
            partial_credit = None
            if partial_dict:
                partial_credit = PartialCreditBreakdown(
                    method=partial_dict.get('method', 0.0),
                    calculation=partial_dict.get('calculation', 0.0),
                    final_answer=partial_dict.get('final_answer', 0.0),
                    presentation=partial_dict.get('presentation', 0.0)
                )
            
            is_correct = marks_awarded >= question.marks * 0.9
            
            return GradingResult(
                question_number=question.question_number,
                marks_available=question.marks,
                marks_awarded=marks_awarded,
                is_correct=is_correct,
                partial_credit=partial_credit,
                feedback=feedback,
                confidence=confidence,
                grading_method="ai_grading"
            )
        
        except Exception as e:
            logger.error(f"AI grading failed for Q{question.question_number}: {e}")
            return GradingResult(
                question_number=question.question_number,
                marks_available=question.marks,
                marks_awarded=0.0,
                is_correct=False,
                partial_credit=None,
                feedback=f"Grading error: {str(e)}",
                confidence=0.0,
                grading_method="ai_grading"
            )
    
    def _grade_mcq(self, question: Question, answer: Answer) -> GradingResult:
        """Grade MCQ - exact match only"""
        
        # Extract option letter from answer
        answer_letter = self._extract_mcq_option(answer.answer_text)
        correct_letter = self._extract_mcq_option(question.correct_answer or "")
        
        is_correct = (answer_letter == correct_letter)
        marks = question.marks if is_correct else 0.0
        
        feedback = f"Selected: {answer_letter}, Correct: {correct_letter}"
        
        return GradingResult(
            question_number=question.question_number,
            marks_available=question.marks,
            marks_awarded=marks,
            is_correct=is_correct,
            partial_credit=None,
            feedback=feedback,
            confidence=1.0,
            grading_method="exact_match"
        )
    
    def _grade_numerical(self, question: Question, answer: Answer) -> GradingResult:
        """Grade numerical answer with tolerance"""
        
        correct_value = self.math_processor.extract_numerical_value(question.correct_answer or "")
        student_value = self.math_processor.extract_numerical_value(answer.answer_text)
        
        if correct_value is None or student_value is None:
            # Fallback to mathematical comparison
            is_equiv, equiv_type = self.math_processor.compare_expressions(
                question.correct_answer or "",
                answer.answer_text
            )
            
            if is_equiv:
                marks = question.marks if equiv_type == 'exact' else question.marks * 0.9
                return GradingResult(
                    question_number=question.question_number,
                    marks_available=question.marks,
                    marks_awarded=marks,
                    is_correct=True,
                    partial_credit=None,
                    feedback=f"Mathematically equivalent ({equiv_type})",
                    confidence=0.9,
                    grading_method="math_equivalence"
                )
            else:
                return GradingResult(
                    question_number=question.question_number,
                    marks_available=question.marks,
                    marks_awarded=0.0,
                    is_correct=False,
                    partial_credit=None,
                    feedback="Could not extract numerical values for comparison",
                    confidence=0.5,
                    grading_method="numerical_tolerance"
                )
        
        # Calculate percentage error
        error_percent = abs(student_value - correct_value) / abs(correct_value) * 100 if correct_value != 0 else abs(student_value) * 100
        
        # Grading with tolerance
        if error_percent <= 2.0:
            # Within 2% - full marks
            marks = question.marks
            is_correct = True
            feedback = f"Correct (error: {error_percent:.2f}%)"
        elif error_percent <= 5.0:
            # Within 5% - 50% marks
            marks = question.marks * 0.5
            is_correct = False
            feedback = f"Close answer, 50% credit (error: {error_percent:.2f}%)"
        else:
            # Beyond 5% - zero marks
            marks = 0.0
            is_correct = False
            feedback = f"Incorrect (error: {error_percent:.2f}%)"
        
        return GradingResult(
            question_number=question.question_number,
            marks_available=question.marks,
            marks_awarded=marks,
            is_correct=is_correct,
            partial_credit=None,
            feedback=feedback + f" | Correct: {correct_value}, Student: {student_value}",
            confidence=0.95,
            grading_method="numerical_tolerance"
        )
    
    def _grade_derivation(self, question: Question, answer: Answer) -> GradingResult:
        """Grade derivation/proof with AI-powered partial credit"""
        
        if not settings.enable_partial_credit:
            # Fallback to basic grading
            return self._grade_short_answer(question, answer)
        
        # Use Claude Vision API for detailed grading
        grading_response = self.vision_api.grade_answer(
            question_type=question.question_type.value,
            marks=question.marks,
            correct_answer=question.correct_answer or "",
            student_answer=answer.answer_text + (f"\n\nWorking:\n{answer.working}" if answer.working else "")
        )
        
        marks_awarded = grading_response.get('marks_awarded', 0.0)
        partial_dict = grading_response.get('partial_credit', {})
        
        # Create partial credit breakdown
        partial_credit = None
        if partial_dict:
            partial_credit = PartialCreditBreakdown(
                method=partial_dict.get('method', 0.0),
                calculation=partial_dict.get('calculation', 0.0),
                final_answer=partial_dict.get('final_answer', 0.0),
                presentation=partial_dict.get('presentation', 0.0)
            )
        
        is_correct = marks_awarded >= question.marks * 0.9  # 90% threshold
        
        return GradingResult(
            question_number=question.question_number,
            marks_available=question.marks,
            marks_awarded=marks_awarded,
            is_correct=is_correct,
            partial_credit=partial_credit,
            feedback=grading_response.get('feedback', 'Graded by AI'),
            confidence=grading_response.get('confidence', 0.8),
            grading_method="ai_grading"
        )
    
    def _grade_diagram(self, question: Question, answer: Answer) -> GradingResult:
        """Grade diagram with visual comparison"""
        
        if not question.has_diagram or not answer.has_diagram:
            feedback = "Missing diagram"
            if not answer.has_diagram:
                feedback = "Student did not provide diagram"
            elif not question.has_diagram:
                feedback = "No reference diagram available"
            
            return GradingResult(
                question_number=question.question_number,
                marks_available=question.marks,
                marks_awarded=0.0,
                is_correct=False,
                partial_credit=None,
                feedback=feedback,
                confidence=1.0,
                grading_method="diagram_comparison"
            )
        
        # Load diagrams
        try:
            from PIL import Image
            correct_img = Image.open(question.diagram_path)
            student_img = Image.open(answer.diagram_path)
            
            # Compare with AI
            comparison = self.vision_api.compare_diagrams(correct_img, student_img)
            
            similarity_score = comparison.get('similarity_score', 0.0)
            
            # Award marks based on similarity
            if similarity_score >= 0.8:
                marks = question.marks
                is_correct = True
                feedback = "Diagram is correct"
            elif similarity_score >= 0.6:
                marks = question.marks * 0.7
                is_correct = False
                feedback = "Diagram is mostly correct with minor issues"
            elif similarity_score >= 0.4:
                marks = question.marks * 0.4
                is_correct = False
                feedback = "Diagram has significant issues"
            else:
                marks = 0.0
                is_correct = False
                feedback = "Diagram is incorrect"
            
            feedback += f" | Similarity: {similarity_score:.2f}"
            if comparison.get('missing_elements'):
                feedback += f" | Missing: {', '.join(comparison['missing_elements'])}"
            
            return GradingResult(
                question_number=question.question_number,
                marks_available=question.marks,
                marks_awarded=marks,
                is_correct=is_correct,
                partial_credit=None,
                feedback=feedback,
                confidence=comparison.get('confidence', 0.8),
                grading_method="diagram_comparison"
            )
            
        except Exception as e:
            logger.error(f"Diagram comparison failed: {e}")
            return GradingResult(
                question_number=question.question_number,
                marks_available=question.marks,
                marks_awarded=0.0,
                is_correct=False,
                partial_credit=None,
                feedback=f"Diagram comparison error: {str(e)}",
                confidence=0.0,
                grading_method="diagram_comparison"
            )
    
    def _grade_short_answer(self, question: Question, answer: Answer) -> GradingResult:
        """Grade short answer with semantic similarity"""
        
        if not self.similarity_model:
            # Fallback to AI grading
            logger.info("Using AI grading (semantic similarity unavailable)")
            return self._grade_derivation(question, answer)
        
        # Calculate semantic similarity
        similarity = self._calculate_semantic_similarity(
            question.correct_answer or "",
            answer.answer_text
        )
        
        # Grading based on similarity threshold
        if similarity >= settings.semantic_similarity_threshold:
            # High similarity - accept
            marks = question.marks
            is_correct = True
            feedback = f"Semantically correct (similarity: {similarity:.2f})"
            confidence = 0.9
            method = "semantic_similarity"
        elif similarity >= 0.6:
            # Medium similarity - verify with AI
            logger.info(f"Medium similarity ({similarity:.2f}), verifying with AI")
            ai_result = self.vision_api.grade_answer(
                question_type=question.question_type.value,
                marks=question.marks,
                correct_answer=question.correct_answer or "",
                student_answer=answer.answer_text
            )
            marks = ai_result.get('marks_awarded', 0.0)
            is_correct = marks >= question.marks * 0.9
            feedback = ai_result.get('feedback', f"Verified with AI (similarity: {similarity:.2f})")
            confidence = ai_result.get('confidence', 0.8)
            method = "ai_verification"
        else:
            # Low similarity - check with AI for partial credit
            if settings.enable_partial_credit:
                logger.info(f"Low similarity ({similarity:.2f}), checking for partial credit")
                ai_result = self.vision_api.grade_answer(
                    question_type=question.question_type.value,
                    marks=question.marks,
                    correct_answer=question.correct_answer or "",
                    student_answer=answer.answer_text
                )
                marks = ai_result.get('marks_awarded', 0.0)
                is_correct = False
                feedback = ai_result.get('feedback', f"Low similarity (similarity: {similarity:.2f})")
                confidence = ai_result.get('confidence', 0.7)
                method = "ai_partial_credit"
            else:
                marks = 0.0
                is_correct = False
                feedback = f"Incorrect (similarity: {similarity:.2f})"
                confidence = 0.85
                method = "semantic_similarity"
        
        return GradingResult(
            question_number=question.question_number,
            marks_available=question.marks,
            marks_awarded=marks,
            is_correct=is_correct,
            partial_credit=None,
            feedback=feedback,
            confidence=confidence,
            grading_method=method
        )
    
    def _calculate_semantic_similarity(self, text1: str, text2: str) -> float:
        """Calculate semantic similarity using sentence transformers"""
        try:
            # Encode texts
            embeddings = self.similarity_model.encode([text1, text2])
            
            # Calculate cosine similarity
            similarity = np.dot(embeddings[0], embeddings[1]) / (
                np.linalg.norm(embeddings[0]) * np.linalg.norm(embeddings[1])
            )
            
            return float(similarity)
            
        except Exception as e:
            logger.warning(f"Semantic similarity calculation failed: {e}")
            return 0.0
    
    def _extract_mcq_option(self, text: str) -> str:
        """Extract MCQ option letter from text"""
        import re
        
        # Look for patterns like: "a)", "A)", "(a)", "(A)", "a.", "A.", or standalone "a", "A"
        patterns = [
            r'\b([a-e])\)',
            r'\(([a-e])\)',
            r'\b([a-e])\.',
            r'\b([a-e])\b'
        ]
        
        text_lower = text.lower().strip()
        for pattern in patterns:
            match = re.search(pattern, text_lower)
            if match:
                return match.group(1)
        
        # If no pattern found, check if entire text is just a letter
        if len(text_lower) == 1 and text_lower in 'abcde':
            return text_lower
        
        return ""
    
    def _calculate_grade(self, percentage: float) -> str:
        """Convert percentage to letter grade"""
        if percentage >= 90:
            return "A+"
        elif percentage >= 85:
            return "A"
        elif percentage >= 80:
            return "A-"
        elif percentage >= 75:
            return "B+"
        elif percentage >= 70:
            return "B"
        elif percentage >= 65:
            return "B-"
        elif percentage >= 60:
            return "C+"
        elif percentage >= 55:
            return "C"
        elif percentage >= 50:
            return "C-"
        elif percentage >= 45:
            return "D"
        else:
            return "F"

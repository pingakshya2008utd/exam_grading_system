from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum
from datetime import datetime


class QuestionType(str, Enum):
    """Types of exam questions"""
    MCQ = "mcq"
    NUMERICAL = "numerical"
    SHORT_ANSWER = "short_answer"
    DERIVATION = "derivation"
    PROOF = "proof"
    DIAGRAM = "diagram"
    ESSAY = "essay"
    CODE = "code"
    MIXED = "mixed"


class BoundingBox(BaseModel):
    """Bounding box coordinates as percentages"""
    x_min: float = Field(..., ge=0, le=100)
    y_min: float = Field(..., ge=0, le=100)
    x_max: float = Field(..., ge=0, le=100)
    y_max: float = Field(..., ge=0, le=100)


class OCRResult(BaseModel):
    """Result from OCR processing"""
    text: str
    confidence: float = Field(..., ge=0, le=1)
    engine: str  # tesseract, easyocr, claude_vision
    has_handwriting: bool = False
    has_math: bool = False
    quality: str = "good"  # good, fair, poor


class Diagram(BaseModel):
    """Diagram extracted from document"""
    diagram_id: str
    type: str
    description: str
    bbox: Optional[BoundingBox] = None
    image_path: str
    relevance: str = "high"  # high, medium, low
    quality_score: float = Field(..., ge=0, le=1)


class Question(BaseModel):
    """Question from exam paper"""
    question_number: str
    sub_parts: List[str] = []
    marks: float
    question_type: QuestionType
    question_text: str
    options: Optional[Dict[str, str]] = None  # For MCQs: {"a": "option text", ...}
    has_diagram: bool = False
    diagram_path: Optional[str] = None
    diagrams: List[Diagram] = []
    correct_answer: Optional[str] = None  # From solution paper


class Answer(BaseModel):
    """Student's answer to a question"""
    question_number: str
    answer_text: str
    working: Optional[str] = None
    has_diagram: bool = False
    diagram_path: Optional[str] = None
    diagrams: List[Diagram] = []
    ocr_confidence: float = Field(..., ge=0, le=1)
    handwriting_quality: str = "good"  # good, fair, poor


class PartialCreditBreakdown(BaseModel):
    """Breakdown of partial credit for a question"""
    method: float = 0.0
    calculation: float = 0.0
    final_answer: float = 0.0
    presentation: float = 0.0


class GradingResult(BaseModel):
    """Result of grading a single question"""
    question_number: str
    marks_available: float
    marks_awarded: float
    is_correct: bool
    partial_credit: Optional[PartialCreditBreakdown] = None
    feedback: str
    confidence: float = Field(..., ge=0, le=1)
    grading_method: str  # exact_match, numerical_tolerance, semantic_similarity, ai_grading


class ExamMetadata(BaseModel):
    """Metadata for exam paper"""
    exam_title: Optional[str] = None
    course_code: Optional[str] = None
    date: Optional[str] = None
    total_marks: Optional[float] = None
    duration: Optional[str] = None
    instructions: Optional[str] = None


class QuestionPaperJSON(BaseModel):
    """Complete question paper structure"""
    metadata: ExamMetadata
    questions: List[Question]
    total_questions: int
    processing_time: float
    created_at: datetime = Field(default_factory=datetime.now)


class SolutionPaperJSON(BaseModel):
    """Complete solution paper structure"""
    metadata: ExamMetadata
    solutions: List[Question]  # Questions with correct_answer populated
    total_questions: int
    processing_time: float
    created_at: datetime = Field(default_factory=datetime.now)


class AnswerSheetJSON(BaseModel):
    """Student's answer sheet structure"""
    student_info: Dict[str, Any]  # name, id, email, etc.
    answers: List[Answer]
    total_answers: int
    processing_time: float
    created_at: datetime = Field(default_factory=datetime.now)


class GradingReport(BaseModel):
    """Complete grading report for a student"""
    student_info: Dict[str, Any]
    results: List[GradingResult]
    total_marks_available: float
    total_marks_awarded: float
    percentage: float
    grade: str
    processing_time: float
    api_cost: float
    created_at: datetime = Field(default_factory=datetime.now)


class ProcessingMetrics(BaseModel):
    """Metrics for transparency"""
    total_pages: int
    diagrams_extracted: int
    avg_ocr_confidence: float
    handwriting_pages: int
    processing_time: float
    api_calls: int
    estimated_cost: float

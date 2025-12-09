import re
from typing import List, Dict, Optional
from loguru import logger

from models.schemas import (Question, Answer, ExamMetadata, QuestionType, 
                            OCRResult, Diagram)


class StructureAnalyzerAgent:
    """Agent for analyzing document structure and extracting questions/answers"""
    
    def analyze_question_paper(self, ocr_results: List[OCRResult],
                               diagrams_by_page: List[List[Diagram]]) -> tuple:
        """
        Analyze question paper structure
        
        Args:
            ocr_results: OCR results for each page
            diagrams_by_page: Diagrams extracted from each page
            
        Returns:
            (ExamMetadata, List[Question])
        """
        logger.info("Analyzing question paper structure")
        
        # Combine all text
        full_text = "\n\n".join([r.text for r in ocr_results])
        
        # Extract metadata
        metadata = self._extract_metadata(full_text)
        
        # Parse questions
        questions = self._parse_questions(full_text, diagrams_by_page)
        
        logger.success(f"Found {len(questions)} questions")
        return metadata, questions
    
    def analyze_answer_sheet(self, ocr_results: List[OCRResult],
                            diagrams_by_page: List[List[Diagram]],
                            question_numbers: List[str]) -> tuple:
        """
        Analyze student answer sheet
        
        Args:
            ocr_results: OCR results for each page
            diagrams_by_page: Diagrams extracted from each page
            question_numbers: Expected question numbers
            
        Returns:
            (student_info dict, List[Answer])
        """
        logger.info("Analyzing answer sheet structure")
        
        # Extract student info from first page
        student_info = self._extract_student_info(ocr_results[0].text if ocr_results else "")
        
        # Combine all text
        full_text = "\n\n".join([r.text for r in ocr_results])
        
        # Parse answers
        answers = self._parse_answers(full_text, diagrams_by_page, question_numbers, ocr_results)
        
        logger.success(f"Found {len(answers)} answers for student {student_info.get('name', 'Unknown')}")
        return student_info, answers
    
    def _extract_metadata(self, text: str) -> ExamMetadata:
        """Extract exam metadata from text"""
        metadata = ExamMetadata()
        
        # Extract course code (e.g., EE-207, CS-101)
        course_match = re.search(r'([A-Z]{2,4}[-\s]?\d{3,4})', text, re.IGNORECASE)
        if course_match:
            metadata.course_code = course_match.group(1)
        
        # Extract exam title
        title_patterns = [
            r'(.*?exam.*?)\n',
            r'(.*?test.*?)\n',
            r'(.*?quiz.*?)\n',
            r'(.*?assignment.*?)\n'
        ]
        for pattern in title_patterns:
            title_match = re.search(pattern, text[:500], re.IGNORECASE)
            if title_match:
                metadata.exam_title = title_match.group(1).strip()
                break
        
        # Extract date
        date_patterns = [
            r'\b(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})\b',
            r'\b([A-Z][a-z]+\s+\d{1,2},?\s+\d{4})\b',
            r'\b(\d{4}[-/]\d{1,2}[-/]\d{1,2})\b'
        ]
        for pattern in date_patterns:
            date_match = re.search(pattern, text[:500])
            if date_match:
                metadata.date = date_match.group(1)
                break
        
        # Extract total marks
        marks_match = re.search(r'total\s*marks?\s*:?\s*(\d+)', text, re.IGNORECASE)
        if marks_match:
            metadata.total_marks = float(marks_match.group(1))
        
        # Extract duration
        duration_match = re.search(r'duration\s*:?\s*(\d+\s*(?:hours?|mins?|minutes?))', text, re.IGNORECASE)
        if duration_match:
            metadata.duration = duration_match.group(1)
        
        return metadata
    
    def _parse_questions(self, text: str, 
                        diagrams_by_page: List[List[Diagram]]) -> List[Question]:
        """Parse questions from text - handles multi-part questions properly"""
        questions = []
        
        # Flatten diagrams
        all_diagrams = [d for page_diagrams in diagrams_by_page for d in page_diagrams]
        
        # Find all marks indicators
        marks_pattern = r'\((\d+)\s*Marks?\)'
        marks_matches = list(re.finditer(marks_pattern, text, re.IGNORECASE))
        
        if not marks_matches:
            logger.warning("No marks indicators found")
            return []
        
        logger.info(f"Found {len(marks_matches)} marks indicators")
        
        # Build text segments with marks
        segments = []
        for i, m in enumerate(marks_matches):
            marks_val = float(m.group(1))
            start_pos = 0 if i == 0 else marks_matches[i-1].end()
            end_pos = m.end()
            segment_text = text[start_pos:end_pos].strip()
            
            segments.append({
                'text': segment_text,
                'marks': marks_val,
                'is_subpart': re.search(r'^\s*\(([a-z])\)', segment_text) is not None
            })
        
        # Intelligently group segments into questions
        # Rules:
        # 1. Numbered prefix (1., 2., 8.) -> definitely new question
        # 2. Starts with (a) -> if previous ended with (x), new question; else subpart
        # 3. High marks (>=3) after subparts -> likely new question
        # 4. Content-based: certain keywords suggest new question
        
        question_groups = []
        current_group = None
        last_was_subpart = False
        
        for i, seg in enumerate(segments):
            text = seg['text']
            marks = seg['marks']
            is_subpart = seg['is_subpart']
            has_number = bool(re.search(r'(?:^|\n)\s*(\d+)\.\s+', text))
            
            # Determine if this should start a new question
            start_new = False
            
            if has_number:
                # Explicit number -> new question
                start_new = True
            
            elif is_subpart:
                # Check if this is (a) after the previous question ended
                # If previous group had subparts, and this is (a), it's a new question
                if re.search(r'^\s*\(a\)', text):
                    if current_group and current_group['has_subparts']:
                        start_new = True
                    else:
                        # First subpart of new question
                        start_new = not current_group or not last_was_subpart
                else:
                    # (b), (c), etc. -> continuation of subparts
                    start_new = False
            
            else:
                # No number, no subpart prefix
                # Heuristic: If marks >= 3 and previous had subparts, this is likely new
                if current_group and current_group['has_subparts'] and marks >= 3:
                    start_new = True
                # Or if there's a clear topic shift
                elif re.search(r'(Show that|Prove that|Consider|Calculate|Find the)', text[:100], re.IGNORECASE):
                    if current_group and len(current_group['segments']) > 0:
                        start_new = True
            
            # Apply the decision
            if start_new:
                if current_group:
                    question_groups.append(current_group)
                current_group = {
                    'segments': [seg],
                    'total_marks': marks,
                    'has_subparts': is_subpart
                }
                last_was_subpart = is_subpart
            
            else:
                # Add to current group
                if current_group:
                    current_group['segments'].append(seg)
                    current_group['total_marks'] += marks
                    if is_subpart:
                        current_group['has_subparts'] = True
                    last_was_subpart = is_subpart
                else:
                    # Start new group
                    current_group = {
                        'segments': [seg],
                        'total_marks': marks,
                        'has_subparts': is_subpart
                    }
                    last_was_subpart = is_subpart
        
        # Add last group
        if current_group:
            question_groups.append(current_group)
        
        # Convert groups to Question objects
        for idx, group in enumerate(question_groups, start=1):
            try:
                # Combine all segment texts
                full_text = "\n\n".join(s['text'] for s in group['segments'])
                
                # Try to find explicit question number
                num_match = re.search(r'(?:^|\n)\s*(\d+)\.\s+', full_text)
                q_num = int(num_match.group(1)) if num_match else idx
                
                q_type = self._classify_question_type(full_text)
                
                options = None
                if q_type == QuestionType.MCQ:
                    options = self._extract_mcq_options(full_text)
                
                # Find associated diagrams
                associated_diagrams = []
                for diagram in all_diagrams[:2]:
                    if diagram.relevance == "high":
                        associated_diagrams.append(diagram)
                
                question = Question(
                    question_number=str(q_num),
                    sub_parts=[],
                    marks=group['total_marks'],
                    question_type=q_type,
                    question_text=full_text,
                    options=options,
                    has_diagram=len(associated_diagrams) > 0,
                    diagram_path=associated_diagrams[0].image_path if associated_diagrams else None,
                    diagrams=associated_diagrams
                )
                
                questions.append(question)
                
            except Exception as e:
                logger.warning(f"Failed to create question {idx}: {e}")
        
        logger.success(f"Parsed {len(questions)} questions, total marks: {sum(q.marks for q in questions)}")
        return questions

    def _old_parse_fallback(self, text: str, all_diagrams: List) -> List[Question]:
        """Old parsing logic kept as fallback"""
        questions = []
        question_pattern = r'(?:^|\n)\s*(?:Q\.?\s*)?(\d+)([a-z]|\([a-z]\))?\s*[.)]\s*(.*?)(?=(?:\n\s*(?:Q\.?\s*)?\d+[a-z]?[.)]|\Z))'
        matches = list(re.finditer(question_pattern, text, re.IGNORECASE | re.DOTALL))
        
        for match in matches:
                try:
                    q_num = match.group(1)
                    sub_part = match.group(2) or ""
                    q_text = match.group(3).strip()
                    
                    # Build question number
                    if sub_part:
                        sub_part = sub_part.strip('()')
                        question_number = f"{q_num}{sub_part}"
                    else:
                        question_number = q_num
                    
                    # Extract marks
                    marks = self._extract_marks(q_text)
                    
                    # Classify question type
                    q_type = self._classify_question_type(q_text)
                    
                    # Extract MCQ options if applicable
                    options = None
                    if q_type == QuestionType.MCQ:
                        options = self._extract_mcq_options(q_text)
                    
                    # Find associated diagrams (simple proximity matching)
                    associated_diagrams = []
                    for diagram in all_diagrams:
                        if diagram.relevance == "high" and len(associated_diagrams) < 2:
                            associated_diagrams.append(diagram)
                    
                    # Create question
                    question = Question(
                        question_number=question_number,
                        sub_parts=[],  # Could be enhanced to detect sub-parts
                        marks=marks,
                        question_type=q_type,
                        question_text=q_text,
                        options=options,
                        has_diagram=len(associated_diagrams) > 0,
                        diagram_path=associated_diagrams[0].image_path if associated_diagrams else None,
                        diagrams=associated_diagrams
                    )
                    
                    questions.append(question)
                    
                except Exception as e:
                    logger.warning(f"Failed to parse question: {e}")
                    continue
        
        return questions
    
    def _parse_answers(self, text: str, diagrams_by_page: List[List[Diagram]],
                      question_numbers: List[str], 
                      ocr_results: List[OCRResult]) -> List[Answer]:
        """Parse student answers from text with improved pattern matching"""
        answers = []
        
        # Flatten diagrams
        all_diagrams = [d for page_diagrams in diagrams_by_page for d in page_diagrams]
        
        # Calculate average OCR confidence
        avg_confidence = sum(r.confidence for r in ocr_results) / len(ocr_results) if ocr_results else 0.5
        
        # Find answer patterns
        for q_num in question_numbers:
            # Try multiple patterns to find the answer
            patterns = [
                # Pattern 1: "Q1", "Q2", etc.
                rf'(?:^|\n)\s*Q\.?\s*{re.escape(q_num)}\s*[:.)]?\s*(.*?)(?=(?:\n\s*(?:Q|Solution)\s*\.?\s*\d+|\Z))',
                # Pattern 2: "Solution 1:", "Solution 2:", etc.
                rf'(?:^|\n)\s*Solution\s+{re.escape(q_num)}\s*:\s*(.*?)(?=(?:\n\s*(?:Q|Solution)\s*\.?\s*\d+|\Z))',
                # Pattern 3: Just the number with markers "1.", "2.", "7_", etc.
                rf'(?:^|\n)\s*{re.escape(q_num)}\s*[_:.)\-]\s*(.*?)(?=(?:\n\s*\d+\s*[_:.)\-]|\Z))',
                # Pattern 4: Relaxed pattern for any format
                rf'(?:^|\n).*?{re.escape(q_num)}.*?[:.)]?\s*(.*?)(?=(?:\n\s*(?:Q|Solution)?\s*\.?\s*\d+[_:.)\-]|\Z))',
            ]
            
            match = None
            for pattern in patterns:
                match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
                if match:
                    break
            
            if match:
                answer_text = match.group(1).strip()
                
                # Separate working from final answer (heuristic)
                working = None
                if len(answer_text) > 100:  # Likely has working
                    # Try to find "Answer:" or similar markers
                    final_answer_match = re.search(r'(?:final\s+)?answer\s*:?\s*(.+?)(?:\n|$)', 
                                                   answer_text, re.IGNORECASE)
                    if final_answer_match:
                        working = answer_text[:final_answer_match.start()]
                        answer_text = final_answer_match.group(1).strip()
                
                # Find associated diagrams
                associated_diagrams = []
                for diagram in all_diagrams:
                    if len(associated_diagrams) < 2:  # Limit to 2 diagrams per answer
                        associated_diagrams.append(diagram)
                
                # Determine handwriting quality
                hw_quality = "good"
                if avg_confidence < 0.6:
                    hw_quality = "poor"
                elif avg_confidence < 0.75:
                    hw_quality = "fair"
                
                # Create answer
                answer = Answer(
                    question_number=q_num,
                    answer_text=answer_text,
                    working=working,
                    has_diagram=len(associated_diagrams) > 0,
                    diagram_path=associated_diagrams[0].image_path if associated_diagrams else None,
                    diagrams=associated_diagrams,
                    ocr_confidence=avg_confidence,
                    handwriting_quality=hw_quality
                )
                
                answers.append(answer)
            else:
                # No answer found, create empty answer
                answer = Answer(
                    question_number=q_num,
                    answer_text="[No answer provided]",
                    working=None,
                    has_diagram=False,
                    diagram_path=None,
                    diagrams=[],
                    ocr_confidence=avg_confidence,
                    handwriting_quality="unknown"
                )
                answers.append(answer)
        
        return answers
    
    def _classify_question_type(self, text: str) -> QuestionType:
        """Classify question type based on text content"""
        text_lower = text.lower()
        
        # MCQ indicators
        if re.search(r'\b[a-e]\)', text_lower) or 'choose' in text_lower or 'select' in text_lower:
            return QuestionType.MCQ
        
        # Derivation/Proof indicators
        if any(word in text_lower for word in ['derive', 'proof', 'prove', 'show that']):
            return QuestionType.DERIVATION
        
        # Diagram indicators
        if any(word in text_lower for word in ['draw', 'sketch', 'diagram', 'plot', 'graph']):
            return QuestionType.DIAGRAM
        
        # Code indicators
        if any(word in text_lower for word in ['code', 'program', 'implement', 'algorithm']):
            return QuestionType.CODE
        
        # Numerical indicators
        if any(word in text_lower for word in ['calculate', 'compute', 'find', 'determine']):
            return QuestionType.NUMERICAL
        
        # Essay indicators
        if any(word in text_lower for word in ['explain', 'discuss', 'describe', 'compare']):
            if len(text) > 200:  # Long question likely essay
                return QuestionType.ESSAY
            return QuestionType.SHORT_ANSWER
        
        return QuestionType.SHORT_ANSWER
    
    def _extract_marks(self, text: str) -> float:
        """Extract marks from question text"""
        # Patterns: [5 marks], (5 marks), [5M], (5), 5 marks
        patterns = [
            r'\[(\d+)\s*(?:marks?|m)\]',
            r'\((\d+)\s*(?:marks?|m)\)',
            r'(\d+)\s*marks?',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return float(match.group(1))
        
        return 1.0  # Default
    
    def _extract_mcq_options(self, text: str) -> Optional[Dict[str, str]]:
        """Extract MCQ options from text"""
        options = {}
        
        # Find options a), b), c), etc.
        option_pattern = r'([a-e])\)\s*([^\n]+?)(?=\s*[a-e]\)|\Z)'
        matches = re.finditer(option_pattern, text, re.IGNORECASE)
        
        for match in matches:
            letter = match.group(1).lower()
            option_text = match.group(2).strip()
            options[letter] = option_text
        
        return options if options else None
    
    def _extract_student_info(self, text: str) -> Dict[str, str]:
        """Extract student information from answer sheet"""
        info = {}
        
        # Extract name
        name_patterns = [
            r'name\s*:?\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)',
            r'student\s+name\s*:?\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)',
        ]
        for pattern in name_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                info['name'] = match.group(1).strip()
                break
        
        # Extract ID
        id_patterns = [
            r'(?:student\s+)?id\s*:?\s*([A-Z0-9]+)',
            r'roll\s+(?:no|number)\s*:?\s*([A-Z0-9]+)',
        ]
        for pattern in id_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                info['id'] = match.group(1).strip()
                break
        
        # Extract email
        email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', text)
        if email_match:
            info['email'] = email_match.group(0)
        
        return info

import anthropic
import base64
import json
from PIL import Image
from io import BytesIO
from typing import Dict, List, Optional, Tuple
from loguru import logger

from config.settings import settings
from config.prompts import *
from models.schemas import OCRResult, BoundingBox, Diagram


class ClaudeVisionAPI:
    """Interface to Claude Vision API for advanced OCR and analysis"""
    
    def __init__(self):
        self.client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        self.model = settings.anthropic_model
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.total_cost = 0.0
    
    def _image_to_base64(self, image: Image.Image) -> str:
        """Convert PIL Image to base64 string"""
        buffered = BytesIO()
        image.save(buffered, format="PNG")
        return base64.b64encode(buffered.getvalue()).decode()
    
    def _track_cost(self, usage):
        """Track API usage and costs"""
        if not usage:
            return
        
        input_tokens = usage.input_tokens
        output_tokens = usage.output_tokens
        
        self.total_input_tokens += input_tokens
        self.total_output_tokens += output_tokens
        
        cost = (input_tokens * settings.input_token_cost + 
                output_tokens * settings.output_token_cost)
        self.total_cost += cost
        
        if settings.track_api_costs:
            logger.debug(f"API call: {input_tokens} in, {output_tokens} out, ${cost:.4f}")
    
    def ocr_with_vision(self, image: Image.Image, 
                       is_handwritten: bool = True) -> OCRResult:
        """
        Perform OCR using Claude Vision API
        
        Args:
            image: PIL Image
            is_handwritten: Whether image contains handwriting
            
        Returns:
            OCRResult object
        """
        try:
            image_base64 = self._image_to_base64(image)
            
            message = self.client.messages.create(
                model=self.model,
                max_tokens=2048,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": "image/png",
                                    "data": image_base64,
                                },
                            },
                            {
                                "type": "text",
                                "text": HANDWRITING_OCR_PROMPT
                            }
                        ],
                    }
                ],
            )
            
            self._track_cost(message.usage)
            
            text = message.content[0].text
            
            # Claude Vision doesn't provide confidence scores, estimate based on content
            confidence = 0.85 if is_handwritten else 0.95
            
            return OCRResult(
                text=text.strip(),
                confidence=confidence,
                engine="claude_vision",
                has_handwriting=is_handwritten,
                has_math="$" in text or "\\" in text,
                quality="good"
            )
            
        except Exception as e:
            logger.error(f"Claude Vision OCR failed: {e}")
            return OCRResult(
                text="",
                confidence=0.0,
                engine="claude_vision",
                has_handwriting=is_handwritten,
                has_math=False,
                quality="poor"
            )
    
    def detect_diagrams(self, image: Image.Image) -> List[Dict]:
        """
        Detect diagrams in image using AI
        
        Args:
            image: PIL Image
            
        Returns:
            List of diagram dictionaries with bbox, type, description
        """
        try:
            image_base64 = self._image_to_base64(image)
            
            message = self.client.messages.create(
                model=self.model,
                max_tokens=1024,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": "image/png",
                                    "data": image_base64,
                                },
                            },
                            {
                                "type": "text",
                                "text": DIAGRAM_DETECTION_PROMPT
                            }
                        ],
                    }
                ],
            )
            
            self._track_cost(message.usage)
            
            response_text = message.content[0].text
            
            # Parse JSON response
            # Sometimes Claude wraps JSON in markdown code blocks
            if "```json" in response_text:
                json_str = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                json_str = response_text.split("```")[1].split("```")[0].strip()
            else:
                json_str = response_text.strip()
            
            result = json.loads(json_str)
            diagrams = result.get("diagrams", [])
            
            logger.info(f"Detected {len(diagrams)} diagrams using AI")
            return diagrams
            
        except Exception as e:
            logger.error(f"AI diagram detection failed: {e}")
            return []
    
    def analyze_structure(self, image: Image.Image, prompt: str) -> str:
        """
        Analyze document structure using Claude Vision
        
        Args:
            image: PIL Image
            prompt: Analysis prompt
            
        Returns:
            Analysis text
        """
        try:
            image_base64 = self._image_to_base64(image)
            
            message = self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": "image/png",
                                    "data": image_base64,
                                },
                            },
                            {
                                "type": "text",
                                "text": prompt
                            }
                        ],
                    }
                ],
            )
            
            self._track_cost(message.usage)
            
            return message.content[0].text.strip()
            
        except Exception as e:
            logger.error(f"Structure analysis failed: {e}")
            return ""
    
    def grade_answer(self, question_type: str, marks: float,
                    correct_answer: str, student_answer: str,
                    question_text: str = "") -> Dict:
        """
        Grade student answer using AI reasoning
        
        Args:
            question_type: Type of question
            marks: Marks available
            correct_answer: Correct solution (can be empty)
            student_answer: Student's answer
            question_text: The question text (used when no correct answer available)
            
        Returns:
            Grading result dictionary
        """
        try:
            # Determine grading context based on whether correct answer is available
            if correct_answer and correct_answer.strip():
                grading_context = "Compare the student's answer with the correct solution."
                question_info = f"Correct Answer: {correct_answer}"
            else:
                grading_context = "Evaluate the student's answer based on the question requirements."
                question_info = f"Question: {question_text}" if question_text else "Question: [See student answer for context]"
            
            prompt = GRADING_PROMPT.format(
                grading_context=grading_context,
                question_type=question_type,
                marks=marks,
                question_info=question_info,
                student_answer=student_answer
            )
            
            message = self.client.messages.create(
                model=self.model,
                max_tokens=1024,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
            )
            
            self._track_cost(message.usage)
            
            response_text = message.content[0].text
            
            logger.debug(f"AI grading response: {response_text}")
            
            # Parse JSON response - try multiple extraction methods
            json_str = None
            
            # Method 1: Look for ```json code blocks
            if "```json" in response_text:
                json_str = response_text.split("```json")[1].split("```")[0].strip()
            # Method 2: Look for any ``` code blocks
            elif "```" in response_text:
                json_str = response_text.split("```")[1].split("```")[0].strip()
            # Method 3: Extract JSON object using regex (handle multi-line)
            else:
                import re
                # Find the first { and last } to extract the JSON object
                start_idx = response_text.find('{')
                end_idx = response_text.rfind('}')
                if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                    json_str = response_text[start_idx:end_idx+1]
                else:
                    json_str = response_text.strip()
            
            logger.debug(f"Extracted JSON string: {json_str[:200]}...")
            
            # Try to parse, if it fails due to control characters, fix them
            try:
                result = json.loads(json_str)
            except json.JSONDecodeError as e:
                # Try fixing common JSON issues (unescaped newlines in strings)
                logger.warning(f"Initial JSON parse failed: {e}, attempting repair...")
                try:
                    # Use ast.literal_eval as fallback or try manual escaping
                    # Replace unescaped control characters within the JSON
                    import re
                    # Find all string values and escape newlines/tabs/etc
                    def escape_string_content(match):
                        s = match.group(0)
                        # Keep the quotes, escape the content
                        s = s.replace('\n', '\\n').replace('\r', '\\r').replace('\t', '\\t')
                        return s
                    
                    # This regex matches JSON string values (content between quotes)
                    json_str_fixed = re.sub(r'"[^"\\]*(?:\\.[^"\\]*)*"', escape_string_content, json_str, flags=re.DOTALL)
                    result = json.loads(json_str_fixed)
                    logger.success("JSON repair successful")
                except Exception as repair_error:
                    logger.error(f"JSON repair also failed: {repair_error}")
                    raise e  # Re-raise original error
            
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"AI grading JSON parse failed: {e}")
            logger.error(f"Response was: {response_text[:500] if 'response_text' in locals() else 'N/A'}")
            return {
                "marks_awarded": 0.0,
                "partial_credit": None,
                "feedback": f"Grading error: Could not parse AI response",
                "confidence": 0.0
            }
        except Exception as e:
            logger.error(f"AI grading failed: {e}")
            return {
                "marks_awarded": 0.0,
                "partial_credit": None,
                "feedback": f"Grading error: {str(e)}",
                "confidence": 0.0
            }
    
    def compare_diagrams(self, correct_diagram: Image.Image, 
                        student_diagram: Image.Image) -> Dict:
        """
        Compare two diagrams for similarity
        
        Args:
            correct_diagram: Reference diagram
            student_diagram: Student's diagram
            
        Returns:
            Comparison result dictionary
        """
        try:
            correct_b64 = self._image_to_base64(correct_diagram)
            student_b64 = self._image_to_base64(student_diagram)
            
            message = self.client.messages.create(
                model=self.model,
                max_tokens=1024,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": "Reference Diagram:"
                            },
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": "image/png",
                                    "data": correct_b64,
                                },
                            },
                            {
                                "type": "text",
                                "text": "Student Diagram:"
                            },
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": "image/png",
                                    "data": student_b64,
                                },
                            },
                            {
                                "type": "text",
                                "text": DIAGRAM_COMPARISON_PROMPT
                            }
                        ],
                    }
                ],
            )
            
            self._track_cost(message.usage)
            
            response_text = message.content[0].text
            
            # Parse JSON response
            if "```json" in response_text:
                json_str = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                json_str = response_text.split("```")[1].split("```")[0].strip()
            else:
                json_str = response_text.strip()
            
            result = json.loads(json_str)
            return result
            
        except Exception as e:
            logger.error(f"Diagram comparison failed: {e}")
            return {
                "similarity_score": 0.0,
                "structure_correct": False,
                "labels_correct": False,
                "missing_elements": [],
                "incorrect_elements": [],
                "feedback": f"Comparison error: {str(e)}"
            }
    
    def get_total_cost(self) -> float:
        """Get total API cost for this session"""
        return self.total_cost
    
    def reset_cost_tracking(self):
        """Reset cost tracking counters"""
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.total_cost = 0.0

"""Domain-agnostic prompts for the exam grading system"""

HANDWRITING_OCR_PROMPT = """You are an expert OCR system specialized in reading handwritten text from exam answer sheets.

Extract ALL text from this image, including:
- Student's handwritten answers
- Mathematical expressions and equations (use LaTeX format: $equation$)
- Any diagrams, tables, or special notation
- Working shown by the student

IMPORTANT:
1. Preserve the structure and layout as much as possible
2. Use LaTeX notation for all mathematical expressions: $x^2 + 3x + 2$
3. If text is unclear or illegible, mark it as [UNCLEAR: approximate_text]
4. Maintain the order of content as it appears
5. Note any diagrams with [DIAGRAM: description]

Return the extracted text in a clean, structured format."""

DIAGRAM_DETECTION_PROMPT = """Analyze this image and identify ALL diagrams, figures, charts, or visual elements.

For each diagram found, provide:
1. Type (circuit, graph, flowchart, mechanical drawing, plot, table, etc.)
2. Bounding box coordinates as percentages (x_min, y_min, x_max, y_max) where 0-100%
3. Brief description of the diagram
4. Relevance to the question (high/medium/low)

Return the response in this exact JSON format:
{
  "diagrams": [
    {
      "type": "circuit",
      "bbox": {"x_min": 10, "y_min": 20, "x_max": 45, "y_max": 60},
      "description": "RC circuit with resistor and capacitor",
      "relevance": "high"
    }
  ]
}

If no diagrams are found, return: {"diagrams": []}"""

QUESTION_STRUCTURE_PROMPT = """Analyze this exam question paper and extract the structure.

Identify for each question:
1. Question number and any sub-parts (1a, 1b, etc.)
2. Marks allocated for each part
3. Question type (MCQ, numerical, short_answer, derivation, proof, diagram, essay, code)
4. The complete question text
5. For MCQs: all options (a, b, c, d, e) with their text
6. Any associated diagrams or figures

Return a structured JSON with all questions and metadata."""

ANSWER_EXTRACTION_PROMPT = """Extract the student's answer from this section of their answer sheet.

Identify:
1. The final answer given by the student
2. Any working or steps shown
3. Mathematical expressions in LaTeX format
4. Any diagrams drawn by the student
5. Confidence level of the OCR (high/medium/low)

Return the answer in a structured format that preserves the student's work."""

GRADING_PROMPT = """You are an expert exam grader. {grading_context}

Question Type: {question_type}
Marks Available: {marks}
{question_info}
Student Answer: {student_answer}

Grading Guidelines:
- For MCQ: Exact match only (full marks or zero) - but if no correct answer provided, evaluate based on question
- For numerical: ±2% tolerance for full marks, ±5% for 50% marks
- For derivations: Evaluate method, calculations, final answer, presentation
- For diagrams: Check accuracy, completeness, labeling
- For short answers: Check key concepts and accuracy
- When no correct answer is provided: Evaluate based on the question requirements, accuracy of concepts, completeness, and clarity

Provide:
1. Marks awarded (out of {marks})
2. Partial credit breakdown if applicable:
   - Method/Approach: X marks
   - Calculations: X marks
   - Final Answer: X marks
   - Presentation: X marks
3. Feedback explaining the grade
4. Confidence in grading (0-1)

IMPORTANT: Return ONLY valid JSON. Escape all special characters in strings (use \\n for newlines, \\" for quotes).

Return as JSON:
{{
  "marks_awarded": float,
  "partial_credit": {{"method": X, "calculation": X, "final_answer": X, "presentation": X}},
  "feedback": "detailed explanation - use \\n for line breaks",
  "confidence": 0.95
}}"""

MATH_COMPARISON_PROMPT = """Compare these two mathematical expressions for equivalence.

Correct Expression: {correct_expr}
Student Expression: {student_expr}

Determine if they are:
1. Exactly equivalent (same algebraic form)
2. Numerically equivalent (same value)
3. Partially correct (e.g., sign error, missing term)
4. Incorrect

Return JSON:
{{
  "equivalent": bool,
  "equivalence_type": "exact|numerical|partial|incorrect",
  "confidence": float,
  "explanation": "brief explanation"
}}"""

DIAGRAM_COMPARISON_PROMPT = """Compare these two diagrams/figures for similarity.

Reference Diagram: [correct diagram]
Student Diagram: [student's diagram]

Evaluate:
1. Overall similarity (0-1 score)
2. Correctness of structure/components
3. Accuracy of labels and annotations
4. Quality of presentation
5. Missing or incorrect elements

Return JSON:
{{
  "similarity_score": float,
  "structure_correct": bool,
  "labels_correct": bool,
  "missing_elements": ["list"],
  "incorrect_elements": ["list"],
  "feedback": "explanation"
}}"""

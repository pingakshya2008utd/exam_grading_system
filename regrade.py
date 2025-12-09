#!/usr/bin/env python3
"""
Regrade using the enhanced answer extraction
"""
import sys
import json
from loguru import logger

logger.remove()
logger.add(sys.stderr, level="INFO")

from agents.grading_agent import GradingAgent
from models.schemas import Question, Answer
from config.settings import settings

print("\n" + "="*80)
print("REGRADING WITH ENHANCED ANSWERS")
print("="*80)

# Load question paper and answer sheet
question_paper_file = settings.output_dir / "question_paper.json"
answer_sheet_file = settings.output_dir / "answer_sheet_A1_solution.json"

with open(question_paper_file, 'r') as f:
    question_paper = json.load(f)

with open(answer_sheet_file, 'r') as f:
    answer_sheet = json.load(f)

print(f"\nLoaded {len(question_paper['questions'])} questions")
print(f"Loaded {len(answer_sheet['answers'])} answers")

# Parse into proper objects
questions = []
for q_dict in question_paper['questions']:
    questions.append(Question(**q_dict))

answers = []
for a_dict in answer_sheet['answers']:
    answers.append(Answer(**a_dict))

student_info = answer_sheet.get('student_info', {'name': 'Unknown', 'id': 'Unknown'})

# Initialize grading agent
grading_agent = GradingAgent()

# Grade
print("\n" + "="*80)
print("GRADING ANSWERS")
print("="*80)

graded_results = grading_agent.grade_answer_sheet(
    questions=questions,
    answers=answers,
    student_info=student_info
)

# Save results
output_file = settings.output_dir / "grading_report_enhanced.json"
with open(output_file, 'w') as f:
    json.dump(graded_results.model_dump(), f, indent=2, default=str)

print(f"\n✓ Grading report saved to: {output_file}")

# Display summary
print("\n" + "="*80)
print("GRADING SUMMARY")
print("="*80)
print(f"Student: {graded_results.student_info.get('name', 'Unknown')}")
print(f"Total: {graded_results.total_marks_awarded}/{graded_results.total_marks_available}")
print(f"Percentage: {graded_results.percentage:.2f}%")
print(f"Grade: {graded_results.grade}")
print(f"API Cost: ${graded_results.api_cost:.4f}")
print("="*80)

# Show individual results
for result in graded_results.results:
    q_num = result.question_number
    marks = result.marks_awarded
    total = result.marks_available
    status = "✓" if result.is_correct or marks > 0 else "✗"
    
    print(f"{status} Q{q_num}: {marks}/{total} [{result.grading_method}]")
    if result.feedback:
        # Truncate long feedback
        feedback = result.feedback[:200] + "..." if len(result.feedback) > 200 else result.feedback
        print(f"   {feedback}")

print("="*80)

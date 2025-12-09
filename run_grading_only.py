#!/usr/bin/env python3
"""
Quick script to run grading on already processed files
"""

import sys
import json
from pathlib import Path
from loguru import logger
from config.settings import settings
from agents import GradingAgent, JSONGeneratorAgent
from models.schemas import Question, Answer


def main():
    # Setup logging
    logger.remove()
    logger.add(sys.stderr, level="INFO", colorize=True)
    
    # Paths to existing JSON files
    question_json = "data/output/question_paper.json"
    answer_json = "data/output/answer_sheet_A1_solution.json"
    
    logger.info("Loading existing processed files...")
    
    # Initialize agents
    json_generator = JSONGeneratorAgent()
    grading_agent = GradingAgent()
    
    # Load JSONs
    question_data = json_generator.load_json(question_json)
    answer_data = json_generator.load_json(answer_json)
    
    # Parse data structures - Use question paper since we don't have solutions
    questions = []
    for q_dict in question_data['questions']:
        questions.append(Question(**q_dict))
    
    answers = []
    for a_dict in answer_data['answers']:
        answers.append(Answer(**a_dict))
    
    student_info = answer_data.get('student_info', {})
    
    # Grade
    logger.info(f"Grading {len(answers)} answers using AI...")
    report = grading_agent.grade_answer_sheet(questions, answers, student_info)
    
    # Save grading report
    student_id = student_info.get('id', 'unknown')
    output_path = settings.output_dir / f"grading_report_{student_id}_new.json"
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report.model_dump(), f, indent=2, default=str)
    
    logger.success(f"Grading complete!")
    logger.info(f"Report saved to: {output_path}")
    
    # Print summary
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
        logger.info(f"   Feedback: {result.feedback}")
    
    logger.info("=" * 80 + "\n")


if __name__ == "__main__":
    main()

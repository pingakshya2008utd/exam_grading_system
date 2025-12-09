#!/bin/bash

# Exam Grading System - Helper Script
# Auto-detects PDFs in data/input and runs the grading pipeline

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  AI-Powered Exam Grading System       ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════╝${NC}"
echo ""

# Check if .env exists
if [ ! -f ".env" ]; then
    echo -e "${RED}Error: .env file not found!${NC}"
    echo -e "Please copy .env.example to .env and add your ANTHROPIC_API_KEY"
    exit 1
fi

# Check if data/input directory exists
if [ ! -d "data/input" ]; then
    echo -e "${RED}Error: data/input directory not found!${NC}"
    echo -e "Creating directory..."
    mkdir -p data/input
    echo -e "${YELLOW}Please place your PDF files in data/input/${NC}"
    exit 1
fi

# Find PDFs
echo -e "${BLUE}Searching for PDFs in data/input...${NC}"
echo ""

QUESTION_PDF=$(find data/input -name "question*.pdf" -o -name "Q*.pdf" -o -name "*question*.pdf" | head -1)
SOLUTION_PDF=$(find data/input -name "solution*.pdf" -o -name "S*.pdf" -o -name "*solution*.pdf" | head -1)
ANSWER_PDFS=$(find data/input -name "answer*.pdf" -o -name "student*.pdf" -o -name "A*.pdf")

# Display found files
if [ -n "$QUESTION_PDF" ]; then
    echo -e "${GREEN}✓ Question paper:${NC} $QUESTION_PDF"
else
    echo -e "${YELLOW}⚠ Question paper not found${NC}"
fi

if [ -n "$SOLUTION_PDF" ]; then
    echo -e "${GREEN}✓ Solution paper:${NC} $SOLUTION_PDF"
else
    echo -e "${YELLOW}⚠ Solution paper not found${NC}"
fi

if [ -n "$ANSWER_PDFS" ]; then
    answer_count=$(echo "$ANSWER_PDFS" | wc -l | tr -d ' ')
    echo -e "${GREEN}✓ Answer sheets:${NC} $answer_count found"
    echo "$ANSWER_PDFS" | while read -r file; do
        echo -e "  - $(basename "$file")"
    done
else
    echo -e "${YELLOW}⚠ Answer sheets not found${NC}"
fi

echo ""

# Check if we have minimum required files
if [ -z "$QUESTION_PDF" ] && [ -z "$ANSWER_PDFS" ]; then
    echo -e "${RED}Error: No PDFs found in data/input/${NC}"
    echo ""
    echo "Expected file naming patterns:"
    echo "  Question paper: question.pdf, Q1.pdf, exam_question.pdf"
    echo "  Solution paper: solution.pdf, S1.pdf, exam_solution.pdf"
    echo "  Answer sheets: answer1.pdf, student1.pdf, A1.pdf"
    exit 1
fi

# Build command
CMD="python main.py"

if [ -n "$QUESTION_PDF" ]; then
    CMD="$CMD --question \"$QUESTION_PDF\""
fi

if [ -n "$SOLUTION_PDF" ]; then
    CMD="$CMD --solution \"$SOLUTION_PDF\""
fi

if [ -n "$ANSWER_PDFS" ]; then
    # Add all answer sheets
    for file in $ANSWER_PDFS; do
        CMD="$CMD --answers \"$file\""
    done
fi

# Confirm before running
echo -e "${BLUE}Ready to run:${NC}"
echo -e "${YELLOW}$CMD${NC}"
echo ""
read -p "Continue? (y/n) " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}Cancelled by user${NC}"
    exit 0
fi

# Run the pipeline
echo -e "${GREEN}Starting grading pipeline...${NC}"
echo ""

eval $CMD

# Check exit code
if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}╔════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║  Processing Complete! ✓                ║${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "Results saved in: ${BLUE}data/output/${NC}"
    echo -e "Logs saved in: ${BLUE}logs/${NC}"
else
    echo ""
    echo -e "${RED}╔════════════════════════════════════════╗${NC}"
    echo -e "${RED}║  Processing Failed! ✗                  ║${NC}"
    echo -e "${RED}╚════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "Check logs for details: ${BLUE}logs/${NC}"
    exit 1
fi

#!/bin/bash

# Exam Grading System - Run Script
# This script sets up the environment and runs the grading system

# Load environment variables from .env file
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

source venv/bin/activate
python main.py

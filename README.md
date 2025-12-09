# Exam Grading System

An AI-powered automated exam grading system that uses OCR, computer vision, and Claude AI to grade handwritten and typed exam papers. The system intelligently extracts questions, processes student answers, and provides detailed grading with feedback.

## 🌟 Features

- **Intelligent PDF Processing**: Converts exam papers to high-resolution images
- **Hybrid OCR**: Uses EasyOCR and Tesseract with automatic fallback
- **Claude Vision API**: Advanced mathematical equation extraction for complex content
- **Smart Question Extraction**: Automatically identifies questions, subparts, and marks
- **Answer Matching**: Semantic similarity-based answer matching
- **AI Grading**: Contextual grading using Claude Opus with detailed feedback
- **Automatic Image Compression**: Handles large images by compressing to meet API limits
- **Comprehensive Reports**: JSON-based grading reports with detailed feedback

## 📋 Prerequisites

- Python 3.13 or higher
- Poppler (for PDF processing)
- Tesseract OCR (optional, for fallback OCR)
- Anthropic API key (Claude API)

### Installing System Dependencies

**macOS:**
```bash
brew install poppler tesseract
```

**Ubuntu/Debian:**
```bash
sudo apt-get install poppler-utils tesseract-ocr
```

**Windows:**
- Download Poppler from: https://github.com/oschwartz10612/poppler-windows/releases/
- Download Tesseract from: https://github.com/UB-Mannheim/tesseract/wiki

## 🚀 Installation

1. **Clone the repository:**
```bash
git clone https://github.com/pingakshya2008utd/exam_grading_system.git
cd exam_grading_system
```

2. **Create and activate a virtual environment:**
```bash
python -m venv venv

# macOS/Linux:
source venv/bin/activate

# Windows:
venv\Scripts\activate
```

3. **Install Python dependencies:**
```bash
pip install -r requirements.txt
```

4. **Set up your Anthropic API key:**
```bash
export ANTHROPIC_API_KEY="your-api-key-here"
```

Or create a `.env` file in the project root:
```env
ANTHROPIC_API_KEY=your-api-key-here
ANTHROPIC_MODEL=claude-3-opus-20240229
```

## 📁 Project Structure

```
exam-grading-system/
├── main.py                 # Main pipeline orchestrator
├── requirements.txt        # Python dependencies
├── README.md              # This file
├── agents/                # Core processing agents
│   ├── document_processor.py   # PDF to image conversion
│   ├── ocr_agent.py           # OCR processing
│   ├── image_extractor.py     # Diagram extraction
│   ├── structure_analyzer.py  # Question/answer parsing
│   ├── json_generator.py      # JSON output generation
│   └── grading_agent.py       # AI-powered grading
├── config/
│   ├── settings.py        # Configuration management
│   └── prompts.py         # AI prompts
├── models/
│   └── schemas.py         # Data models (Pydantic)
├── utils/
│   ├── pdf_tools.py       # PDF utilities
│   ├── image_tools.py     # Image processing
│   ├── ocr_tools.py       # OCR utilities
│   ├── vision_api.py      # Claude API wrapper
│   └── math_ocr.py        # Mathematical OCR with Vision API
└── data/
    ├── input/             # Place your PDF files here
    ├── output/            # Generated JSON reports
    ├── images/            # Extracted images
    └── temp/              # Temporary files
```

## 🎯 Usage

### Basic Usage

The system is configured to process hardcoded input files. Edit `main.py` to change the input files:

```python
# In main.py, modify these constants:
QUESTION_PAPER_PDF = "A1.pdf"        # Your question paper
ANSWER_SHEET_PDF = "A1_solution.pdf" # Student answer sheet
SOLUTION_PAPER_PDF = None            # Optional sample solution
```

1. **Place your PDF files in the `data/input/` directory**

2. **Run the grading pipeline:**
```bash
python main.py
```

3. **Check the results** in `data/output/`:
   - `question_paper.json` - Extracted questions
   - `answer_sheet_*.json` - Extracted student answers
   - `grading_report_*.json` - Final grading report

### Advanced Usage

#### Using Vision API for Specific Questions

For questions with complex mathematical equations or graphs, the system automatically uses Claude Vision API. You can manually extract specific questions:

```bash
python update_q6_q8.py  # Extract Q6 and Q8 with Vision API
```

#### Regrading with Enhanced Answers

After updating answers with Vision API:

```bash
python regrade.py
```

### Output Format

**Grading Report (`grading_report_*.json`):**
```json
{
  "student_info": {
    "name": "Unknown",
    "id": "Unknown"
  },
  "results": [
    {
      "question_number": 1,
      "marks_awarded": 2.0,
      "marks_available": 2.0,
      "grading_method": "ai_grading",
      "feedback": "Detailed feedback from AI..."
    }
  ],
  "total_marks_awarded": 43.0,
  "total_marks_available": 45.0,
  "percentage": 95.56,
  "grade": "A+",
  "api_cost": 0.15,
  "processing_time": 120.5
}
```

## 🔧 Configuration

Edit `config/settings.py` to customize:

- **DPI**: Image resolution (default: 600)
- **OCR Confidence**: Threshold for OCR reliability (default: 0.70)
- **Semantic Similarity**: Answer matching threshold (default: 0.80)
- **API Model**: Claude model to use (default: claude-3-opus-20240229)

## 🧪 Testing

Run the test suite:

```bash
pytest tests/
```

Test specific components:

```bash
# Test OCR extraction
python -m agents.ocr_agent

# Test Vision API
python test_math_ocr.py
```

## 💡 How It Works

1. **PDF Processing**: Converts PDFs to high-resolution images (600 DPI)
2. **OCR Extraction**: 
   - Primary: EasyOCR (CPU-optimized)
   - Fallback: Tesseract
   - Advanced: Claude Vision API for mathematical content
3. **Structure Analysis**: 
   - Detects question boundaries using numbering and marks
   - Identifies subparts (a, b, c)
   - Extracts marks allocation
4. **Answer Matching**: Maps student answers to questions using question numbers
5. **AI Grading**:
   - Analyzes answer quality
   - Compares with question requirements
   - Provides detailed feedback
   - Assigns marks and partial credit
6. **Report Generation**: Creates comprehensive JSON reports with grades and feedback

## 🎨 Key Features Explained

### Automatic Image Compression

The system automatically compresses images larger than 5MB to meet API limits:
- Detects oversized images
- Resizes intelligently (preserves aspect ratio)
- Converts to JPEG with optimal quality (85%)
- Ensures base64-encoded size < 5MB

### Hybrid OCR Strategy

Cost-effective approach:
- **Standard OCR** (Free): Used for regular text
- **Vision API** (Paid): Only for complex math equations, graphs, diagrams

### Smart Question Detection

Multiple strategies for accurate question extraction:
- Numbered prefix detection (1., 2., Q1, etc.)
- Subpart detection ((a), (b), (c))
- Marks-based splitting (high marks after subparts → new question)
- Content keywords ("Show that", "Prove that", "Consider")

## 📊 Example Results

```
GRADING SUMMARY
================================================================================
Student: Unknown
Total: 43.0/45.0
Percentage: 95.56%
Grade: A+
API Cost: $0.12
--------------------------------------------------------------------------------
✓ Q1: 2.0/2.0 [ai_grading]
✓ Q2: 4.0/4.0 [ai_grading]
✓ Q3: 4.0/4.0 [ai_grading]
✓ Q4: 4.0/4.0 [ai_grading]
✓ Q5: 6.0/6.0 [ai_grading]
✓ Q6: 5.0/5.0 [ai_grading]
✓ Q7: 4.0/5.0 [ai_grading]
✓ Q8: 14.0/15.0 [ai_grading]
================================================================================
```

## 🐛 Troubleshooting

### Common Issues

**1. "poppler not found"**
```bash
# macOS
brew install poppler

# Linux
sudo apt-get install poppler-utils
```

**2. "EasyOCR download fails"**
- The first run downloads ML models (~100MB)
- Ensure stable internet connection
- Models are cached in `~/.EasyOCR/`

**3. "API rate limit exceeded"**
- Claude API has rate limits
- Add delays between API calls
- Consider using a higher tier API key

**4. "Image exceeds 5MB"**
- System automatically compresses images
- If still failing, reduce DPI in settings (e.g., 400 instead of 600)

**5. "No questions extracted"**
- Check if PDF converted correctly (`data/images/`)
- Verify OCR output quality
- Adjust OCR confidence threshold in settings

## 🔐 Security

- Never commit your `.env` file or API keys
- Use environment variables for sensitive data
- The `.gitignore` file is configured to exclude sensitive files

## 📝 API Costs

Claude API pricing (as of 2024):
- **Input**: $15 per 1M tokens (~$0.015 per 1K tokens)
- **Output**: $75 per 1M tokens (~$0.075 per 1K tokens)

Typical costs per exam:
- 8 questions: ~$0.10 - $0.20
- Vision API usage adds ~$0.05 per complex image

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- **Anthropic** for Claude AI API
- **EasyOCR** for robust OCR capabilities
- **pdf2image** for PDF processing
- **Pydantic** for data validation

## 📧 Contact

For questions or support, please open an issue on GitHub.

---

**Made with ❤️ for automated exam grading**

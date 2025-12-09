from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path
from typing import Optional


class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        case_sensitive=False,
        extra='ignore'
    )
    
    # API Configuration
    anthropic_api_key: str
    anthropic_model: str = "claude-3-opus-20240229"
    
    # Paths
    base_dir: Path = Path(__file__).parent.parent
    input_dir: Path = base_dir / "data" / "input"
    output_dir: Path = base_dir / "data" / "output"
    images_dir: Path = base_dir / "data" / "images"
    temp_dir: Path = base_dir / "data" / "temp"
    logs_dir: Path = base_dir / "logs"
    
    # Image Processing
    dpi: int = 600
    use_gpu: bool = True
    parallel_processing: bool = False
    
    # OCR Configuration
    use_multi_ocr: bool = True
    ocr_confidence_threshold: float = 0.70
    handwriting_detection_threshold: float = 0.60
    
    # Diagram Extraction
    min_diagram_size: int = 5000
    use_ai_diagram_detection: bool = True
    image_quality_threshold: float = 50.0
    
    # Grading Configuration
    enable_partial_credit: bool = True
    semantic_similarity_threshold: float = 0.80
    math_equation_matching: bool = True
    
    # Logging
    log_level: str = "INFO"
    verbose: bool = True
    track_api_costs: bool = True
    
    # Cost Tracking (Sonnet 4 pricing)
    input_token_cost: float = 3.0 / 1_000_000  # $3 per 1M tokens
    output_token_cost: float = 15.0 / 1_000_000  # $15 per 1M tokens
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Create directories if they don't exist
        for directory in [self.input_dir, self.output_dir, self.images_dir, 
                         self.temp_dir, self.logs_dir]:
            directory.mkdir(parents=True, exist_ok=True)


# Global settings instance
settings = Settings()

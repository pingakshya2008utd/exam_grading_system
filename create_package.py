#!/usr/bin/env python3
"""
Script to create a distributable package of the exam grading system
"""

import os
import zipfile
from pathlib import Path
from datetime import datetime

def create_package():
    """Create a zip package of the complete system"""
    
    # Get current directory
    base_dir = Path(__file__).parent
    
    # Create package name with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    package_name = f"exam-grading-system_{timestamp}.zip"
    package_path = base_dir / package_name
    
    print(f"Creating package: {package_name}")
    print("-" * 60)
    
    # Files and directories to include
    include_patterns = [
        # Root files
        ".env.example",
        "README.md",
        "requirements.txt",
        "main.py",
        "run.sh",
        "create_package.py",
        
        # Python packages
        "config/*.py",
        "models/*.py",
        "utils/*.py",
        "agents/*.py",
        
        # Empty directories (with .gitkeep)
        "data/input/",
        "data/output/",
        "data/images/",
        "data/temp/",
        "logs/",
    ]
    
    # Create zip file
    with zipfile.ZipFile(package_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        file_count = 0
        
        # Add files
        for pattern in include_patterns:
            if pattern.endswith('/'):
                # Directory - create with .gitkeep
                dir_path = base_dir / pattern.rstrip('/')
                dir_path.mkdir(parents=True, exist_ok=True)
                gitkeep_path = dir_path / ".gitkeep"
                gitkeep_path.touch()
                
                arcname = os.path.join("exam-grading-system", pattern.rstrip('/'), ".gitkeep")
                zipf.write(gitkeep_path, arcname)
                print(f"Added: {arcname}")
                file_count += 1
            elif '*' in pattern:
                # Wildcard pattern
                parts = pattern.split('/')
                if len(parts) == 2:
                    directory = base_dir / parts[0]
                    if directory.exists():
                        for file in directory.glob(parts[1]):
                            if file.is_file():
                                arcname = os.path.join("exam-grading-system", parts[0], file.name)
                                zipf.write(file, arcname)
                                print(f"Added: {arcname}")
                                file_count += 1
            else:
                # Single file
                file_path = base_dir / pattern
                if file_path.exists():
                    arcname = os.path.join("exam-grading-system", pattern)
                    zipf.write(file_path, arcname)
                    print(f"Added: {arcname}")
                    file_count += 1
    
    # Get file size
    size_mb = package_path.stat().st_size / (1024 * 1024)
    
    print("-" * 60)
    print(f"✓ Package created successfully!")
    print(f"  Location: {package_path}")
    print(f"  Size: {size_mb:.2f} MB")
    print(f"  Files: {file_count}")
    print()
    print("To extract:")
    print(f"  unzip {package_name}")
    print(f"  cd exam-grading-system")
    print(f"  pip install -r requirements.txt")
    print(f"  cp .env.example .env")
    print(f"  # Edit .env with your ANTHROPIC_API_KEY")
    print(f"  python main.py --help")
    

if __name__ == "__main__":
    create_package()

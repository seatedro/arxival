import os
import sys
from pathlib import Path

# Get the root directory of the project (where this conftest.py lives)
ROOT_DIR = Path(__file__).parent

# Add the root directory to Python path so we can import our package
sys.path.append(str(ROOT_DIR))

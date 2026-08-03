import sys
from pathlib import Path

# Add root directory to python path for Vercel Serverless Function
ROOT_DIR = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(ROOT_DIR))

from app import app

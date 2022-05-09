import os
from pathlib import Path

BASE_DIR = Path(os.path.abspath(__file__)).parents[2]
ROOT_DIR = Path(os.path.abspath(__file__)).parents[4]
APPS_DIR = BASE_DIR / "app"
